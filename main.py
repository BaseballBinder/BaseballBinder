from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_
from collections import defaultdict
import logging
import json
import time

from models import Card, CardPriceHistory, CardSearchHistory, CardTrackingHistory, SessionLocal, get_db
from checklist_api import router as checklist_router
from router_checklists import router as checklists_router
from router_parallels import router as parallels_router
from ebay_service import eBayService, eBayOAuthError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Card Collection API")

# Include checklist routes
app.include_router(checklist_router)
app.include_router(checklists_router)
app.include_router(parallels_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_preview_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return url
    upgraded = url
    replacements = ["s-l64", "s-l75", "s-l96", "s-l140", "s-l150", "s-l200", "s-l320", "s-l400", "s-l500"]
    for token in replacements:
        if token in upgraded:
            upgraded = upgraded.replace(token, "s-l800")
    return upgraded

def extract_image_url(item: dict) -> Optional[str]:
    if not item:
        return None
    candidates = [
        item.get("image", {}) or {},
        {"direct": item.get("imageUrl")},
        {"direct": item.get("imageURL")},
        {"direct": item.get("image", {}).get("url")},
        {"direct": item.get("image", {}).get("originalImage")},
    ]
    for source in candidates:
        url = source.get("imageUrl") or source.get("direct")
        if url:
            return normalize_preview_url(url)
    thumbnails = item.get("thumbnailImages") or item.get("additionalImages") or []
    for thumb in thumbnails:
        url = thumb.get("imageUrl") or thumb.get("imageURL") or thumb.get("url")
        if url:
            return normalize_preview_url(url)
    return None

def extract_listing_url(item: dict) -> Optional[str]:
    if not item:
        return None
    for key in ["itemWebUrl", "itemUrl", "itemURL", "legacyLink", "sellerItemLink"]:
        url = item.get(key)
        if url:
            return url
    return None

STAT_CACHE: dict[str, dict] = {}

def get_cached_stat(key: str, ttl_seconds: int, compute_fn):
    now = time.time()
    entry = STAT_CACHE.get(key)
    if entry and now - entry["ts"] < ttl_seconds:
        return entry["data"]
    data = compute_fn()
    STAT_CACHE[key] = {"ts": now, "data": data}
    return data

def invalidate_stat_cache(keys: Optional[List[str]] = None):
    if not keys:
        STAT_CACHE.clear()
    else:
        for key in keys:
            STAT_CACHE.pop(key, None)

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
    preview_image_url: Optional[str] = None
    preview_fit: Optional[str] = 'cover'
    preview_focus: Optional[float] = 50.0
    preview_zoom: Optional[float] = 1.0
    preview_source: Optional[str] = None
    preview_confirmed: bool = False
    preview_confirmed_at: Optional[datetime] = None
    tracked_since: Optional[datetime] = None

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
    preview_image_url: Optional[str] = None
    preview_fit: Optional[str] = None
    preview_focus: Optional[float] = None
    preview_zoom: Optional[float] = None
    preview_source: Optional[str] = None
    preview_confirmed: Optional[bool] = None
    preview_confirmed_at: Optional[datetime] = None

class CardResponse(CardCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    tracked_for_pricing: bool = False
    last_price_check: Optional[datetime] = None
    ebay_avg_price: Optional[float] = None
    preview_image_url: Optional[str] = None
    preview_fit: Optional[str] = 'cover'
    preview_focus: Optional[float] = 50.0
    preview_zoom: Optional[float] = 1.0

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

class CardPreviewUpdate(BaseModel):
    preview_image_url: Optional[str] = None
    preview_fit: Optional[str] = None
    preview_focus: Optional[float] = None
    preview_zoom: Optional[float] = None
    clear: bool = False
    force: bool = False
    source: Optional[str] = None
    mark_confirmed: bool = False

class ImageSearchFilters(BaseModel):
    require_player: bool = True
    require_year: bool = True
    require_set: bool = True
    require_single_card: bool = True
    require_numbering: bool = False
    require_grade: bool = False
    exclude_phrases: List[str] = Field(default_factory=list)

class ImageSearchRequest(BaseModel):
    query: Optional[str] = None
    strategy: str = "strict"
    filters: ImageSearchFilters = Field(default_factory=ImageSearchFilters)
    limit: int = Field(default=24, ge=5, le=50)
    record_history: bool = True

IMAGE_SEARCH_STRATEGIES = {
    "strict": {
        "label": "Exact Match",
        "components": ["player", "year", "set", "variety", "parallel", "numbered_term", "grade_term", "autograph_term"],
    },
    "focused": {
        "label": "Focused",
        "components": ["player", "year", "set", "variety", "numbered_term"],
    },
    "broad": {
        "label": "Broad",
        "components": ["player", "set", "year"],
    },
}

MULTI_LISTING_PHRASES = [
    "pick your", "pick/card", "choose your", "player break", "team break", "case break",
    "sealed case", "hobby box", "blaster box", "factory box", "factory sealed", "complete set",
    "lot of", "lot-", "random team", "group break", "mystery pack", "team pack",
]

GENERIC_EXCLUDE_PHRASES = [
    "custom card", "reprint", "mystery redemption", "digital only", "nft",
]

GRADE_KEYWORDS = ["psa", "bgs", "sgc", "cgc", "beckett", "bvg", "gm", "csg"]
AUTOGRAPH_KEYWORDS = ["auto", "autograph", "sig", "signature", "signed"]

def format_numbered_term(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if "/" in value:
        denom = value.split("/")[-1]
        if denom.isdigit():
            return f"/{denom}"
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits:
        return f"/{digits}"
    return None

def _resolve_component(card: Card, key: str) -> Optional[str]:
    numbered_term = format_numbered_term(card.numbered)
    mapping = {
        "player": card.player,
        "year": card.year,
        "set": card.set_name,
        "variety": card.variety,
        "parallel": card.parallel,
        "numbered_term": numbered_term,
        "grade_term": card.graded,
        "autograph_term": "autograph" if getattr(card, "autograph", False) else None,
    }
    return mapping.get(key)

def build_query_for_strategy(card: Card, strategy_key: str) -> str:
    strategy = IMAGE_SEARCH_STRATEGIES.get(strategy_key) or IMAGE_SEARCH_STRATEGIES["strict"]
    parts = []
    for key in strategy["components"]:
        value = _resolve_component(card, key)
        if value:
            parts.append(str(value).strip())
    return " ".join(part for part in parts if part).strip()

def build_card_search_query(card: Card) -> str:
    return build_query_for_strategy(card, "strict")

def tokenize_terms(value: Optional[str]) -> List[str]:
    if not value:
        return []
    tokens = [token.strip().lower() for token in value.replace("-", " ").split() if token.strip()]
    if value.strip():
        tokens.append(value.strip().lower())
    return list(dict.fromkeys(tokens))

def build_card_context(card: Card) -> Dict:
    numbered_term = format_numbered_term(card.numbered)
    return {
        "player_tokens": tokenize_terms(card.player),
        "year": (card.year or "").strip().lower(),
        "set_terms": tokenize_terms(card.set_name),
        "variety_terms": tokenize_terms(card.variety),
        "parallel_terms": tokenize_terms(card.parallel),
        "numbered_term": numbered_term.lower() if numbered_term else None,
        "grade_terms": tokenize_terms(card.graded),
        "autograph": bool(card.autograph),
    }

def looks_like_multi_listing(title_lower: str) -> bool:
    return any(phrase in title_lower for phrase in MULTI_LISTING_PHRASES)

def analyze_listing(item: Dict, card: Card, filters: ImageSearchFilters, context: Dict) -> Dict:
    title = (item.get("title") or "").lower()
    matched_terms = []
    reasons = []
    score = 0
    passes = True

    def require(condition: bool, reason: str):
        nonlocal passes
        if not condition:
            passes = False
            reasons.append(reason)

    player_tokens = context["player_tokens"]
    player_match = all(token in title for token in player_tokens) if player_tokens else True
    if player_match and player_tokens:
        matched_terms.append("player")
        score += 35
    if filters.require_player:
        require(player_match, "Missing player name")

    year_value = context["year"]
    year_match = bool(year_value) and year_value in title
    if year_match:
        matched_terms.append("year")
        score += 10
    if filters.require_year and year_value:
        require(year_match, "Missing year")

    set_terms = context["set_terms"]
    set_match = any(term in title for term in set_terms) if set_terms else True
    if set_match and set_terms:
        matched_terms.append("set")
        score += 20
    if filters.require_set and set_terms:
        require(set_match, "Missing set/brand")

    variety_terms = context["variety_terms"]
    if variety_terms:
        variety_match = any(term in title for term in variety_terms)
        if variety_match:
            matched_terms.append("variety")
            score += 10
    parallel_terms = context["parallel_terms"]
    if parallel_terms:
        parallel_match = any(term in title for term in parallel_terms)
        if parallel_match:
            matched_terms.append("parallel")
            score += 5

    numbered_term = context["numbered_term"]
    numbering_match = False
    if numbered_term:
        variations = {numbered_term, numbered_term.replace("/", "#/"), numbered_term.replace("/", " /")}
        numbering_match = any(var in title for var in variations)
        if numbering_match:
            matched_terms.append("numbered")
            score += 10
    if filters.require_numbering and numbered_term:
        require(numbering_match, f"Missing numbering {numbered_term}")

    grade_terms = context["grade_terms"] or GRADE_KEYWORDS
    grade_match = any(term in title for term in grade_terms)
    if grade_match and context["grade_terms"]:
        matched_terms.append("grade")
        score += 10
    if filters.require_grade and context["grade_terms"]:
        require(grade_match, "Missing grade mention")

    if context["autograph"]:
        auto_match = any(term in title for term in AUTOGRAPH_KEYWORDS)
        if auto_match:
            matched_terms.append("autograph")
            score += 8
        else:
            reasons.append("Autograph not mentioned")

    if filters.require_single_card:
        require(not looks_like_multi_listing(title), "Appears to be multi-card listing")

    user_excludes = [phrase.lower() for phrase in (filters.exclude_phrases or [])]
    combined_excludes = set(GENERIC_EXCLUDE_PHRASES + user_excludes)
    if any(phrase in title for phrase in combined_excludes):
        require(False, "Excluded keyword present")

    if not item.get("image_url"):
        require(False, "Missing image")

    if not passes:
        score = max(0, score - 20)

    confidence = "high" if score >= 70 else "medium" if score >= 40 else "low"
    if not passes:
        confidence = "rejected"

    return {
        "match_score": score,
        "confidence": confidence,
        "matched_terms": matched_terms,
        "rejection_reasons": reasons,
        "passes": passes,
    }

def evaluate_listings(items: List[Dict], card: Card, filters: ImageSearchFilters) -> Dict:
    context = build_card_context(card)
    approved = []
    rejected = []
    for item in items:
        analysis = analyze_listing(item, card, filters, context)
        enriched = {**item, **analysis}
        if analysis["passes"]:
            approved.append(enriched)
        else:
            rejected.append(enriched)
    approved.sort(key=lambda entry: (-entry["match_score"], entry.get("price") or 0))
    return {
        "context": context,
        "approved": approved,
        "rejected": rejected,
        "total_raw": len(items),
        "rejected_count": len(rejected),
        "rejected_samples": rejected[:5],
    }

def format_ebay_items(items: List[Dict]) -> List[Dict]:
    formatted = []
    for raw in items[:40]:
        try:
            price_obj = raw.get('price') or raw.get('currentBidPrice') or {}
            price_val = price_obj.get('value')
            formatted.append({
                'item_id': raw.get('itemId') or raw.get('item_id') or '',
                'title': raw.get('title', 'No title'),
                'price': float(price_val) if price_val else None,
                'currency': price_obj.get('currency', 'USD'),
                'image_url': extract_image_url(raw) or '',
                'item_url': extract_listing_url(raw) or '',
                'condition': raw.get('condition', 'Unknown'),
                'seller': raw.get('seller', {}).get('username', 'Unknown'),
            })
        except Exception as exc:
            logger.warning(f"Unable to format eBay item: {exc}")
    return formatted

def mark_preview_confirmed(card: Card, source: Optional[str] = None):
    card.preview_confirmed = True
    card.preview_source = source or card.preview_source or "manual"
    card.preview_confirmed_at = datetime.now(timezone.utc)

def clear_preview_confirmation(card: Card):
    card.preview_confirmed = False
    card.preview_source = None
    card.preview_confirmed_at = None

def default_filters_for_card(card: Card) -> ImageSearchFilters:
    numbered_term = format_numbered_term(card.numbered)
    return ImageSearchFilters(
        require_player=True,
        require_year=bool(card.year),
        require_set=bool(card.set_name),
        require_single_card=True,
        require_numbering=bool(numbered_term),
        require_grade=bool(card.graded),
    )

def build_strategy_options(card: Card) -> List[Dict]:
    options = []
    for key, meta in IMAGE_SEARCH_STRATEGIES.items():
        options.append({
            "key": key,
            "label": meta["label"],
            "query": build_query_for_strategy(card, key),
        })
    return options

def execute_card_image_search(
    *,
    card: Card,
    db: Session,
    query: str,
    filters: ImageSearchFilters,
    limit: int,
    strategy: str,
    record_history: bool = True,
):
    ebay_service = eBayService()
    result = ebay_service.search_card(
        year=card.year,
        brand=card.set_name,
        player_name=card.player,
        card_number=card.card_number,
        variety=card.variety,
        parallel=card.parallel,
        autograph=card.autograph,
        graded=card.graded,
        numbered=card.numbered,
        card_id=card.id,
        manual_query=query,
    )

    raw_items = result.get('items', [])
    formatted_items = format_ebay_items(raw_items)
    evaluation = evaluate_listings(formatted_items, card, filters)
    approved = evaluation["approved"][:limit]

    search_history_id = None
    if record_history:
        history = CardSearchHistory(
            card_id=card.id,
            player=card.player,
            year=card.year,
            set_name=card.set_name,
            card_number=card.card_number,
            search_query=query,
            all_results=json.dumps(approved),
            total_results=len(approved),
            user_confirmed=False,
            needs_refinement=False,
        )
        db.add(history)
        db.commit()
        search_history_id = history.id

    return {
        "card_id": card.id,
        "query_used": query,
        "strategy": strategy,
        "filters": filters.model_dump(),
        "total_results": result.get('total_results', len(raw_items)),
        "items": approved,
        "items_returned": len(approved),
        "rejected_count": evaluation["rejected_count"],
        "rejected_samples": evaluation["rejected_samples"],
        "search_history_id": search_history_id,
        "pricing": result.get('pricing'),
        "context": evaluation["context"],
    }

def lock_existing_previews():
    try:
        session = SessionLocal()
        cards = session.query(Card).filter(
            Card.preview_image_url.isnot(None),
            (Card.preview_confirmed.is_(None)) | (Card.preview_confirmed == False)
        ).all()
        if cards:
            for card in cards:
                mark_preview_confirmed(card, card.preview_source or "legacy")
            session.commit()
    except Exception as exc:
        logger.warning(f"Preview lock bootstrap skipped: {exc}")
    finally:
        try:
            session.close()
        except Exception:
            pass

lock_existing_previews()

@app.get("/")
def root():
    return {"message": "Card Collection API", "version": "1.0"}

def attach_tracked_since(cards: List[Card], db: Session):
    tracked_ids = [card.id for card in cards if getattr(card, "tracked_for_pricing", False) and not getattr(card, "tracked_since", None)]
    if not tracked_ids:
        return
    rows = (
        db.query(CardTrackingHistory.card_id, func.max(CardTrackingHistory.created_at))
        .filter(
            CardTrackingHistory.card_id.in_(tracked_ids),
            CardTrackingHistory.action == "track",
        )
        .group_by(CardTrackingHistory.card_id)
        .all()
    )
    mapping = {card_id: ts for card_id, ts in rows}
    for card in cards:
        ts = mapping.get(card.id)
        if ts:
            setattr(card, "tracked_since", ts)

@app.post("/cards/", response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    db_card = Card(**card.dict())
    if db_card.preview_image_url:
        mark_preview_confirmed(db_card, db_card.preview_source or "import")
    elif db_card.preview_confirmed and db_card.preview_image_url is None:
        db_card.preview_confirmed = False
        db_card.preview_source = None
        db_card.preview_confirmed_at = None
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    invalidate_stat_cache()
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
    attach_tracked_since(cards, db)
    return cards

@app.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.tracked_for_pricing and not card.tracked_since:
        attach_tracked_since([card], db)
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
    invalidate_stat_cache()
    return card

@app.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    invalidate_stat_cache()
    return {"message": "Card deleted successfully"}

@app.delete("/cards/")
def delete_all_cards(db: Session = Depends(get_db)):
    """Delete all cards from the collection"""
    try:
        count = db.query(Card).count()
        db.query(Card).delete()
        db.commit()
        invalidate_stat_cache()
        return {"message": f"Successfully deleted {count} card(s)", "deleted_count": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/")
def get_collection_stats(db: Session = Depends(get_db)):
    """Get collection statistics"""
    def compute():
        total_cards = db.query(Card).count()
        total_value = db.query(func.sum(Card.current_value)).scalar() or 0
        total_invested = db.query(func.sum(Card.price_paid)).scalar() or 0
        cards_with_ebay_pricing = db.query(Card).filter(Card.ebay_avg_price.isnot(None)).count()
        profit_loss = total_value - total_invested if cards_with_ebay_pricing > 0 else None
        return {
            "total_cards": total_cards,
            "total_value": total_value,
            "total_invested": total_invested,
            "profit_loss": profit_loss,
            "has_ebay_data": cards_with_ebay_pricing > 0
        }
    return get_cached_stat("stats:basic", 60, compute)

@app.get("/stats/enhanced")
def get_enhanced_stats(db: Session = Depends(get_db)):
    def compute():
        total_cards = db.query(Card).count()
        total_value = db.query(func.sum(Card.current_value)).scalar() or 0
        total_invested = db.query(func.sum(Card.price_paid)).scalar() or 0
        cards_with_ebay_pricing = db.query(Card).filter(Card.ebay_avg_price.isnot(None)).count()
        profit_loss = total_value - total_invested if cards_with_ebay_pricing > 0 else None
        tracked_count = db.query(Card).filter(Card.tracked_for_pricing == True).count()
        unique_sets = db.query(func.count(func.distinct(Card.set_name))).scalar() or 0

        now = datetime.now(timezone.utc)
        cards_added_trend_7d = []
        for i in range(6, -1, -1):
            day_start = now - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            daily_count = db.query(Card).filter(
                and_(Card.created_at >= day_start, Card.created_at < day_end)
            ).count()
            cards_added_trend_7d.append(daily_count)

        value_trend_7d = [float(total_value) if i == 6 else 0 for i in range(7)]
        return {
            "total_cards": total_cards,
            "total_value": total_value,
            "total_invested": total_invested,
            "profit_loss": profit_loss,
            "tracked_count": tracked_count,
            "unique_sets": unique_sets,
            "value_trend_7d": value_trend_7d,
            "cards_added_trend_7d": cards_added_trend_7d,
            "has_ebay_data": cards_with_ebay_pricing > 0
        }
    return get_cached_stat("stats:enhanced", 60, compute)

@app.get("/stats/top-tracked-cards")
def get_top_tracked_cards(limit: int = Query(default=3, le=20), db: Session = Depends(get_db)):
    cache_key = f"stats:top-tracked:{limit}"
    def compute():
        cards = db.query(Card).filter(
            Card.tracked_for_pricing == True,
            Card.current_value.isnot(None)
        ).order_by(Card.current_value.desc()).limit(limit).all()

        result = []
        for card in cards:
            value_change_percent = None
            if card.price_paid and card.current_value and card.price_paid > 0:
                value_change_percent = ((card.current_value - card.price_paid) / card.price_paid) * 100

            result.append({
                "id": card.id,
                "player": card.player,
                "year": card.year,
                "set_name": card.set_name,
                "card_number": card.card_number,
                "current_value": card.current_value,
                "preview_image_url": card.preview_image_url,
                "value_change_percent": round(value_change_percent, 2) if value_change_percent else None
            })
        return result
    return get_cached_stat(cache_key, 60, compute)

@app.get("/stats/top-valuable-cards")
def get_top_valuable_cards(limit: int = Query(default=5, le=20), db: Session = Depends(get_db)):
    """Get top N most valuable cards in collection (regardless of tracking status)"""
    cache_key = f"stats:top-valuable:{limit}"
    def compute():
        cards = db.query(Card).filter(
            Card.current_value.isnot(None)
        ).order_by(Card.current_value.desc()).limit(limit).all()

        result = []
        for card in cards:
            value_change_percent = None
            if card.price_paid and card.current_value and card.price_paid > 0:
                value_change_percent = ((card.current_value - card.price_paid) / card.price_paid) * 100

            result.append({
                "id": card.id,
                "player": card.player,
                "year": card.year,
                "set_name": card.set_name,
                "card_number": card.card_number,
                "variety": card.variety,
                "parallel": card.parallel,
                "current_value": card.current_value,
                "price_paid": card.price_paid,
                "preview_image_url": card.preview_image_url,
                "value_change_percent": round(value_change_percent, 2) if value_change_percent else None
            })
        return result
    return get_cached_stat(cache_key, 60, compute)

@app.get("/stats/card-types")
def get_card_types(db: Session = Depends(get_db)):
    def compute():
        cards = db.query(Card).all()
        types = {"Graded": 0, "Autograph": 0, "Numbered": 0, "Parallel": 0, "Base": 0}
        for card in cards:
            if card.graded:
                types["Graded"] += 1
            elif card.autograph:
                types["Autograph"] += 1
            elif card.numbered:
                types["Numbered"] += 1
            elif card.parallel:
                types["Parallel"] += 1
            else:
                types["Base"] += 1
        return types
    return get_cached_stat("stats:card-types", 120, compute)

@app.get("/stats/team-distribution")
def get_team_distribution(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    key = f"stats:team:{limit}"
    def compute():
        teams = db.query(
            Card.team,
            func.count(Card.id).label('count')
        ).filter(
            Card.team.isnot(None),
            Card.team != ''
        ).group_by(Card.team).order_by(func.count(Card.id).desc()).limit(limit).all()
        return [{"team": team, "count": count} for team, count in teams]
    return get_cached_stat(key, 120, compute)

@app.get("/stats/player-distribution")
def get_player_distribution(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    key = f"stats:player:{limit}"
    def compute():
        players = db.query(
            Card.player,
            func.count(Card.id).label('count')
        ).filter(
            Card.player.isnot(None),
            Card.player != ''
        ).group_by(Card.player).order_by(func.count(Card.id).desc()).limit(limit).all()
        return [{"player": player, "count": count} for player, count in players]
    return get_cached_stat(key, 120, compute)

@app.get("/stats/set-breakdown")
def get_set_breakdown(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    key = f"stats:set-breakdown:{limit}"
    def compute():
        sets = db.query(
            Card.set_name,
            Card.year,
            func.count(Card.id).label('count')
        ).filter(
            Card.set_name.isnot(None),
            Card.set_name != ''
        ).group_by(Card.set_name, Card.year).order_by(func.count(Card.id).desc()).limit(limit).all()
        return [{"set_name": set_name, "year": year, "count": count} for set_name, year, count in sets]
    return get_cached_stat(key, 120, compute)

@app.get("/stats/recent-additions")
def get_recent_additions(limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    key = f"stats:recent:{limit}"
    def compute():
        cards = db.query(Card).order_by(Card.created_at.desc()).limit(limit).all()
        now = datetime.now(timezone.utc)
        result = []
        for card in cards:
            days_ago = 0
            if card.created_at:
                card_dt = card.created_at if card.created_at.tzinfo else card.created_at.replace(tzinfo=timezone.utc)
                days_ago = (now - card_dt).days
            result.append({
                "id": card.id,
                "player": card.player,
                "year": card.year,
                "set_name": card.set_name,
                "card_number": card.card_number,
                "preview_image_url": card.preview_image_url,
                "created_at": card.created_at.isoformat() if card.created_at else None,
                "days_ago": days_ago
            })
        return result
    return get_cached_stat(key, 60, compute)

@app.get("/stats/milestones")
def get_milestones(db: Session = Depends(get_db)):
    def compute():
        total_cards = db.query(Card).count()
        total_value = db.query(func.sum(Card.current_value)).scalar() or 0
        unique_players = db.query(func.count(func.distinct(Card.player))).filter(
            Card.player.isnot(None), Card.player != ''
        ).scalar() or 0

        card_milestones = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
        value_milestones = [100, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        player_milestones = [5, 10, 25, 50, 100, 250, 500]

        def milestone_progress(current, milestones):
            achieved = [m for m in milestones if current >= m]
            next_milestone = next((m for m in milestones if m > current), milestones[-1])
            progress = (current / next_milestone) if next_milestone > 0 else 1.0
            return achieved, next_milestone, min(progress, 1.0)

        cards_achieved, cards_next, cards_progress = milestone_progress(total_cards, card_milestones)
        value_achieved, value_next, value_progress = milestone_progress(total_value, value_milestones)
        players_achieved, players_next, players_progress = milestone_progress(unique_players, player_milestones)

        return {
            "total_cards_current": total_cards,
            "total_cards_milestones": cards_achieved,
            "total_cards_next": cards_next,
            "total_cards_progress": round(cards_progress, 2),
            "total_value_current": total_value,
            "total_value_milestones": value_achieved,
            "total_value_next": value_next,
            "total_value_progress": round(value_progress, 2),
            "unique_players_current": unique_players,
            "unique_players_milestones": players_achieved,
            "unique_players_next": players_next,
            "unique_players_progress": round(players_progress, 2),
        }
    return get_cached_stat("stats:milestones", 300, compute)

@app.get("/stats/monthly-snapshot")
def get_monthly_snapshot(db: Session = Depends(get_db)):
    def compute():
        now = datetime.now(timezone.utc)
        last_30_start = now - timedelta(days=30)
        prev_30_start = now - timedelta(days=60)

        last_30_cards = db.query(Card).filter(Card.created_at >= last_30_start).all()
        prev_30_cards = db.query(Card).filter(Card.created_at >= prev_30_start, Card.created_at < last_30_start).all()

        last = {
            "cards_added": len(last_30_cards),
            "value_added": sum(c.price_paid for c in last_30_cards if c.price_paid) or 0,
            "unique_sets_added": db.query(func.count(func.distinct(Card.set_name))).filter(Card.created_at >= last_30_start).scalar() or 0,
        }
        prev = {
            "cards_added": len(prev_30_cards),
            "value_added": sum(c.price_paid for c in prev_30_cards if c.price_paid) or 0,
            "unique_sets_added": db.query(func.count(func.distinct(Card.set_name))).filter(
                Card.created_at >= prev_30_start,
                Card.created_at < last_30_start
            ).scalar() or 0,
        }

        def pct(current, prior):
            if prior == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - prior) / prior) * 100

        return {
            "last_30_days": last,
            "previous_30_days": prev,
            "change": {
                "cards_added_percent": round(pct(last["cards_added"], prev["cards_added"]), 2),
                "value_added_percent": round(pct(last["value_added"], prev["value_added"]), 2),
                "unique_sets_added_percent": round(pct(last["unique_sets_added"], prev["unique_sets_added"]), 2),
            },
        }
    return get_cached_stat("stats:monthly-snapshot", 300, compute)

@app.get("/stats/year-distribution")
def get_year_distribution(db: Session = Depends(get_db)):
    def compute():
        years = db.query(
            Card.year,
            func.count(Card.id).label('count')
        ).filter(
            Card.year.isnot(None),
            Card.year != ''
        ).group_by(Card.year).order_by(Card.year.desc()).all()
        return [{"year": year, "count": count} for year, count in years]
    return get_cached_stat("stats:year-distribution", 300, compute)

@app.get("/stats/growth-over-time")
def get_growth_over_time(
    period: str = Query(default="monthly", pattern="^(daily|weekly|monthly)$"),
    months: int = Query(default=12, le=36),
    db: Session = Depends(get_db)
):
    cache_key = f"stats:growth:{period}:{months}"

    def compute():
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=months * 30)
        cards = db.query(Card).filter(Card.created_at >= start_date).order_by(Card.created_at).all()

        result = {"card_count": [], "total_value": []}
        if period == "monthly":
            monthly = defaultdict(lambda: {"count": 0, "value": 0})
            for card in cards:
                if not card.created_at:
                    continue
                key = card.created_at.strftime("%Y-%m-01")
                monthly[key]["count"] += 1
                monthly[key]["value"] += card.price_paid or 0
            for key in sorted(monthly.keys()):
                result["card_count"].append({"date": key, "count": monthly[key]["count"]})
                result["total_value"].append({"date": key, "value": round(monthly[key]["value"], 2)})
        return result

    return get_cached_stat(cache_key, 300, compute)

@app.get("/stats/value-trends")
def get_value_trends(
    period: str = Query(default="monthly", pattern="^(daily|weekly|monthly)$"),
    months: int = Query(default=12, le=36),
    db: Session = Depends(get_db)
):
    cache_key = f"stats:value-trends:{period}:{months}"

    def compute():
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=months * 30)
        history = db.query(CardPriceHistory).filter(
            CardPriceHistory.checked_at >= start_date
        ).order_by(CardPriceHistory.checked_at).all()

        result = []
        if period == "monthly":
            monthly = defaultdict(lambda: {"total": 0, "count": 0})
            for entry in history:
                if entry.checked_at and entry.price:
                    key = entry.checked_at.strftime("%Y-%m-01")
                    monthly[key]["total"] += entry.price
                    monthly[key]["count"] += 1
            for key in sorted(monthly.keys()):
                avg_value = monthly[key]["total"] / monthly[key]["count"] if monthly[key]["count"] > 0 else 0
                result.append({"date": key, "avg_value": round(avg_value, 2), "count": monthly[key]["count"]})
        return result

    return get_cached_stat(cache_key, 300, compute)

@app.get("/stats/activity-heatmap")
def get_activity_heatmap(days: int = Query(default=365, le=730), db: Session = Depends(get_db)):
    cache_key = f"stats:heatmap:{days}"

    def compute():
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        cards = db.query(Card).filter(Card.created_at >= start_date).all()

        daily_counts = defaultdict(int)
        for card in cards:
            if card.created_at:
                date_key = card.created_at.date().isoformat()
                daily_counts[date_key] += 1

        result = []
        current = start_date.date()
        end = now.date()
        while current <= end:
            iso = current.isoformat()
            result.append({"date": iso, "count": daily_counts.get(iso, 0)})
            current += timedelta(days=1)
        return result

    return get_cached_stat(cache_key, 300, compute)

# ==============================
# PRICE TRACKING ENDPOINTS
# ==============================

@app.get("/cards/tracked/", response_model=List[CardResponse])
def get_tracked_cards(db: Session = Depends(get_db)):
    """Get all cards marked for price tracking"""
    cards = db.query(Card).filter(Card.tracked_for_pricing == True).all()
    attach_tracked_since(cards, db)
    return cards

@app.post("/cards/update-tracking")
def update_tracking(request: UpdateTrackingRequest, db: Session = Depends(get_db)):
    """Update which cards are being tracked for pricing"""
    try:
        desired_ids = set(request.card_ids or [])
        existing_rows = db.query(Card.id).filter(Card.tracked_for_pricing == True).all()
        existing_ids = {row.id for row in existing_rows}

        to_track = desired_ids - existing_ids
        to_untrack = existing_ids - desired_ids

        if to_track:
            cards_to_track = db.query(Card).filter(Card.id.in_(to_track)).all()
            for card in cards_to_track:
                card.tracked_for_pricing = True
                card.tracked_since = datetime.now(timezone.utc)
                db.add(CardTrackingHistory(card_id=card.id, action="track"))

        if to_untrack:
            cards_to_untrack = db.query(Card).filter(Card.id.in_(to_untrack)).all()
            for card in cards_to_untrack:
                card.tracked_for_pricing = False
                card.tracked_since = None
                db.add(CardTrackingHistory(card_id=card.id, action="untrack"))

        db.commit()
        invalidate_stat_cache()

        return {
            "message": f"Successfully updated tracking for {len(request.card_ids)} card(s)",
            "tracked_count": len(request.card_ids)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cards/{card_id}/preview")
def update_card_preview(card_id: int, payload: CardPreviewUpdate, db: Session = Depends(get_db)):
    """Persist or clear a preview image for a card."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    clear_request = getattr(payload, "clear", False)

    if clear_request:
        card.preview_image_url = None
        card.preview_fit = 'cover'
        card.preview_focus = 50.0
        card.preview_zoom = 1.0
        card.ebay_avg_price = None
        card.current_value = None
        card.last_price_check = None
    else:
        if payload.preview_image_url is not None:
            card.preview_image_url = normalize_preview_url(payload.preview_image_url)
        if payload.preview_fit:
            card.preview_fit = payload.preview_fit
        if payload.preview_focus is not None:
            card.preview_focus = payload.preview_focus
        if payload.preview_zoom is not None:
            card.preview_zoom = max(0.5, min(3.0, payload.preview_zoom))
    card.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "preview_image_url": card.preview_image_url,
        "preview_fit": card.preview_fit,
        "preview_focus": card.preview_focus,
        "preview_zoom": card.preview_zoom,
    }

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

@app.get("/cards/{card_id}/image-search/options")
def get_image_search_options(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    strategies = build_strategy_options(card)
    filters = default_filters_for_card(card)
    context = build_card_context(card)

    return {
        "card_id": card_id,
        "default_strategy": "strict",
        "strategies": strategies,
        "default_query": strategies[0]["query"] if strategies else "",
        "filters": filters.model_dump(),
        "context": context,
        "numbered_term": context.get("numbered_term"),
        "preview_locked": bool(card.preview_image_url and card.preview_confirmed),
        "preview_image_url": card.preview_image_url,
    }

@app.post("/cards/{card_id}/image-search")
def run_image_search(card_id: int, payload: ImageSearchRequest, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    strategy_key = payload.strategy if payload.strategy in IMAGE_SEARCH_STRATEGIES else "strict"
    filters = payload.filters
    query_to_use = (payload.query or build_query_for_strategy(card, strategy_key)).strip()
    if not query_to_use:
        raise HTTPException(status_code=400, detail="A search query is required.")

    try:
        data = execute_card_image_search(
            card=card,
            db=db,
            query=query_to_use,
            filters=filters,
            limit=payload.limit,
            strategy=strategy_key,
            record_history=payload.record_history,
        )
        return data
    except eBayOAuthError as e:
        logger.error(f"eBay OAuth error for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"eBay search error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/cards/{card_id}/search-with-images")
def search_card_with_images(card_id: int, q: Optional[str] = Query(None, alias="q"), db: Session = Depends(get_db)):
    """Search eBay for a card and return listings with images for user confirmation."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    filters = default_filters_for_card(card)
    query_to_use = (q or build_card_search_query(card)).strip()
    strategy = "manual" if q else "strict"

    try:
        data = execute_card_image_search(
            card=card,
            db=db,
            query=query_to_use,
            filters=filters,
            limit=20,
            strategy=strategy,
            record_history=True,
        )

        message = "No listings matched your filters."
        if data["items"]:
            message = f"Found {data['items_returned']} high-confidence matches."
        elif data["total_results"]:
            message = "Listings were found but filtered out. Try relaxing your query."

        return {
            "success": True,
            "card_id": card_id,
            "card_info": {
                "player": card.player,
                "year": card.year,
                "set_name": card.set_name,
                "card_number": card.card_number
            },
            "search_query": data["query_used"],
            "strategy": data["strategy"],
            "filters": data["filters"],
            "total_results": data["total_results"],
            "items": data["items"],
            "pricing": data["pricing"],
            "search_history_id": data["search_history_id"],
            "rejected_count": data["rejected_count"],
            "message": message
        }
    except eBayOAuthError as e:
        logger.error(f"eBay OAuth error for card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"eBay search error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching card {card_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

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
            if db_card.preview_image_url:
                mark_preview_confirmed(db_card, db_card.preview_source or "csv-import")
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
        query_hint = build_card_search_query(card)
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
            card_id=card_id,
            manual_query=query_hint,
        )

        # Extract pricing info from Browse API response
        pricing = result.get('pricing', {})
        avg_price = pricing.get('avg_price')
        sample_urls = [item.get('itemWebUrl', '') for item in result.get('items', [])[:3]]
        sample_images = result.get('sample_images', [])
        preview_candidate = None
        if sample_images:
            preview_candidate = sample_images[0]
        else:
            for item in result.get('items', []):
                image_url = item.get('image', {}).get('imageUrl')
                if image_url:
                    preview_candidate = image_url
                    break
        if preview_candidate:
            preview_candidate = normalize_preview_url(preview_candidate)

        # Update card in database
        card.ebay_avg_price = avg_price
        card.current_value = avg_price  # Update current_value so stats dashboard reflects eBay pricing
        card.last_price_check = datetime.now(timezone.utc)
        if preview_candidate:
            card.preview_image_url = preview_candidate
            card.preview_fit = card.preview_fit or 'cover'
            card.preview_focus = card.preview_focus if card.preview_focus is not None else 50.0
            card.preview_zoom = card.preview_zoom if card.preview_zoom is not None else 1.0
        # Record price history if we have a value
        try:
            if avg_price is not None:
                db.add(CardPriceHistory(card_id=card_id, price=avg_price, source='ebay_browse'))
        except Exception:
            pass
        db.commit()
        invalidate_stat_cache()

        timestamp = datetime.now(timezone.utc).isoformat()

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
            query_hint = build_card_search_query(card)
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
                card_id=card.id,
                manual_query=query_hint,
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

    if successful:
        invalidate_stat_cache()

    return BulkPriceCheckResponse(
        total_cards=len(tracked_cards),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors
    )

@app.get("/cards/{card_id}/tracking-history")
def get_tracking_history(card_id: int, limit: int = Query(default=20, le=100), db: Session = Depends(get_db)):
    card_exists = db.query(Card.id).filter(Card.id == card_id).first()
    if not card_exists:
        raise HTTPException(status_code=404, detail="Card not found")
    rows = (
        db.query(CardTrackingHistory)
            .filter(CardTrackingHistory.card_id == card_id)
            .order_by(CardTrackingHistory.created_at.desc())
            .limit(limit)
            .all()
    )
    return [
        {
            "id": row.id,
            "card_id": row.card_id,
            "action": row.action,
            "actor": row.actor,
            "timestamp": row.created_at.isoformat(),
            "notes": row.notes,
        }
        for row in rows
    ]

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


# ==========================================
# ADMIN AUTHENTICATION - NOT YET ACTIVATED
# ==========================================
# Uncomment this section when ready to activate admin login
#
# class AdminLoginRequest(BaseModel):
#     password: str
#
# ADMIN_PASSWORD = "1234"  # TODO: Move to environment variable in production
#
# @app.post("/admin/login")
# async def admin_login(request: AdminLoginRequest):
#     """
#     Admin login endpoint - validates password and returns success status.
#     Password is currently hardcoded as "1234" but should be moved to env var.
#     """
#     if request.password == ADMIN_PASSWORD:
#         return {"success": True, "message": "Login successful"}
#     else:
#         return {"success": False, "message": "Invalid password"}
# ==========================================


@app.post("/cards/{card_id}/confirm-selection")
def confirm_card_selection(
    card_id: int,
    search_history_id: int,
    selected_item_id: str,
    db: Session = Depends(get_db)
):
    """Persist the user-selected eBay listing and update preview/value."""
    search_history = db.query(CardSearchHistory).filter(
        CardSearchHistory.id == search_history_id
    ).first()

    if not search_history:
        raise HTTPException(status_code=404, detail="Search history not found")

    all_results = json.loads(search_history.all_results)
    selected_item = next((item for item in all_results if item['item_id'] == selected_item_id), None)

    if not selected_item:
        raise HTTPException(status_code=404, detail="Selected item not found in search results")

    search_history.user_confirmed = True
    search_history.selected_ebay_item_id = selected_item['item_id']
    search_history.selected_ebay_title = selected_item['title']
    search_history.selected_ebay_image_url = selected_item['image_url']
    search_history.selected_ebay_price = selected_item['price']
    search_history.selected_at = datetime.now(timezone.utc)

    card = db.query(Card).filter(Card.id == card_id).first()
    if card:
        card.ebay_avg_price = selected_item['price']
        card.current_value = selected_item['price']
        card.last_price_check = datetime.now(timezone.utc)
        card.ebay_item_id = selected_item['item_id']  # Track which specific listing was selected
        if selected_item.get('image_url'):
            card.preview_image_url = normalize_preview_url(selected_item['image_url'])
            card.preview_fit = card.preview_fit or 'cover'
            card.preview_focus = card.preview_focus if card.preview_focus is not None else 50.0
            card.preview_zoom = card.preview_zoom if card.preview_zoom is not None else 1.0
            mark_preview_confirmed(card, "ebay-selection")

    db.commit()

    return {
        "success": True,
        "message": "Selection confirmed and card updated",
        "selected_item": selected_item,
        "card_updated": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
