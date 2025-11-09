from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, index=True)
    set_name = Column(String, index=True)
    card_number = Column(String, index=True)
    player = Column(String, index=True)
    team = Column(String)
    year = Column(String)
    variety = Column(String)
    parallel = Column(String)
    autograph = Column(Boolean, default=False)
    numbered = Column(String)
    graded = Column(String)
    price_paid = Column(Float)
    current_value = Column(Float)
    sold_price = Column(Float)
    location = Column(String)
    notes = Column(String)
    quantity = Column(Integer, default=1)

    # eBay Price Tracking fields
    tracked_for_pricing = Column(Boolean, default=False, index=True)
    last_price_check = Column(DateTime, nullable=True)
    ebay_avg_price = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class EbayApiCallLog(Base):
    __tablename__ = 'ebay_api_calls'

    id = Column(Integer, primary_key=True, index=True)

    # Request info
    endpoint = Column(String, index=True)
    search_query = Column(String)
    card_id = Column(Integer, nullable=True, index=True)
    request_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Response info
    response_status = Column(Integer)
    response_time_ms = Column(Integer, nullable=True)
    items_returned = Column(Integer, nullable=True)

    # Caching
    cache_hit = Column(Boolean, default=False, index=True)

    # Metadata
    ip_address = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    success = Column(Boolean, default=True, index=True)

class EbaySearchCache(Base):
    __tablename__ = 'ebay_search_cache'

    id = Column(Integer, primary_key=True, index=True)

    # Cache key
    search_query = Column(String, unique=True, index=True)

    # Cached data (JSON string)
    result_data = Column(String)  # Store as JSON string

    # Cache metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, index=True)
    hit_count = Column(Integer, default=0)

class CardSearchHistory(Base):
    __tablename__ = 'card_search_history'

    id = Column(Integer, primary_key=True, index=True)

    # Card identification
    card_id = Column(Integer, index=True)
    player = Column(String, index=True)
    year = Column(String)
    set_name = Column(String)
    card_number = Column(String)

    # Search query used
    search_query = Column(String, index=True)

    # User-selected eBay listing
    selected_ebay_item_id = Column(String)
    selected_ebay_title = Column(String)
    selected_ebay_image_url = Column(String)
    selected_ebay_price = Column(Float)

    # All results returned (JSON)
    all_results = Column(String)  # Store as JSON string
    total_results = Column(Integer)

    # User feedback
    user_confirmed = Column(Boolean, default=False)
    needs_refinement = Column(Boolean, default=False)
    refinement_notes = Column(String)

    # Timestamps
    searched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    selected_at = Column(DateTime, nullable=True)

class CardPriceHistory(Base):
    __tablename__ = 'card_price_history'

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, index=True)
    price = Column(Float, nullable=True)
    source = Column(String, default='ebay_browse')  # ebay_browse, manual, other
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    metadata_json = Column(String, nullable=True)  # optional JSON for extra info

DATABASE_URL = "sqlite:///./card_collection.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
