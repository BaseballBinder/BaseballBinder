from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io

from models import get_db
from checklist_models import Checklist

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.post("/upload")
async def upload_checklists(
    year: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple CSV files for a given year.
    CSV format: Variety, Card Number, Player/Athlete, Team, Rookie, Parallel, Unique Variety
    """
    uploaded_count = 0
    errors = []

    for file in files:
        try:
            # Get set name from filename (remove .csv extension)
            set_name = file.filename.replace('.csv', '').replace('-', ' ').strip()

            # Read CSV content
            content = await file.read()
            
            # Try different encodings
            try:
                decoded = content.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    decoded = content.decode('latin-1')
                except UnicodeDecodeError:
                    decoded = content.decode('cp1252')
            
            # Parse CSV with proper handling of quoted fields
            csv_reader = csv.reader(
                io.StringIO(decoded), 
                quotechar='"', 
                skipinitialspace=True,
                quoting=csv.QUOTE_MINIMAL
            )
            
            # SKIP THE FIRST ROW (headers)
            next(csv_reader, None)

            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):
                # Skip empty rows
                if not row or len(row) < 3:
                    continue
                
                # Direct column mapping (0-indexed)
                # Column A (0): Variety
                # Column B (1): Card Number
                # Column C (2): Player/Athlete (may have quotes and trailing comma)
                # Column D (3): Team
                # Column E (4): Rookie
                # Column F (5): Parallel
                # Column G (6): Unique Variety (IGNORE THIS)
                
                variety = row[0].strip() if len(row) > 0 and row[0].strip() else None
                card_number = row[1].strip() if len(row) > 1 and row[1].strip() else None
                
                # Clean player name - remove trailing comma if present
                player_raw = row[2].strip() if len(row) > 2 else ""
                player = player_raw.replace(',', '').strip() if player_raw else None
                
                team = row[3].strip() if len(row) > 3 and row[3].strip() else None
                rookie_str = row[4].strip().upper() if len(row) > 4 and row[4].strip() else ""
                parallel = row[5].strip() if len(row) > 5 and row[5].strip() else None
                # Column 6 (Unique Variety) is ignored

                # Skip if missing required fields
                if not card_number or not player or not variety:
                    continue

                # Convert rookie to boolean
                rookie = rookie_str in ['YES', 'Y', 'TRUE', 'RC', 'ROOKIE']

                # Check if entry already exists
                existing = db.query(Checklist).filter(
                    Checklist.set_name == set_name,
                    Checklist.year == year,
                    Checklist.card_number == card_number,
                    Checklist.variety == variety,
                    Checklist.parallel == (parallel if parallel else None)
                ).first()

                if not existing:
                    checklist_entry = Checklist(
                        set_name=set_name,
                        year=year,
                        card_number=card_number,
                        player=player,
                        team=team,
                        variety=variety,
                        rookie=rookie,
                        parallel=parallel
                    )
                    db.add(checklist_entry)
                    uploaded_count += 1

            db.commit()

        except Exception as e:
            errors.append(f"Error processing {file.filename}: {str(e)}")

    return {
        "uploaded": uploaded_count,
        "files_processed": len(files),
        "errors": errors
    }

@router.get("/years")
def get_years(db: Session = Depends(get_db)):
    """Get all unique years in the checklist database."""
    years = db.query(Checklist.year).distinct().order_by(Checklist.year.desc()).all()
    return [year[0] for year in years if year[0]]

@router.get("/imported-sets")
def get_imported_sets(db: Session = Depends(get_db)):
    """Get all imported sets grouped by year with card counts."""
    from sqlalchemy import func

    results = db.query(
        Checklist.year,
        Checklist.set_name,
        func.count(Checklist.id).label('card_count')
    ).group_by(
        Checklist.year,
        Checklist.set_name
    ).order_by(
        Checklist.year.desc(),
        Checklist.set_name
    ).all()

    # Group by year
    grouped = {}
    for year, set_name, count in results:
        if year not in grouped:
            grouped[year] = []
        grouped[year].append({
            "set_name": set_name,
            "card_count": count
        })

    return grouped

@router.get("/all-sets")
def get_all_sets(db: Session = Depends(get_db)):
    """Get all unique set names across all years."""
    sets = db.query(Checklist.set_name, Checklist.year).distinct().order_by(
        Checklist.year.desc(),
        Checklist.set_name
    ).all()
    return [{"set_name": s[0], "year": s[1]} for s in sets if s[0]]

@router.get("/sets/{year}")
def get_sets_by_year(year: str, db: Session = Depends(get_db)):
    """Get all unique set names for a given year."""
    sets = db.query(Checklist.set_name).filter(
        Checklist.year == year
    ).distinct().order_by(Checklist.set_name).all()
    return [set_name[0] for set_name in sets if set_name[0]]

@router.get("/lookup")
def lookup_card(
    set_name: str,
    year: str,
    card_number: str,
    db: Session = Depends(get_db)
):
    """
    Look up card details from checklist.
    Returns all matching entries (different varieties/parallels).
    """
    cards = db.query(Checklist).filter(
        Checklist.set_name == set_name,
        Checklist.year == year,
        Checklist.card_number == card_number
    ).all()

    if not cards:
        raise HTTPException(status_code=404, detail="Card not found in checklist")

    return [{
        "id": card.id,
        "set_name": card.set_name,
        "year": card.year,
        "card_number": card.card_number,
        "player": card.player,
        "team": card.team,
        "variety": card.variety,
        "rookie": card.rookie,
        "parallel": card.parallel
    } for card in cards]

@router.get("/varieties/{set_name}/{year}")
def get_varieties(set_name: str, year: str, db: Session = Depends(get_db)):
    """Get all unique varieties for a specific set and year."""
    varieties = db.query(Checklist.variety).distinct().filter(
        Checklist.set_name == set_name,
        Checklist.year == year,
        Checklist.variety.isnot(None),
        Checklist.variety != ""
    ).all()
    return [variety[0] for variety in varieties if variety[0]]

@router.get("/search")
def search_checklist(
    query: str,
    year: Optional[str] = None,
    set_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search checklist by player name, card number, or team."""
    q = db.query(Checklist)

    if year:
        q = q.filter(Checklist.year == year)
    if set_name:
        q = q.filter(Checklist.set_name == set_name)

    # Search in player, card_number, or team
    search_filter = (
        Checklist.player.contains(query) |
        Checklist.card_number.contains(query) |
        Checklist.team.contains(query)
    )
    q = q.filter(search_filter)

    results = q.limit(50).all()

    return [{
        "id": card.id,
        "set_name": card.set_name,
        "year": card.year,
        "card_number": card.card_number,
        "player": card.player,
        "team": card.team,
        "variety": card.variety,
        "rookie": card.rookie,
        "parallel": card.parallel
    } for card in results]

@router.delete("/clear/{year}")
def clear_year(year: str, db: Session = Depends(get_db)):
    """Delete all checklist entries for a specific year."""
    deleted = db.query(Checklist).filter(Checklist.year == year).delete()
    db.commit()
    return {"deleted": deleted}