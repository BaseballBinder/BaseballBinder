# -*- coding: utf-8 -*-
"""Quick script to remove Topps Series 1 2025 from database"""
from models import get_db
from checklist_models import Checklist

db = next(get_db())

# Delete Topps Series 1 2025
deleted = db.query(Checklist).filter(
    Checklist.set_name == "Topps Series 1",
    Checklist.year == "2025"
).delete()

db.commit()
print(f"Deleted {deleted} cards from Topps Series 1 2025")
