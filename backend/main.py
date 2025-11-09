from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import func
import logging
import json

from models import Card, CardSearchHistory, get_db
from checklist_api import router as checklist_router
from ebay_api import eBayAPI, eBayAPIError
from ebay_service import eBayService, eBayOAuthError
from rate_limiter import rate_limiter
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------
# Initialize FastAPI
# -------------------------------------------------
app = FastAPI(title="Card Collection API")

# -------------------------------------------------
# CORS Middleware (allow React and local API)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:8000",  # Local FastAPI (optional)
        "*"                       # Wildcard for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Setup logging
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Include your API routers
# -------------------------------------------------
app.include_router(checklist_router)
# Add others like eBay if needed:
# app.include_router(ebay_router)

# -------------------------------------------------
# Serve built React app (Vision UI Dashboard)
# -------------------------------------------------
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

# -------------------------------------------------
# Run the server
# -------------------------------------------------

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

    # Count cards with eBay pricing data (has ebay_avg_price)
    cards_with_ebay_pricing = db.query(Card).filter(Card.ebay_avg_price.isnot(None)).count()

    # Only calculate profit/loss if we have eBay pricing data
    # Otherwise return None to indicate it's not available yet
    profit_loss = None
    if cards_with_ebay_pricing > 0:
        profit_loss = total_value - total_invested

    return {
        "total_cards": total_cards,
        "total_value": total_value,
        "total_invested": total_invested,
        "profit_loss": profit_loss,
        "has_ebay_data": cards_with_ebay_pricing > 0
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
                card.last_price_check = datetime.now(timezone.utc)
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
        last_checked=datetime.now(timezone.utc).isoformat(),
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

# ==============================
# EBAY API ENDPOINTS
# ==============================

class EbayPriceResult(BaseModel):
    """Response model for eBay price check"""
    card_id: int
    player: str
    avg_sold_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    listing_count: int
    sample_urls: List[str]
    search_keywords: str
    last_checked: str
    success: bool
    message: Optional[str] = None

@app.get("/ebay/test-connection")
def test_ebay_connection():
    """Test eBay API connection and credentials"""
    try:
        ebay = eBayAPI()
        result = ebay.test_connection()
        return result
    except eBayAPIError as e:
        logger.error(f"eBay connection test failed: {e}")
        return {
            "success": False,
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error testing eBay connection: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.post("/cards/{card_id}/check-ebay-price", response_model=EbayPriceResult)
def check_card_ebay_price(card_id: int, db: Session = Depends(get_db)):
    """
    Check eBay prices for a specific card.
    Searches sold listings and updates the card's ebay_avg_price and last_price_check.
    """
    # Get the card
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    try:
        # Initialize eBay API
        ebay = eBayAPI()

        # Search for sold listings
        logger.info(f"Checking eBay price for card {card_id}: {card.player}")
        result = ebay.search_sold_listings(
            player=card.player,
            year=card.year,
            set_name=card.set_name,
            card_number=card.card_number
        )

        # Update card in database
        card.ebay_avg_price = result['avg_price']
        card.last_price_check = datetime.now(timezone.utc)
        db.commit()

        timestamp = datetime.now(timezone.utc).isoformat()

        # Return result
        return EbayPriceResult(
            card_id=card_id,
            player=card.player,
            avg_sold_price=result['avg_price'],
            min_price=result['min_price'],
            max_price=result['max_price'],
            listing_count=result['listing_count'],
            sample_urls=result['sample_urls'],
            search_keywords=result['search_keywords'],
            last_checked=timestamp,
            success=True,
            message=f"Found {result['listing_count']} sold listings" if result['listing_count'] > 0 else "No sold listings found"
        )

    except eBayAPIError as e:
        logger.error(f"eBay API error for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"eBay API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error checking eBay price for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

class BulkPriceCheckResponse(BaseModel):
    """Response model for bulk price check"""
    total_cards: int
    successful: int
    failed: int
    results: List[EbayPriceResult]
    errors: List[str]

@app.post("/cards/check-tracked-prices", response_model=BulkPriceCheckResponse)
def check_tracked_prices(db: Session = Depends(get_db)):
    """
    Check eBay prices for all cards marked as tracked_for_pricing.
    Limited to 20 cards to respect rate limits.
    """
    # Get tracked cards (max 20)
    tracked_cards = db.query(Card).filter(Card.tracked_for_pricing == True).limit(20).all()

    if not tracked_cards:
        return BulkPriceCheckResponse(
            total_cards=0,
            successful=0,
            failed=0,
            results=[],
            errors=["No cards are marked for price tracking"]
        )

    try:
        ebay = eBayAPI()
    except eBayAPIError as e:
        logger.error(f"Failed to initialize eBay API: {e}")
        raise HTTPException(status_code=500, detail=f"eBay API initialization failed: {str(e)}")

    results = []
    errors = []
    successful = 0
    failed = 0

    for idx, card in enumerate(tracked_cards, 1):
        try:
            logger.info(f"Checking price {idx}/{len(tracked_cards)}: {card.player}")

            # Search for sold listings
            result = ebay.search_sold_listings(
                player=card.player,
                year=card.year,
                set_name=card.set_name,
                card_number=card.card_number
            )

            # Update card in database
            card.ebay_avg_price = result['avg_price']
            card.last_price_check = datetime.now(timezone.utc)
            db.commit()

            timestamp = datetime.now(timezone.utc).isoformat()

            # Add to results
            results.append(EbayPriceResult(
                card_id=card.id,
                player=card.player,
                avg_sold_price=result['avg_price'],
                min_price=result['min_price'],
                max_price=result['max_price'],
                listing_count=result['listing_count'],
                sample_urls=result['sample_urls'],
                search_keywords=result['search_keywords'],
                last_checked=timestamp,
                success=True,
                message=f"Found {result['listing_count']} sold listings" if result['listing_count'] > 0 else "No sold listings found"
            ))

            successful += 1

        except eBayAPIError as e:
            logger.error(f"eBay API error for card {card.id}: {e}")
            errors.append(f"{card.player}: {str(e)}")
            failed += 1
            db.rollback()

        except Exception as e:
            logger.error(f"Unexpected error for card {card.id}: {e}")
            errors.append(f"{card.player}: Unexpected error - {str(e)}")
            failed += 1
            db.rollback()

    return BulkPriceCheckResponse(
        total_cards=len(tracked_cards),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors
    )

@app.get("/ebay/rate-limit-stats")
def get_rate_limit_stats():
    """Get current eBay API rate limit statistics"""
    try:
        stats = rate_limiter.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {
            "error": str(e),
            "count": 0,
            "limit": 5000,
            "remaining": 5000
        }

@app.post("/ebay/reset-rate-limit")
def reset_rate_limit():
    """Reset rate limit counter (admin only)"""
    try:
        rate_limiter.reset()
        return {"message": "Rate limit counter reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================
# EBAY OAUTH API ENDPOINTS (Browse API)
# ==============================

@app.get("/cards/{card_id}/price")
def get_card_price_oauth(card_id: int, db: Session = Depends(get_db)):
    """
    Get eBay pricing for a card using OAuth Browse API.
    Uses Client Credentials Grant flow for authenticated access.
    """
    # Get the card
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    try:
        # Initialize eBay OAuth service
        ebay_service = eBayService()

        # Build search parameters
        year = card.year or ""
        brand = card.set_name.split()[0] if card.set_name else ""  # Extract brand from set name
        player_name = card.player or ""
        card_number = card.card_number

        if not player_name:
            raise HTTPException(status_code=400, detail="Card must have a player name")

        logger.info(f"Fetching OAuth price for card {card_id}: {player_name}")

        # Get pricing using OAuth service
        pricing = ebay_service.get_average_price(
            year=year,
            brand=brand,
            player_name=player_name,
            card_number=card_number,
            card_id=card_id
        )

        # Update card in database if we got a price
        if pricing.get('avg_price'):
            card.ebay_avg_price = pricing['avg_price']
            card.last_price_check = datetime.now(timezone.utc)
            db.commit()

        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "card_id": card_id,
            "player": player_name,
            "search_query": f"{year} {brand} {player_name} {card_number or ''}".strip(),
            "pricing": {
                "avg_price": pricing.get('avg_price'),
                "min_price": pricing.get('min_price'),
                "max_price": pricing.get('max_price'),
                "count": pricing.get('count', 0)
            },
            "last_checked": timestamp,
            "success": pricing.get('avg_price') is not None,
            "message": f"Found {pricing.get('count', 0)} listings" if pricing.get('count') else "No listings found",
            "error": pricing.get('error')
        }

    except eBayOAuthError as e:
        logger.error(f"eBay OAuth error for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"eBay OAuth error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching OAuth price for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/ebay/oauth/test-connection")
def test_ebay_oauth_connection():
    """Test eBay OAuth connection and credentials"""
    try:
        service = eBayService()
        result = service.test_connection()
        return result
    except eBayOAuthError as e:
        logger.error(f"eBay OAuth connection test failed: {e}")
        return {
            "success": False,
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error testing OAuth connection: {e}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/cards/{card_id}/search-with-images")
def search_card_with_images(card_id: int, db: Session = Depends(get_db)):
    """
    Enhanced search that returns full eBay results with images for user selection.
    Logs search progress and allows user to confirm the correct card match.
    """
    logger.info(f"Starting enhanced search for card {card_id}")

    # Get the card
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        logger.error(f"Card {card_id} not found")
        raise HTTPException(status_code=404, detail="Card not found")

    try:
        # Log: Starting search
        logger.info(f"Card found: {card.player} - {card.year} {card.set_name} #{card.card_number}")

        # Check if we have a previous search history for this card
        previous_search = db.query(CardSearchHistory).filter(
            CardSearchHistory.card_id == card_id,
            CardSearchHistory.user_confirmed == True
        ).order_by(CardSearchHistory.selected_at.desc()).first()

        # Initialize eBay OAuth service
        ebay_service = eBayService()

        # Build search parameters
        year = card.year or ""
        brand = card.set_name.split()[0] if card.set_name else ""
        player_name = card.player or ""
        card_number = card.card_number

        if not player_name:
            logger.error(f"Card {card_id} missing player name")
            raise HTTPException(status_code=400, detail="Card must have a player name for eBay search")

        logger.info(f"Search parameters: year={year}, brand={brand}, player={player_name}, card_number={card_number}")

        # Perform the search
        logger.info(f"Calling eBay API for card {card_id}")
        result = ebay_service.search_card(
            year=year,
            brand=brand,
            player_name=player_name,
            card_number=card_number,
            card_id=card_id
        )

        # Extract items with images
        items = result.get('items', [])
        total_results = result.get('total_results', 0)

        logger.info(f"eBay search completed: {total_results} results found")

        # Format results for frontend
        formatted_items = []
        for item in items[:20]:  # Return top 20 results
            try:
                formatted_item = {
                    'item_id': item.get('itemId', ''),
                    'title': item.get('title', 'No title'),
                    'price': float(item.get('price', {}).get('value', 0)),
                    'currency': item.get('price', {}).get('currency', 'USD'),
                    'image_url': item.get('image', {}).get('imageUrl', ''),
                    'item_url': item.get('itemWebUrl', ''),
                    'condition': item.get('condition', 'Unknown'),
                    'seller': item.get('seller', {}).get('username', 'Unknown')
                }
                formatted_items.append(formatted_item)
            except Exception as e:
                logger.warning(f"Error formatting item: {e}")
                continue

        # Save search to history
        search_history = CardSearchHistory(
            card_id=card_id,
            player=player_name,
            year=year,
            set_name=card.set_name,
            card_number=card_number,
            search_query=result.get('search_query', ''),
            all_results=json.dumps(formatted_items),
            total_results=total_results,
            user_confirmed=False,
            needs_refinement=False
        )
        db.add(search_history)
        db.commit()

        logger.info(f"Search history saved for card {card_id}")

        # Return comprehensive response
        response = {
            "success": True,
            "card_id": card_id,
            "card_info": {
                "player": player_name,
                "year": year,
                "set_name": card.set_name,
                "card_number": card_number
            },
            "search_query": result.get('search_query', ''),
            "total_results": total_results,
            "items": formatted_items,
            "pricing": result.get('pricing'),
            "has_previous_selection": previous_search is not None,
            "previous_selection": {
                "item_id": previous_search.selected_ebay_item_id,
                "title": previous_search.selected_ebay_title,
                "image_url": previous_search.selected_ebay_image_url,
                "price": previous_search.selected_ebay_price
            } if previous_search else None,
            "search_history_id": search_history.id,
            "message": f"Found {total_results} results" if total_results > 0 else "No results found. Try refining your search.",
            "suggestions": [
                "Add more details (card number, set name, year)",
                "Check spelling of player name",
                "Try without card number if no results"
            ] if total_results == 0 else []
        }

        logger.info(f"Returning {len(formatted_items)} formatted results to frontend")
        return response

    except eBayOAuthError as e:
        logger.error(f"eBay OAuth error for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"eBay search error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/cards/{card_id}/confirm-selection")
def confirm_card_selection(
    card_id: int,
    search_history_id: int,
    selected_item_id: str,
    db: Session = Depends(get_db)
):
    """
    User confirms which eBay listing matches their card.
    Updates search history and card pricing.
    """
    logger.info(f"User confirming selection for card {card_id}, item {selected_item_id}")

    # Get the search history
    search_history = db.query(CardSearchHistory).filter(
        CardSearchHistory.id == search_history_id
    ).first()

    if not search_history:
        raise HTTPException(status_code=404, detail="Search history not found")

    # Parse the results to find the selected item
    all_results = json.loads(search_history.all_results)
    selected_item = next((item for item in all_results if item['item_id'] == selected_item_id), None)

    if not selected_item:
        raise HTTPException(status_code=404, detail="Selected item not found in search results")

    # Update search history with user confirmation
    search_history.user_confirmed = True
    search_history.selected_ebay_item_id = selected_item['item_id']
    search_history.selected_ebay_title = selected_item['title']
    search_history.selected_ebay_image_url = selected_item['image_url']
    search_history.selected_ebay_price = selected_item['price']
    search_history.selected_at = datetime.now(timezone.utc)

    # Update the card's price
    card = db.query(Card).filter(Card.id == card_id).first()
    if card:
        card.ebay_avg_price = selected_item['price']
        card.last_price_check = datetime.now(timezone.utc)

    db.commit()

    logger.info(f"Selection confirmed: {selected_item['title']} @ ${selected_item['price']}")

    return {
        "success": True,
        "message": "Selection confirmed and card price updated",
        "selected_item": selected_item,
        "card_updated": True
    }

# ================================
# ADMIN API ANALYTICS ENDPOINTS
# ================================

@app.get("/admin/api-usage/summary")
def get_api_usage_summary(db: Session = Depends(get_db)):
    """Get summary of today's eBay API usage"""
    try:
        from models import EbayApiCallLog
        from datetime import date
        from sqlalchemy import func

        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Get today's calls
        total_calls = db.query(func.count(EbayApiCallLog.id)).filter(
            EbayApiCallLog.request_timestamp >= today_start
        ).scalar()

        # Get real API calls (not cache hits)
        real_calls = db.query(func.count(EbayApiCallLog.id)).filter(
            EbayApiCallLog.request_timestamp >= today_start,
            EbayApiCallLog.cache_hit == False
        ).scalar()

        # Get cache hits
        cache_hits = db.query(func.count(EbayApiCallLog.id)).filter(
            EbayApiCallLog.request_timestamp >= today_start,
            EbayApiCallLog.cache_hit == True
        ).scalar()

        # Calculate cache hit rate
        cache_hit_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0

        # Get average response time
        avg_response_time = db.query(func.avg(EbayApiCallLog.response_time_ms)).filter(
            EbayApiCallLog.request_timestamp >= today_start,
            EbayApiCallLog.success == True
        ).scalar() or 0

        # Get success rate
        successful_calls = db.query(func.count(EbayApiCallLog.id)).filter(
            EbayApiCallLog.request_timestamp >= today_start,
            EbayApiCallLog.success == True
        ).scalar()

        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

        return {
            "today": today.isoformat(),
            "total_calls": total_calls,
            "real_calls": real_calls,
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "remaining_limit": max(0, 5000 - real_calls),
            "daily_limit": 5000,
            "avg_response_time_ms": round(avg_response_time, 2),
            "success_rate": round(success_rate, 2)
        }

    except Exception as e:
        logger.error(f"Error getting API usage summary: {e}")
        return {
            "error": str(e),
            "total_calls": 0,
            "real_calls": 0,
            "cache_hits": 0,
            "remaining_limit": 5000
        }

@app.get("/admin/api-usage/recent")
def get_recent_api_calls(limit: int = 100, db: Session = Depends(get_db)):
    """Get recent API call logs"""
    try:
        from models import EbayApiCallLog

        calls = db.query(EbayApiCallLog).order_by(
            EbayApiCallLog.request_timestamp.desc()
        ).limit(limit).all()

        return {
            "count": len(calls),
            "calls": [
                {
                    "id": call.id,
                    "timestamp": call.request_timestamp.isoformat(),
                    "endpoint": call.endpoint,
                    "query": call.search_query,
                    "card_id": call.card_id,
                    "cache_hit": call.cache_hit,
                    "success": call.success,
                    "response_status": call.response_status,
                    "response_time_ms": call.response_time_ms,
                    "items_returned": call.items_returned,
                    "error_message": call.error_message
                }
                for call in calls
            ]
        }

    except Exception as e:
        logger.error(f"Error getting recent API calls: {e}")
        return {"error": str(e), "calls": []}

@app.get("/admin/api-usage/trends")
def get_api_usage_trends(days: int = 30, db: Session = Depends(get_db)):
    """Get API usage trends over the last N days"""
    try:
        from models import EbayApiCallLog
        from datetime import date, timedelta
        from sqlalchemy import func, cast, Date, Integer

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Query daily stats
        daily_stats = db.query(
            cast(EbayApiCallLog.request_timestamp, Date).label('date'),
            func.count(EbayApiCallLog.id).label('total_calls'),
            func.sum(func.cast(EbayApiCallLog.cache_hit == False, Integer)).label('real_calls'),
            func.sum(func.cast(EbayApiCallLog.cache_hit == True, Integer)).label('cache_hits')
        ).filter(
            EbayApiCallLog.request_timestamp >= start_date
        ).group_by(
            cast(EbayApiCallLog.request_timestamp, Date)
        ).order_by(
            cast(EbayApiCallLog.request_timestamp, Date)
        ).all()

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "data": [
                {
                    "date": str(stat.date),
                    "total_calls": stat.total_calls,
                    "real_calls": stat.real_calls or 0,
                    "cache_hits": stat.cache_hits or 0
                }
                for stat in daily_stats
            ]
        }

    except Exception as e:
        logger.error(f"Error getting API usage trends: {e}")
        return {"error": str(e), "data": []}

@app.get("/admin/cache/stats")
def get_cache_stats(db: Session = Depends(get_db)):
    """Get cache statistics"""
    try:
        from models import EbaySearchCache

        total_entries = db.query(func.count(EbaySearchCache.id)).scalar()

        # Count expired entries
        now = datetime.now(timezone.utc)
        expired_entries = db.query(func.count(EbaySearchCache.id)).filter(
            EbaySearchCache.expires_at < now
        ).scalar()

        active_entries = total_entries - expired_entries

        # Get most hit cache entries
        top_cached = db.query(EbaySearchCache).order_by(
            EbaySearchCache.hit_count.desc()
        ).limit(10).all()

        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "top_cached": [
                {
                    "query": cache.search_query,
                    "hit_count": cache.hit_count,
                    "created_at": cache.created_at.isoformat(),
                    "expires_at": cache.expires_at.isoformat()
                }
                for cache in top_cached
            ]
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


# ================================
# VERSION & UPDATE ENDPOINTS
# ================================

@app.get("/version/current")
def get_current_version():
    """Get current application version"""
    try:
        with open('version.json', 'r') as f:
            version_data = json.load(f)
        return version_data
    except FileNotFoundError:
        return {
            "version": "0.2.0",
            "release_date": "2025-01-03",
            "github_repo": "BaseballBinder/BaseballBinder"
        }
    except Exception as e:
        logger.error(f"Error reading version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/version/check-update")
async def check_for_updates():
    """Check if a newer version is available on GitHub"""
    try:
        # Read local version
        with open('version.json', 'r') as f:
            local_version = json.load(f)

        # Check GitHub for latest release
        import requests
        github_repo = local_version.get('github_repo', 'BaseballBinder/BaseballBinder')
        github_api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

        response = requests.get(github_api_url, timeout=5)

        if response.status_code == 404:
            # No releases yet
            return {
                "update_available": False,
                "current_version": local_version['version'],
                "message": "No releases available yet"
            }

        response.raise_for_status()
        latest_release = response.json()

        # Parse version strings (assuming semver: v0.2.0)
        latest_version = latest_release['tag_name'].lstrip('v')
        current_version = local_version['version']

        # Simple version comparison (you can use packaging.version for more robust comparison)
        update_available = latest_version != current_version

        result = {
            "update_available": update_available,
            "current_version": current_version,
            "latest_version": latest_version,
            "release_date": latest_release.get('published_at'),
            "release_notes": latest_release.get('body', ''),
            "download_url": None,
            "installer_url": None
        }

        # Find Windows executable in assets
        for asset in latest_release.get('assets', []):
            if asset['name'].endswith('.exe'):
                result['installer_url'] = asset['browser_download_url']
                result['download_url'] = asset['browser_download_url']
                result['file_size'] = asset['size']
                break

        return result

    except requests.exceptions.Timeout:
        return {
            "update_available": False,
            "error": "Connection timeout while checking for updates"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking for updates: {e}")
        return {
            "update_available": False,
            "error": "Could not connect to update server"
        }
    except Exception as e:
        logger.error(f"Unexpected error checking updates: {e}")
        return {
            "update_available": False,
            "error": str(e)
        }
    from fastapi.staticfiles import StaticFiles

# Serve built React app when ready
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)