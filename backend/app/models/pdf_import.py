from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    constitution_id = Column(Integer, ForeignKey("constitutions.id"), nullable=False)
    article_number = Column(String(50), nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    part = Column(String(100))
    section = Column(String(100))
    page_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Article(id={self.id}, article_number='{self.article_number}', constitution_id={self.constitution_id})>"

class Metadata(Base):
    __tablename__ = "metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    constitution_id = Column(Integer, ForeignKey("constitutions.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Metadata(id={self.id}, key='{self.key}', constitution_id={self.constitution_id})>" 