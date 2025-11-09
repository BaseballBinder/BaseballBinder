from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import func
import logging
import json

from models import Card, CardPriceHistory, get_db
from checklist_api import router as checklist_router
from ebay_service import eBayService, eBayOAuthError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class PriceHistoryPoint(BaseModel):
    t: datetime
    v: float | None

class PriceHistoryResponse(BaseModel):
    card_id: int
    window: str
    points: List[PriceHistoryPoint]

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
    median_price: Optional[float] = None  # Median price (resistant to outliers)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    listing_count: int
    sample_urls: List[str]
    sample_images: List[str] = []  # eBay listing images for visual verification
    search_keywords: str
    last_checked: str
    success: bool
    message: Optional[str] = None

@app.get("/ebay/test-connection")
def test_ebay_connection():
    """Test eBay OAuth connection and credentials"""
    try:
        ebay = eBayService()
        result = ebay.test_connection()
        return result
    except eBayOAuthError as e:
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
    Searches active listings and updates the card's ebay_avg_price and last_price_check.
    """
    # Get the card
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    try:
        # Initialize eBay OAuth service
        ebay = eBayService()

        # Search for active listings using Browse API
        logger.info(f"Checking eBay price for card {card_id}: {card.player}")
        result = ebay.search_card(
            year=card.year,
            brand=card.set_name,
            player_name=card.player,
            card_number=card.card_number,
            variety=card.variety,
            parallel=card.parallel,
            autograph=card.autograph,
            graded=card.graded,
            numbered=card.numbered,
            card_id=card_id
        )

        # Extract pricing info from Browse API response
        pricing = result.get('pricing', {})
        avg_price = pricing.get('avg_price')

        # Update card in database
        card.ebay_avg_price = avg_price
        card.current_value = avg_price  # Update current_value so stats dashboard reflects eBay pricing
        card.last_price_check = datetime.now(timezone.utc)
        # Record price history if we have a value
        try:
            if avg_price is not None:
                db.add(CardPriceHistory(card_id=card_id, price=avg_price, source='ebay_browse'))
        except Exception:
            pass
        db.commit()

        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract sample URLs and images from items
        sample_urls = [item.get('itemWebUrl', '') for item in result.get('items', [])[:3]]
        sample_images = result.get('sample_images', [])

        # Return result
        return EbayPriceResult(
            card_id=card_id,
            player=card.player,
            avg_sold_price=avg_price,
            median_price=pricing.get('median_price'),
            min_price=pricing.get('min_price'),
            max_price=pricing.get('max_price'),
            listing_count=result.get('total_results', 0),
            sample_urls=sample_urls,
            sample_images=sample_images,
            search_keywords=result.get('search_query', ''),
            last_checked=timestamp,
            success=True,
            message=f"Found {result.get('total_results', 0)} active listings" if result.get('total_results', 0) > 0 else "No active listings found"
        )

    except eBayOAuthError as e:
        logger.error(f"eBay OAuth error for card {card_id}: {e}")
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
        ebay = eBayService()
    except eBayOAuthError as e:
        logger.error(f"Failed to initialize eBay OAuth service: {e}")
        raise HTTPException(status_code=500, detail=f"eBay API initialization failed: {str(e)}")

    results = []
    errors = []
    successful = 0
    failed = 0

    for idx, card in enumerate(tracked_cards, 1):
        try:
            logger.info(f"Checking price {idx}/{len(tracked_cards)}: {card.player}")

            # Search for active listings using Browse API
            result = ebay.search_card(
                year=card.year,
                brand=card.set_name,
                player_name=card.player,
                card_number=card.card_number,
                variety=card.variety,
                parallel=card.parallel,
                autograph=card.autograph,
                graded=card.graded,
                numbered=card.numbered,
                card_id=card.id
            )

            # Extract pricing info from Browse API response
            pricing = result.get('pricing', {})
            avg_price = pricing.get('avg_price')

            # Update card in database
            card.ebay_avg_price = avg_price
            card.current_value = avg_price  # Update current_value so stats dashboard reflects eBay pricing
            card.last_price_check = datetime.now(timezone.utc)
            # Record price history if we have a value
            try:
                if avg_price is not None:
                    db.add(CardPriceHistory(card_id=card.id, price=avg_price, source='ebay_browse'))
            except Exception:
                pass
            db.commit()

            timestamp = datetime.now(timezone.utc).isoformat()

            # Extract sample URLs and images from items
            sample_urls = [item.get('itemWebUrl', '') for item in result.get('items', [])[:3]]
            sample_images = result.get('sample_images', [])

            # Add to results
            results.append(EbayPriceResult(
                card_id=card.id,
                player=card.player,
                avg_sold_price=avg_price,
                median_price=pricing.get('median_price'),
                min_price=pricing.get('min_price'),
                max_price=pricing.get('max_price'),
                listing_count=result.get('total_results', 0),
                sample_urls=sample_urls,
                sample_images=sample_images,
                search_keywords=result.get('search_query', ''),
                last_checked=timestamp,
                success=True,
                message=f"Found {result.get('total_results', 0)} active listings" if result.get('total_results', 0) > 0 else "No active listings found"
            ))

            successful += 1

        except eBayOAuthError as e:
            logger.error(f"eBay OAuth error for card {card.id}: {e}")
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

@app.get("/cards/{card_id}/history", response_model=PriceHistoryResponse)
def get_card_price_history(card_id: int, window: str = 'lifetime', db: Session = Depends(get_db)):
    """Return price history points for a card. Window: daily, weekly, monthly, lifetime."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)

    start = None
    w = window.lower()
    if w in ('day', 'daily'):
        start = now - timedelta(days=7)
        w = 'daily'
    elif w in ('week', 'weekly'):
        start = now - timedelta(days=30)
        w = 'weekly'
    elif w in ('month', 'monthly'):
        start = now - timedelta(days=180)
        w = 'monthly'
    else:
        w = 'lifetime'

    q = db.query(CardPriceHistory).filter(CardPriceHistory.card_id == card_id)
    if start is not None:
        q = q.filter(CardPriceHistory.checked_at >= start)
    rows = q.order_by(CardPriceHistory.checked_at.asc()).all()

    points = [PriceHistoryPoint(t=r.checked_at, v=r.price) for r in rows]
    return PriceHistoryResponse(card_id=card_id, window=w, points=points)

@app.get("/ebay/rate-limit-stats")
def get_rate_limit_stats():
    """Get current eBay OAuth API rate limit statistics"""
    try:
        ebay = eBayService()
        count = ebay._get_request_count()
        can_request, message = ebay._can_make_request()
        return {
            "count": count,
            "limit": ebay.daily_limit,
            "remaining": ebay.daily_limit - count,
            "can_request": can_request,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {
            "error": str(e),
            "count": 0,
            "limit": 5000,
            "remaining": 5000,
            "can_request": True,
            "message": "Error retrieving stats"
        }

@app.post("/ebay/reset-rate-limit")
def reset_rate_limit():
    """Reset rate limit counter (admin only)"""
    try:
        import json
        from pathlib import Path
        from datetime import datetime

        request_count_file = Path("ebay_oauth_requests.json")
        date_str = datetime.now().strftime('%Y-%m-%d')

        with open(request_count_file, 'w') as f:
            json.dump({'date': date_str, 'count': 0}, f)

        return {"message": "eBay OAuth rate limit counter reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
