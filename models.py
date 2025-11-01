from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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