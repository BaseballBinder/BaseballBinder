from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
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
    set_name: str
    card_number: str
    player: str
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
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)