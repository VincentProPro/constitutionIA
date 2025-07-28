from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.constitution import ConstitutionStatus

class ConstitutionBase(BaseModel):
    title: str
    year: Optional[int] = None
    country: str = "Guinée"
    status: ConstitutionStatus = ConstitutionStatus.ACTIVE
    content: Optional[str] = None
    summary: Optional[str] = None
    file_path: Optional[str] = None
    filename: Optional[str] = None
    description: Optional[str] = None
    file_size: Optional[int] = None
    key_topics: Optional[str] = None

class ConstitutionCreate(ConstitutionBase):
    pass

class ConstitutionUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    country: Optional[str] = None
    status: Optional[ConstitutionStatus] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    file_path: Optional[str] = None

class Constitution(ConstitutionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True

class ConstitutionSearch(BaseModel):
    query: str
    year: Optional[int] = None
    status: Optional[ConstitutionStatus] = None
    limit: int = 10
    offset: int = 0 