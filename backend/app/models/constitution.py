from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean, BigInteger
from sqlalchemy.sql import func
from app.database import Base
import enum

class ConstitutionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    IN_DEVELOPMENT = "in_development"

class Constitution(Base):
    __tablename__ = "constitutions"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    year = Column(Integer, nullable=True, index=True)
    country = Column(String(100), nullable=False, default="Guinée")
    status = Column(Enum(ConstitutionStatus), default=ConstitutionStatus.ACTIVE)
    content = Column(Text, nullable=True)
    summary = Column(Text)
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    key_topics = Column(Text)  # Stocké comme JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Constitution(id={self.id}, title='{self.title}', year={self.year})>" 