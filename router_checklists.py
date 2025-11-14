# router_checklists.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
import parsing
from models import get_db
import json
from datetime import datetime

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.post("/parse", response_model=list[schemas.CardParsed])
def parse_checklist(req: schemas.ChecklistParseRequest):
    return parsing.parse_checklist_text(req.raw_text)


def get_or_create_product(db: Session, year: int, product_name: str) -> models.Product:
    product = (
        db.query(models.Product)
        .filter(models.Product.year == year, models.Product.name == product_name)
        .first()
    )
    if product:
        return product
    product = models.Product(year=year, name=product_name)
    db.add(product)
    db.flush()
    return product


def get_or_create_set_type(db: Session, name: str) -> models.SetType:
    st = db.query(models.SetType).filter(models.SetType.name == name).first()
    if st:
        return st
    st = models.SetType(name=name, is_custom=True)
    db.add(st)
    db.flush()
    return st


def _normalize_string_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [segment.strip() for segment in value.split(",") if segment.strip()]
    return []


def _materialize_cards_submission(submission: models.ChecklistSubmission, db: Session):
    cards = submission.parsed_data or []
    if not cards:
        return

    product = get_or_create_product(db, submission.year, submission.product_name)
    set_type = get_or_create_set_type(db, submission.set_type_name)
    display_name = submission.set_type_name or set_type.name

    checklist = None
    if submission.result_checklist_id:
        checklist = (
            db.query(models.ProductChecklist)
            .filter(models.ProductChecklist.id == submission.result_checklist_id)
            .first()
        )

    if not checklist:
        checklist = (
            db.query(models.ProductChecklist)
            .filter(
                models.ProductChecklist.product_id == product.id,
                models.ProductChecklist.display_name == display_name,
            )
            .first()
        )

    if not checklist:
        checklist = models.ProductChecklist(
            product=product,
            set_type=set_type,
            display_name=display_name,
            card_count_declared=submission.card_count_declared,
        )
        db.add(checklist)
        db.flush()
    else:
        checklist.set_type = set_type
        if submission.card_count_declared:
            checklist.card_count_declared = submission.card_count_declared
        db.query(models.ChecklistCard).filter(models.ChecklistCard.checklist_id == checklist.id).delete()

    card_models = []
    for entry in cards:
        card_number = str(entry.get("card_number") or "").strip()
        if not card_number:
            continue
        players = _normalize_string_list(entry.get("players") or entry.get("player"))
        teams = _normalize_string_list(entry.get("teams") or entry.get("team"))
        flags = entry.get("flags") or []
        if isinstance(flags, str):
            flags = [segment.strip() for segment in flags.split(",") if segment.strip()]
        descriptions = entry.get("descriptions") or entry.get("description") or []
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        raw_lines = entry.get("raw_lines") or []
        if isinstance(raw_lines, str):
            raw_lines = [raw_lines]

        player_display = ", ".join(players) if players else entry.get("player_name") or entry.get("player") or "Unknown Player"
        team_display = ", ".join(teams) if teams else entry.get("team")
        raw_value = "\n".join(raw_lines) if raw_lines else entry.get("raw_line") or card_number

        card_models.append(
            models.ChecklistCard(
                checklist=checklist,
                card_number=card_number,
                player_name=player_display,
                team=team_display,
                flags=flags,
                subset=entry.get("subset"),
                notes="; ".join([d for d in descriptions if d]) or None,
                raw_line=raw_value,
            )
        )

    if card_models:
        db.add_all(card_models)

    submission.result_checklist_id = checklist.id
    submission.materialized_at = datetime.utcnow()


def _materialize_parallels_submission(submission: models.ChecklistSubmission, db: Session):
    lines = submission.parsed_data or []
    if not lines:
        return
    product = get_or_create_product(db, submission.year, submission.product_name)
    db.query(models.Parallel).filter(models.Parallel.product_id == product.id).delete()
    for entry in lines:
        name = (entry.get("name") or entry.get("title") or "").strip()
        if not name:
            continue
        db.add(
            models.Parallel(
                product=product,
                name=name,
                print_run=entry.get("print_run"),
                exclusive=entry.get("exclusive"),
                notes=entry.get("notes") or entry.get("raw_line"),
                raw_line=entry.get("raw_line") or name,
            )
        )


def materialize_submission(submission: models.ChecklistSubmission, db: Session):
    if submission.submission_type == "parallels":
        _materialize_parallels_submission(submission, db)
    else:
        _materialize_cards_submission(submission, db)


def sync_approved_submissions(db: Session):
    pending = (
        db.query(models.ChecklistSubmission)
        .filter(models.ChecklistSubmission.status == "approved")
        .filter(models.ChecklistSubmission.materialized_at.is_(None))
        .all()
    )
    synced = 0
    for submission in pending:
        materialize_submission(submission, db)
        synced += 1
    if synced:
        db.commit()
    return synced


@router.post("", response_model=schemas.ChecklistCreateResponse)
def create_checklist(req: schemas.ChecklistCreateRequest, db: Session = Depends(get_db)):
    product = get_or_create_product(db, req.year, req.product_name)
    set_type = get_or_create_set_type(db, req.set_type_name)

    checklist = models.ProductChecklist(
        product=product,
        set_type=set_type,
        display_name=req.checklist_display_name,
        card_count_declared=req.card_count_declared,
    )
    db.add(checklist)
    db.flush()

    card_models = []
    for c in req.cards:
        player_display = ", ".join(c.players) if c.players else None
        team_display = ", ".join([t for t in c.teams if t]) if c.teams else None
        notes_display = "; ".join([d for d in c.descriptions if d]) if c.descriptions else None
        raw_line = "\n".join(c.raw_lines) if c.raw_lines else ""

        card_models.append(
            models.ChecklistCard(
                checklist=checklist,
                card_number=c.card_number,
                player_name=player_display,
                team=team_display,
                flags=c.flags,
                subset=None,
                notes=notes_display,
                raw_line=raw_line,
            )
        )
    db.add_all(card_models)
    db.commit()

    return schemas.ChecklistCreateResponse(
        product_id=product.id,
        checklist_id=checklist.id,
        cards_inserted=len(card_models),
    )


@router.post("/check-product", response_model=schemas.ProductCheckResponse)
def check_product(req: schemas.ProductCheckRequest, db: Session = Depends(get_db)):
    """Check if a product exists and return existing set types"""
    product = (
        db.query(models.Product)
        .filter(models.Product.year == req.year, models.Product.name == req.product_name)
        .first()
    )

    if not product:
        return schemas.ProductCheckResponse(
            exists=False,
            product_id=None,
            existing_types=[]
        )

    # Get existing set types for this product
    existing_types = (
        db.query(models.SetType.name)
        .join(models.ProductChecklist)
        .filter(models.ProductChecklist.product_id == product.id)
        .distinct()
        .all()
    )

    type_names = [t[0] for t in existing_types]

    return schemas.ProductCheckResponse(
        exists=True,
        product_id=product.id,
        existing_types=type_names
    )


@router.get("/set-types", response_model=schemas.SetTypeListResponse)
def get_set_types(db: Session = Depends(get_db)):
    """Get all set types that have been used"""
    set_types = db.query(models.SetType.name).order_by(models.SetType.name).all()
    type_names = [t[0] for t in set_types]
    return schemas.SetTypeListResponse(set_types=type_names)


@router.post("/submit", response_model=schemas.ChecklistSubmissionResponse)
def submit_checklist(req: schemas.ChecklistSubmissionRequest, db: Session = Depends(get_db)):
    """Submit a checklist for admin review"""

    # Create submission record
    submission = models.ChecklistSubmission(
        year=req.year,
        product_name=req.product_name,
        set_type_name=req.set_type_name,
        submission_type=req.submission_type,
        card_count_declared=req.card_count_declared,
        raw_text=req.raw_text,
        parsed_data=req.parsed_data,
        status='pending'
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return schemas.ChecklistSubmissionResponse(
        submission_id=submission.id,
        status='pending',
        message=f'Checklist submission received! Submission ID: {submission.id}. An admin will review it shortly.'
    )


@router.get("/submissions", response_model=list[schemas.ChecklistSubmissionAdmin])
def list_submissions(status: str | None = Query(default=None), db: Session = Depends(get_db)):
    """List checklist submissions for admin review"""
    query = db.query(models.ChecklistSubmission).order_by(models.ChecklistSubmission.submitted_at.desc())
    if status:
        query = query.filter(models.ChecklistSubmission.status == status)
    return query.all()


@router.patch("/submissions/{submission_id}/status", response_model=schemas.ChecklistSubmissionResponse)
def update_submission_status(
    submission_id: int,
    payload: schemas.ChecklistSubmissionStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update the status of a checklist submission"""
    valid_statuses = {"pending", "approved", "rejected"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    submission = db.query(models.ChecklistSubmission).filter(models.ChecklistSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    previous_status = submission.status
    submission.status = payload.status
    if payload.admin_notes is not None:
        submission.admin_notes = payload.admin_notes
    submission.reviewed_at = datetime.utcnow()
    if payload.status == "approved" and previous_status != "approved":
        materialize_submission(submission, db)
    db.commit()
    db.refresh(submission)

    return schemas.ChecklistSubmissionResponse(
        submission_id=submission.id,
        status=submission.status,
        message=f"Submission #{submission.id} updated to '{submission.status}'"
    )


@router.get("/library/summary")
def get_checklist_library_summary(db: Session = Depends(get_db)):
    sync_approved_submissions(db)
    rows = (
        db.query(
            models.ProductChecklist.id.label("id"),
            models.Product.id.label("product_id"),
            models.Product.year.label("year"),
            models.Product.name.label("product_name"),
            models.SetType.name.label("set_type_name"),
            models.ProductChecklist.display_name.label("display_name"),
            models.ProductChecklist.card_count_declared.label("card_count_declared"),
            func.count(models.ChecklistCard.id).label("card_count"),
            func.max(models.ChecklistCard.created_at).label("last_card_added_at"),
        )
        .join(models.Product, models.ProductChecklist.product_id == models.Product.id)
        .join(models.SetType, models.ProductChecklist.set_type_id == models.SetType.id)
        .outerjoin(models.ChecklistCard, models.ChecklistCard.checklist_id == models.ProductChecklist.id)
        .group_by(
            models.ProductChecklist.id,
            models.Product.id,
            models.Product.year,
            models.Product.name,
            models.SetType.name,
            models.ProductChecklist.display_name,
            models.ProductChecklist.card_count_declared,
        )
        .order_by(
            models.Product.year.desc(),
            models.Product.name.asc(),
            models.ProductChecklist.display_name.asc(),
        )
        .all()
    )

    # Group by product and fetch parallels for each product
    products_dict = {}
    for row in rows:
        product_key = (row.year, row.product_name)
        if product_key not in products_dict:
            # Fetch parallels for this product
            parallels = (
                db.query(models.Parallel)
                .filter(models.Parallel.product_id == row.product_id)
                .order_by(models.Parallel.name.asc())
                .all()
            )
            products_dict[product_key] = {
                "year": row.year,
                "product_id": row.product_id,
                "product_name": row.product_name,
                "checklists": [],
                "parallels": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "print_run": p.print_run,
                        "exclusive": p.exclusive,
                        "notes": p.notes,
                    }
                    for p in parallels
                ],
            }

        products_dict[product_key]["checklists"].append({
            "id": row.id,
            "year": row.year,
            "product_name": row.product_name,
            "set_type": row.set_type_name,
            "display_name": row.display_name,
            "card_count": row.card_count,
            "card_count_declared": row.card_count_declared,
            "last_card_added_at": row.last_card_added_at,
        })

    return list(products_dict.values())


@router.get("/library/{checklist_id}")
def get_checklist_detail(checklist_id: int, db: Session = Depends(get_db)):
    checklist = (
        db.query(models.ProductChecklist)
        .filter(models.ProductChecklist.id == checklist_id)
        .first()
    )
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    cards = (
        db.query(models.ChecklistCard)
        .filter(models.ChecklistCard.checklist_id == checklist.id)
        .order_by(models.ChecklistCard.card_number.asc())
        .all()
    )

    return {
        "id": checklist.id,
        "year": checklist.product.year if checklist.product else None,
        "product_name": checklist.product.name if checklist.product else None,
        "set_type": checklist.set_type.name if checklist.set_type else None,
        "display_name": checklist.display_name,
        "card_count": len(cards),
        "card_count_declared": checklist.card_count_declared,
        "cards": [
            {
                "id": card.id,
                "card_number": card.card_number,
                "player_name": card.player_name,
                "team": card.team,
                "flags": card.flags or [],
                "subset": card.subset,
                "notes": card.notes,
                "raw_line": card.raw_line,
            }
            for card in cards
        ],
    }


@router.patch("/library/{checklist_id}", response_model=schemas.ChecklistUpdateResponse)
def update_checklist(
    checklist_id: int,
    payload: schemas.ChecklistUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update checklist metadata (product name, set type, display name)"""
    checklist = (
        db.query(models.ProductChecklist)
        .filter(models.ProductChecklist.id == checklist_id)
        .first()
    )
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Update product if year or product_name changed
    if payload.year is not None or payload.product_name is not None:
        new_year = payload.year if payload.year is not None else checklist.product.year
        new_name = payload.product_name if payload.product_name is not None else checklist.product.name

        # Check if product with new values already exists
        existing_product = (
            db.query(models.Product)
            .filter(models.Product.year == new_year, models.Product.name == new_name)
            .first()
        )

        if existing_product and existing_product.id != checklist.product.id:
            # Use existing product
            checklist.product_id = existing_product.id
        else:
            # Update current product
            checklist.product.year = new_year
            checklist.product.name = new_name

    # Update set type if changed
    if payload.set_type_name is not None:
        set_type = get_or_create_set_type(db, payload.set_type_name)
        checklist.set_type_id = set_type.id

    # Update display name if changed
    if payload.display_name is not None:
        checklist.display_name = payload.display_name

    db.commit()
    db.refresh(checklist)

    return schemas.ChecklistUpdateResponse(
        checklist_id=checklist.id,
        message=f"Checklist updated successfully"
    )


@router.delete("/library/{checklist_id}")
def delete_checklist(checklist_id: int, db: Session = Depends(get_db)):
    checklist = (
        db.query(models.ProductChecklist)
        .filter(models.ProductChecklist.id == checklist_id)
        .first()
    )
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    db.query(models.ChecklistCard).filter(
        models.ChecklistCard.checklist_id == checklist.id
    ).delete()
    db.delete(checklist)
    db.commit()

    return {"message": f"Checklist '{checklist.display_name}' deleted"}
