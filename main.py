from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from sqlalchemy import func

from models import Card, get_db
from checklist_api import router as checklist_router

app = FastAPI(title="Card Collection API")

# Include checklist routes
app.include_router(checklist_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CardCreate(BaseModel):
    set_name: Optional[str] = None
    card_number: Optional[str] = None
    player: Optional[str] = None
    team: Optional[str] = None
    year: Optional[str] = None
    variety: Optional[str] = None
    parallel: Optional[str] = None
    autograph: bool = False
    numbered: Optional[str] = None
    graded: Optional[str] = None
    price_paid: Optional[float] = None
    current_value: Optional[float] = None
    sold_price: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    quantity: int = 1

class CardUpdate(BaseModel):
    set_name: Optional[str] = None
    card_number: Optional[str] = None
    player: Optional[str] = None
    team: Optional[str] = None
    year: Optional[str] = None
    variety: Optional[str] = None
    parallel: Optional[str] = None
    autograph: Optional[bool] = None
    numbered: Optional[str] = None
    graded: Optional[str] = None
    price_paid: Optional[float] = None
    current_value: Optional[float] = None
    sold_price: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    quantity: Optional[int] = None

class CardResponse(CardCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    tracked_for_pricing: bool = False
    last_price_check: Optional[datetime] = None
    ebay_avg_price: Optional[float] = None

# Price Tracking Models
class UpdateTrackingRequest(BaseModel):
    card_ids: List[int]

class BulkUpdateValue(BaseModel):
    card_id: int
    ebay_avg_price: float
    current_value: float

class BulkUpdateValuesRequest(BaseModel):
    updates: List[BulkUpdateValue]

class EbayPriceCheckRequest(BaseModel):
    card_id: int
    player: str
    set_name: str
    year: Optional[str] = None
    card_number: str
    variety: Optional[str] = None
    parallel: Optional[str] = None

class EbayPriceCheckResponse(BaseModel):
    avg_sold_price: Optional[float] = None
    price_range: Optional[str] = None
    last_checked: str
    ebay_url: str

@app.get("/")
def root():
    return {"message": "Card Collection API", "version": "1.0"}

@app.post("/cards/", response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    db_card = Card(**card.dict())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@app.get("/cards/", response_model=List[CardResponse])
def get_cards(
    skip: int = 0,
    limit: int = 100,
    set_name: Optional[str] = None,
    player: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Card)
    
    if set_name:
        query = query.filter(Card.set_name.contains(set_name))
    if player:
        query = query.filter(Card.player.contains(player))
    
    cards = query.offset(skip).limit(limit).all()
    return cards

@app.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card

@app.put("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    update_data = card_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    return card

@app.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    return {"message": "Card deleted successfully"}

@app.delete("/cards/")
def delete_all_cards(db: Session = Depends(get_db)):
    """Delete all cards from the collection"""
    try:
        count = db.query(Card).count()
        db.query(Card).delete()
        db.commit()
        return {"message": f"Successfully deleted {count} card(s)", "deleted_count": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/")
def get_collection_stats(db: Session = Depends(get_db)):
    """Get collection statistics"""
    total_cards = db.query(Card).count()
    total_value = db.query(func.sum(Card.current_value)).scalar() or 0
    total_invested = db.query(func.sum(Card.price_paid)).scalar() or 0

    return {
        "total_cards": total_cards,
        "total_value": total_value,
        "total_invested": total_invested,
        "profit_loss": total_value - total_invested
    }

# ==============================
# PRICE TRACKING ENDPOINTS
# ==============================

@app.get("/cards/tracked/", response_model=List[CardResponse])
def get_tracked_cards(db: Session = Depends(get_db)):
    """Get all cards marked for price tracking"""
    cards = db.query(Card).filter(Card.tracked_for_pricing == True).all()
    return cards

@app.post("/cards/update-tracking")
def update_tracking(request: UpdateTrackingRequest, db: Session = Depends(get_db)):
    """Update which cards are being tracked for pricing"""
    try:
        # First, untrack all cards
        db.query(Card).update({Card.tracked_for_pricing: False})

        # Then, track the selected cards
        if request.card_ids:
            db.query(Card).filter(Card.id.in_(request.card_ids)).update(
                {Card.tracked_for_pricing: True},
                synchronize_session=False
            )

        db.commit()

        return {
            "message": f"Successfully updated tracking for {len(request.card_ids)} card(s)",
            "tracked_count": len(request.card_ids)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cards/bulk-update-values")
def bulk_update_values(request: BulkUpdateValuesRequest, db: Session = Depends(get_db)):
    """Bulk update card values from eBay price checks"""
    try:
        updated_count = 0

        for update in request.updates:
            card = db.query(Card).filter(Card.id == update.card_id).first()
            if card:
                card.ebay_avg_price = update.ebay_avg_price
                card.current_value = update.current_value
                card.last_price_check = datetime.utcnow()
                updated_count += 1

        db.commit()

        return {
            "message": f"Successfully updated {updated_count} card(s)",
            "updated_count": updated_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ebay/check-price", response_model=EbayPriceCheckResponse)
def check_ebay_price(request: EbayPriceCheckRequest, db: Session = Depends(get_db)):
    """
    Check eBay price for a card (placeholder implementation)

    TODO: Implement actual eBay API integration using Finding API or Browse API
    See EBAY_API_PLAN.md for implementation details
    """
    # Build eBay search URL for sold/completed listings
    search_query = f"{request.year or ''} {request.set_name} {request.player} {request.card_number} {request.variety or ''} {request.parallel or ''}".strip()
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"

    # TODO: Replace this with actual eBay API calls
    # For now, return placeholder data
    # When eBay API is configured, this will:
    # 1. Call eBay Finding API (findCompletedItems) or Browse API
    # 2. Parse sold listings from last 90 days
    # 3. Calculate average sold price
    # 4. Determine price range (min-max)
    # 5. Update card's last_price_check timestamp

    return EbayPriceCheckResponse(
        avg_sold_price=None,  # Will be populated by eBay API
        price_range="API not configured",  # e.g., "$20.00 - $35.00"
        last_checked=datetime.utcnow().isoformat(),
        ebay_url=ebay_url
    )

# ==============================
# BULK CARD IMPORT ENDPOINT
# ==============================

class BulkCardImport(BaseModel):
    cards: List[CardCreate]

class BulkImportResponse(BaseModel):
    success: int
    failed: int
    errors: List[str]

@app.post("/cards/bulk-import", response_model=BulkImportResponse)
def bulk_import_cards(import_data: BulkCardImport, db: Session = Depends(get_db)):
    """
    Bulk import cards from CSV data
    """
    success_count = 0
    failed_count = 0
    errors = []

    for idx, card_data in enumerate(import_data.cards):
        try:
            db_card = Card(**card_data.model_dump())
            db.add(db_card)
            db.commit()
            db.refresh(db_card)
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"Row {idx + 1}: {str(e)}")
            db.rollback()

    return BulkImportResponse(
        success=success_count,
        failed=failed_count,
        errors=errors
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)