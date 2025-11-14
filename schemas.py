# schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Card Parsing Schemas
class CardParsed(BaseModel):
    card_number: str
    players: List[str] = Field(default_factory=list)
    teams: List[str] = Field(default_factory=list)
    descriptions: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    raw_lines: List[str] = Field(default_factory=list)


class ChecklistParseRequest(BaseModel):
    raw_text: str


# Checklist Creation Schemas
class ChecklistCreateRequest(BaseModel):
    year: int
    product_name: str
    set_type_name: str
    checklist_display_name: str
    card_count_declared: Optional[int] = None
    cards: List[CardParsed]


class ChecklistCreateResponse(BaseModel):
    product_id: int
    checklist_id: int
    cards_inserted: int


# Parallel Parsing Schemas
class ParallelParsed(BaseModel):
    name: str
    print_run: Optional[int] = None
    exclusive: Optional[str] = None
    notes: Optional[str] = None
    raw_line: str


class ParallelParseRequest(BaseModel):
    raw_text: str


# Parallel Creation Schemas
class ParallelCreateRequest(BaseModel):
    year: int
    product_name: str
    parallels: List[ParallelParsed]


class ParallelCreateResponse(BaseModel):
    product_id: int
    parallels_inserted: int


# Checklist Submission Schemas (for admin review)
class ChecklistSubmissionRequest(BaseModel):
    year: int
    product_name: str
    set_type_name: str
    submission_type: str  # "cards" or "parallels"
    card_count_declared: Optional[int] = None  # Expected number of cards
    raw_text: str
    parsed_data: List[dict]  # Parsed cards or parallels


class ChecklistSubmissionResponse(BaseModel):
    submission_id: int
    status: str
    message: str

class ChecklistSubmissionAdmin(BaseModel):
    id: int
    year: int
    product_name: str
    set_type_name: str
    submission_type: str
    card_count_declared: Optional[int] = None
    raw_text: str
    parsed_data: List[dict]
    status: str
    submitted_at: datetime
    admin_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChecklistSubmissionStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


# Product Check Schemas
class ProductCheckRequest(BaseModel):
    year: int
    product_name: str


class ProductCheckResponse(BaseModel):
    exists: bool
    product_id: Optional[int] = None
    existing_types: List[str] = Field(default_factory=list)


# SetType List Response
class SetTypeListResponse(BaseModel):
    set_types: List[str]


# Checklist Update Schemas
class ChecklistUpdateRequest(BaseModel):
    year: Optional[int] = None
    product_name: Optional[str] = None
    set_type_name: Optional[str] = None
    display_name: Optional[str] = None


class ChecklistUpdateResponse(BaseModel):
    checklist_id: int
    message: str
