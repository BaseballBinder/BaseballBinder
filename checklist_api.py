# -*- coding: utf-8 -*-
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
import logging
import csv
import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import get_db
from checklist_models import Checklist, ChecklistRequest, Suggestion

app = FastAPI()

router = APIRouter(prefix="/checklist", tags=["checklist"])

logger = logging.getLogger(__name__)

# Pydantic Models
class ChecklistSummary(BaseModel):
    set_name: str
    year: str
    card_count: int
    last_updated: Optional[str] = None

class ChecklistRequestCreate(BaseModel):
    set_name: str
    year: str
    manufacturer: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = "normal"

class ChecklistRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    set_name: str
    year: str
    manufacturer: Optional[str]
    email: Optional[str]
    notes: Optional[str]
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

class ChecklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    set_name: str
    year: str
    card_number: str
    player: str
    team: Optional[str] = None
    variety: Optional[str] = None
    rookie: bool
    parallel: Optional[str] = None

def normalize_set_name(value: str) -> str:
    """
    Normalize a set name so file stems and UI strings can be matched reliably.
    """
    return value.replace("-", " ").replace("_", " ").strip()


def find_checklist_csv(year: str, set_name: str) -> Optional[Path]:
    """
    Attempt to locate the CSV file on disk that represents a given set.
    """
    year_folder = Path("checklists") / year
    if not year_folder.exists():
        return None

    target = normalize_set_name(set_name).lower()
    for csv_file in year_folder.glob("*.csv"):
        normalized = normalize_set_name(csv_file.stem).lower()
        if normalized == target:
            return csv_file
    return None


# Helper function to scan and import CSVs from checklists folder
def scan_and_import_checklists(db: Session, force: bool = False):
    """
    Scans /checklists/{year}/ folders and imports CSV files.
    If force=True, all existing checklists are cleared before import.
    If a set already exists for a given year, it is replaced.
    Also removes checklists from database if their CSV files no longer exist.
    """
    base_path = Path("checklists")
    imported_count = 0
    errors = []
    logger.info(f"Scanning folder for changes: {base_path.resolve()}")

    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        return {"imported": 0, "errors": ["Checklists folder created. Add CSV files to import."]}

    if force:
        db.query(Checklist).delete()
        db.commit()
        logger.info("Cleared all checklists before reimport (force=True)")

    # Track all CSV files found during scan (set_name, year)
    found_checklists = set()

    for year_folder in base_path.iterdir():
        if not year_folder.is_dir():
            continue

        year = year_folder.name

        for csv_file in year_folder.glob("*.csv"):
            try:
                set_name = normalize_set_name(csv_file.stem)

                # Track this checklist as found
                found_checklists.add((set_name, year))

                # 🧽 Remove existing records for this set/year before reimporting
                existing = db.query(Checklist).filter(
                    Checklist.set_name == set_name,
                    Checklist.year == year
                ).count()

                if existing > 0:
                    db.query(Checklist).filter(
                        Checklist.set_name == set_name,
                        Checklist.year == year
                    ).delete()
                    db.commit()
                    logger.info(f"Replacing existing checklist: {year} - {set_name}")

                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    csv_reader = csv.reader(f, quotechar='"', skipinitialspace=True)
                    next(csv_reader, None)  # skip header
                    cards_added = 0

                    for row in csv_reader:
                        if len(row) < 3:
                            continue

                        checklist_entry = Checklist(
                            set_name=set_name,
                            year=year,
                            card_number=row[1].strip(),
                            player=row[2].strip(),
                            team=row[3].strip() if len(row) > 3 else "",
                            variety=row[0].strip(),
                            rookie=(len(row) > 4 and row[4].strip().lower() in ['yes', 'true', '1', 'rookie', 'rc']),
                            parallel=row[5].strip() if len(row) > 5 else "",
                        )
                        db.add(checklist_entry)
                        cards_added += 1

                    if cards_added > 0:
                        db.commit()
                        imported_count += 1

            except Exception as e:
                errors.append(f"{csv_file.name}: {str(e)}")
                db.rollback()

    # 🗑️ Remove checklists from database that no longer have CSV files
    all_db_checklists = db.query(
        Checklist.set_name,
        Checklist.year
    ).distinct().all()

    removed_count = 0
    for db_set_name, db_year in all_db_checklists:
        if (db_set_name, db_year) not in found_checklists:
            deleted = db.query(Checklist).filter(
                Checklist.set_name == db_set_name,
                Checklist.year == db_year
            ).delete()
            if deleted > 0:
                removed_count += 1
                logger.info(f"Removed checklist (file no longer exists): {db_year} - {db_set_name}")

    if removed_count > 0:
        db.commit()
        logger.info(f"Removed {removed_count} checklist(s) that no longer have CSV files")

    return {"imported": imported_count, "removed": removed_count, "errors": errors}


@router.get("/summary", response_model=List[ChecklistSummary])
def get_checklist_summary(db: Session = Depends(get_db)):
    """
    Get summary of all imported checklists (set name, year, card count)
    """
    results = db.query(
        Checklist.set_name,
        Checklist.year,
        func.count(Checklist.id).label('card_count')
    ).group_by(
        Checklist.set_name,
        Checklist.year
    ).order_by(
        Checklist.year.desc(),
        Checklist.set_name
    ).all()

    return [
        ChecklistSummary(
            set_name=row.set_name,
            year=row.year,
            card_count=row.card_count,
            last_updated=None
        )
        for row in results
    ]


@router.get("/years")
def list_checklist_years(db: Session = Depends(get_db)):
    """
    Return the distinct years that currently have imported checklists.
    """
    year_rows = (
        db.query(Checklist.year)
        .distinct()
        .order_by(Checklist.year.desc())
        .all()
    )
    return {"years": [row[0] for row in year_rows]}


@router.post("/rescan")
def rescan_checklists(
    force: bool = Query(False, description="If true, clears existing checklists before rescanning"),
    db: Session = Depends(get_db)
):
    """
    Rescan the /checklists folder and import new CSV files.
    Use ?force=true to clear the database before rescanning.
    Also removes checklists from database if their CSV files no longer exist.
    """
    if force:
        db.query(Checklist).delete()
        db.commit()
        logger.info("Existing checklists cleared before rescan.")

    result = scan_and_import_checklists(db)

    # Build message with import and removal info
    messages = []
    if result['imported'] > 0:
        messages.append(f"Imported {result['imported']} checklist(s)")
    if result.get('removed', 0) > 0:
        messages.append(f"Removed {result['removed']} checklist(s)")
    if not messages:
        messages.append("No changes detected")

    message = "Scan complete. " + ", ".join(messages) + "."

    return {
        "message": message,
        "imported": result['imported'],
        "removed": result.get('removed', 0),
        "errors": result['errors']
    }

@router.get("/sets/{year}")
def get_sets_by_year(year: str, db: Session = Depends(get_db)):
    """Get all unique set names for a given year"""
    sets = db.query(Checklist.set_name).filter(
        Checklist.year == year
    ).distinct().order_by(Checklist.set_name).all()

    return {"year": year, "sets": [s[0] for s in sets]}

@router.get("/{year}/{set_name}", response_model=List[ChecklistItem])
def get_checklist(year: str, set_name: str, db: Session = Depends(get_db)):
    """Get full checklist for a specific set and year"""
    checklists = db.query(Checklist).filter(
        Checklist.year == year,
        Checklist.set_name == set_name
    ).order_by(Checklist.card_number).all()

    if not checklists:
        raise HTTPException(status_code=404, detail="Checklist not found")

    return checklists


@router.delete("/{year}/{set_name}")
def delete_checklist(year: str, set_name: str, db: Session = Depends(get_db)):
    """
    Delete a checklist's records from the database and remove its CSV file if present.
    """
    normalized = normalize_set_name(set_name).lower()

    cards_query = db.query(Checklist).filter(
        Checklist.year == year,
        func.lower(Checklist.set_name) == normalized
    )

    cards_removed = cards_query.count()
    if cards_removed:
        cards_query.delete(synchronize_session=False)
        db.commit()

    csv_file = find_checklist_csv(year, set_name)
    file_removed = False
    removed_filename = None
    if csv_file and csv_file.exists():
        csv_file.unlink()
        file_removed = True
        removed_filename = csv_file.name

    if cards_removed == 0 and not file_removed:
        raise HTTPException(status_code=404, detail="Checklist not found")

    return {
        "message": f"Removed checklist '{set_name}' for {year}.",
        "cards_removed": cards_removed,
        "file_removed": file_removed,
        "removed_filename": removed_filename,
    }

# ==============================
# EMAIL NOTIFICATION HELPER
# ==============================

def send_checklist_request_email(request_data: ChecklistRequest):
    """
    Send email notification when a new checklist is requested

    To enable email notifications:
    1. Set environment variables:
       - EMAIL_HOST (e.g., smtp.gmail.com)
       - EMAIL_PORT (e.g., 587)
       - EMAIL_USER (your email address)
       - EMAIL_PASSWORD (your app password)
    2. For Gmail: Enable 2FA and create an App Password
    """
    # Check if email is configured
    email_host = os.getenv('EMAIL_HOST')
    email_port = os.getenv('EMAIL_PORT', '587')
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')

    if not all([email_host, email_user, email_password]):
        print("⚠️ Email not configured. Skipping email notification.")
        print("💡 Set EMAIL_HOST, EMAIL_USER, and EMAIL_PASSWORD environment variables to enable emails.")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'New Checklist Request: {request_data.year} {request_data.set_name}'
        msg['From'] = email_user
        msg['To'] = 'baseballbinder@gmail.com'

        # HTML body
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">⚾ New Checklist Request</h1>
                </div>

                <div style="padding: 30px; background: #f9fafb; border: 1px solid #e5e7eb;">
                    <h2 style="color: #1e3a8a; margin-top: 0;">Request Details</h2>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold; width: 150px;">Set Name:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">{request_data.set_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">Year:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">{request_data.year}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">Manufacturer:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">{request_data.manufacturer or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">Priority:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">
                                <span style="padding: 4px 12px; background: {'#dc2626' if request_data.priority == 'high' else '#3b82f6' if request_data.priority == 'normal' else '#6b7280'}; color: white; border-radius: 4px; font-size: 0.9em;">
                                    {request_data.priority.upper()}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">User Email:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">{request_data.email or 'Not provided'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">Request ID:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">#{request_data.id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb; font-weight: bold;">Submitted:</td>
                            <td style="padding: 10px; background: white; border: 1px solid #e5e7eb;">{request_data.created_at.strftime('%B %d, %Y at %I:%M %p')}</td>
                        </tr>
                    </table>

                    {f'<div style="margin-top: 20px; padding: 15px; background: white; border-left: 4px solid #3b82f6; border-radius: 4px;"><strong>Notes:</strong><br>{request_data.notes}</div>' if request_data.notes else ''}
                </div>

                <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 0.9em;">
                    <p>This is an automated notification from BaseballBinder</p>
                </div>
            </body>
        </html>
        """

        # Plain text fallback
        text = f"""
New Checklist Request

Set Name: {request_data.set_name}
Year: {request_data.year}
Manufacturer: {request_data.manufacturer or 'Not specified'}
Priority: {request_data.priority.upper()}
User Email: {request_data.email or 'Not provided'}
Request ID: #{request_data.id}
Submitted: {request_data.created_at.strftime('%B %d, %Y at %I:%M %p')}

{f'Notes: {request_data.notes}' if request_data.notes else ''}

---
This is an automated notification from BaseballBinder
        """

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Send email
        with smtplib.SMTP(email_host, int(email_port)) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)

        print(f"✅ Email sent successfully for request #{request_data.id}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

# ==============================
# CHECKLIST REQUESTS ENDPOINTS
# ==============================

@router.post("/request", response_model=ChecklistRequestResponse)
def create_checklist_request(
    request: ChecklistRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a request for a missing checklist
    Sends email notification to baseballbinder@gmail.com if configured
    """
    db_request = ChecklistRequest(
        set_name=request.set_name,
        year=request.year,
        manufacturer=request.manufacturer,
        email=request.email,
        notes=request.notes,
        priority=request.priority or "normal",
        status="pending"
    )

    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    # Send email notification
    send_checklist_request_email(db_request)

    return db_request

@router.get("/requests", response_model=List[ChecklistRequestResponse])
def get_checklist_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all checklist requests (for admin use)
    Filter by status: pending, processing, completed, rejected
    """
    query = db.query(ChecklistRequest)

    if status:
        query = query.filter(ChecklistRequest.status == status)

    requests = query.order_by(ChecklistRequest.created_at.desc()).all()

    return requests

@router.patch("/requests/{request_id}/status")
def update_checklist_request_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update the status of a checklist request
    Valid statuses: pending, processing, completed, rejected
    """
    valid_statuses = ['pending', 'processing', 'completed', 'rejected']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    request = db.query(ChecklistRequest).filter(ChecklistRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = status
    request.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request)

    return {"message": f"Request #{request_id} status updated to '{status}'", "request": request}

@router.delete("/requests/{request_id}")
def delete_checklist_request(request_id: int, db: Session = Depends(get_db)):
    """
    Delete a checklist request
    """
    request = db.query(ChecklistRequest).filter(ChecklistRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(request)
    db.commit()

    return {"message": "Request deleted successfully"}

# ==============================
# SUGGESTIONS ENDPOINTS
# ==============================

class SuggestionCreate(BaseModel):
    category: str
    title: str
    description: str
    email: Optional[str] = None

class SuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    description: str
    email: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

@router.post("/suggestions", response_model=SuggestionResponse)
def create_suggestion(
    suggestion: SuggestionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a suggestion or feedback
    """
    db_suggestion = Suggestion(
        category=suggestion.category,
        title=suggestion.title,
        description=suggestion.description,
        email=suggestion.email,
        status="new"
    )

    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)

    return db_suggestion

@router.get("/suggestions", response_model=List[SuggestionResponse])
def get_suggestions(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all suggestions (for admin use)
    Filter by status: new, reviewing, planned, completed, rejected
    """
    query = db.query(Suggestion)

    if status:
        query = query.filter(Suggestion.status == status)

    suggestions = query.order_by(Suggestion.created_at.desc()).all()

    return suggestions

@router.patch("/suggestions/{suggestion_id}/status")
def update_suggestion_status(
    suggestion_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update the status of a suggestion
    Valid statuses: new, reviewing, planned, completed, rejected
    """
    valid_statuses = ['new', 'reviewing', 'planned', 'completed', 'rejected']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = status
    suggestion.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(suggestion)

    return {"message": f"Suggestion #{suggestion_id} status updated to '{status}'", "suggestion": suggestion}

@router.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    """
    Delete a suggestion
    """
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    db.delete(suggestion)
    db.commit()

    return {"message": "Suggestion deleted successfully"}
