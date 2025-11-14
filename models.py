from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, index=True)
    set_name = Column(String, index=True)
    card_number = Column(String, index=True)
    player = Column(String, index=True)
    team = Column(String, index=True)
    year = Column(String, index=True)
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
    ebay_item_id = Column(String, nullable=True)  # Tracks which specific eBay listing was selected
    preview_image_url = Column(String, nullable=True)
    preview_fit = Column(String, nullable=True, default='cover')
    preview_focus = Column(Float, nullable=True, default=50.0)
    preview_zoom = Column(Float, nullable=True, default=1.0)
    preview_source = Column(String, nullable=True)
    preview_confirmed = Column(Boolean, default=False)
    preview_confirmed_at = Column(DateTime, nullable=True)
    tracked_since = Column(DateTime, nullable=True)

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

class CardTrackingHistory(Base):
    __tablename__ = 'card_tracking_history'

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, index=True, nullable=False)
    action = Column(String, nullable=False)  # track or untrack
    actor = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(String, nullable=True)


# ============================================================================
# CHECKLIST MODELS - For parsing and storing Beckett/TCDB-style checklists
# ============================================================================

class Product(Base):
    """Represents a product line for a specific year (e.g., 2024 Topps Series 1)"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    checklists = relationship("ProductChecklist", back_populates="product")
    parallels = relationship("Parallel", back_populates="product")


class SetType(Base):
    """Represents set types like Base, Insert, Autograph, Relic, etc."""
    __tablename__ = 'set_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_custom = Column(Boolean, default=False)  # True if user-created, False if predefined
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    checklists = relationship("ProductChecklist", back_populates="set_type")


class ProductChecklist(Base):
    """Represents a specific checklist within a product (e.g., Base Set, Rookie Debut Insert)"""
    __tablename__ = 'product_checklists'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    set_type_id = Column(Integer, ForeignKey('set_types.id'), nullable=False, index=True)
    display_name = Column(String, nullable=False)
    card_count_declared = Column(Integer, nullable=True)  # Expected number of cards in set
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="checklists")
    set_type = relationship("SetType", back_populates="checklists")
    cards = relationship("ChecklistCard", back_populates="checklist")


class ChecklistCard(Base):
    """Individual cards within a checklist - parsed from raw checklist text"""
    __tablename__ = 'checklist_cards'

    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey('product_checklists.id'), nullable=False, index=True)
    card_number = Column(String, index=True, nullable=False)
    player_name = Column(String, index=True, nullable=False)
    team = Column(String, index=True, nullable=True)  # NULLABLE - only store if present in source
    flags = Column(JSON, nullable=True)  # ["RC", "SP", "AUTO", etc.]
    subset = Column(String, nullable=True)  # "Rookie Debut", "Season Highlights", etc.
    notes = Column(String, nullable=True)  # Any additional description
    raw_line = Column(String, nullable=False)  # Original input line
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    checklist = relationship("ProductChecklist", back_populates="cards")


class Parallel(Base):
    """Parallel variations for a product (e.g., Gold /50, Rainbow Foil)"""
    __tablename__ = 'parallels'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    print_run = Column(Integer, nullable=True)  # e.g., 50 for "/50"
    exclusive = Column(String, nullable=True)  # "Hobby", "Retail", "Hanger", "Value Box", "Superbox"
    notes = Column(String, nullable=True)  # Full text from parentheses
    raw_line = Column(String, nullable=False)  # Original input line
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="parallels")


class ChecklistSubmission(Base):
    """Pending checklist submissions awaiting admin review"""
    __tablename__ = 'checklist_submissions'

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    product_name = Column(String, nullable=False, index=True)
    set_type_name = Column(String, nullable=False)  # Base, Insert, Autograph, Relic, Parallel, etc.
    submission_type = Column(String, nullable=False)  # "cards" or "parallels"
    card_count_declared = Column(Integer, nullable=True)  # Expected number of cards in this type
    raw_text = Column(String, nullable=False)  # Original pasted text
    parsed_data = Column(JSON, nullable=False)  # Parsed cards or parallels as JSON
    status = Column(String, default='pending', index=True)  # pending, approved, rejected
    submitted_by = Column(String, nullable=True)  # Username/email if we add auth later
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    admin_notes = Column(String, nullable=True)
    result_checklist_id = Column(Integer, ForeignKey('product_checklists.id'), nullable=True)
    materialized_at = Column(DateTime, nullable=True)


DATABASE_URL = "sqlite:///./card_collection.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def ensure_column(table_name: str, column_name: str, ddl: str):
    with engine.connect() as conn:
        existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info('{table_name}')"))]
        if column_name not in existing:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))

ensure_column('cards', 'tracked_since', 'tracked_since DATETIME')
ensure_column('cards', 'preview_source', 'preview_source VARCHAR')
ensure_column('cards', 'preview_confirmed', 'preview_confirmed BOOLEAN DEFAULT 0')
ensure_column('cards', 'preview_confirmed_at', 'preview_confirmed_at DATETIME')
ensure_column('checklist_submissions', 'result_checklist_id', 'result_checklist_id INTEGER')
ensure_column('checklist_submissions', 'materialized_at', 'materialized_at DATETIME')
ensure_column('cards', 'ebay_item_id', 'ebay_item_id VARCHAR')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
