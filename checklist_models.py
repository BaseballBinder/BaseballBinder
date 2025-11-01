from sqlalchemy import Column, Integer, String, Boolean
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

# Create the checklist table
Base.metadata.create_all(bind=engine)
