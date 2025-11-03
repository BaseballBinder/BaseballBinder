from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from models import Base, engine

class Checklist(Base):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True, index=True)
    set_name = Column(String, index=True)
    year = Column(String, index=True)
    card_number = Column(String, index=True)
    player = Column(String, index=True)
    team = Column(String)
    variety = Column(String, index=True)
    rookie = Column(Boolean, default=False)
    parallel = Column(String)

class ChecklistRequest(Base):
    __tablename__ = 'checklist_requests'

    id = Column(Integer, primary_key=True, index=True)
    set_name = Column(String, nullable=False, index=True)
    year = Column(String, nullable=False, index=True)
    manufacturer = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    priority = Column(String, default='normal')  # low, normal, high
    status = Column(String, default='pending', index=True)  # pending, processing, completed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Suggestion(Base):
    __tablename__ = 'suggestions'

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)  # feature, bug, improvement, ui, other
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    email = Column(String, nullable=True)
    status = Column(String, default='new', index=True)  # new, reviewing, planned, completed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create the tables
Base.metadata.create_all(bind=engine)
