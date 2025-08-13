"""
Modèle pour stocker les informations structurées de la constitution
Optimisation pour ChatNow avec cache et recherche rapide
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class ConstitutionArticle(Base):
    """Table pour stocker les articles de la constitution"""
    __tablename__ = "constitution_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    article_number = Column(String(10), nullable=False, index=True)  # "15", "16", etc.
    title = Column(String(500), nullable=True)  # Titre de l'article
    content = Column(Text, nullable=False)  # Contenu complet de l'article
    chapter = Column(String(100), nullable=True, index=True)  # Chapitre
    section = Column(String(100), nullable=True, index=True)  # Section
    part = Column(String(100), nullable=True, index=True)  # Partie
    page_number = Column(Integer, nullable=True)  # Numéro de page dans le fichier original
    line_start = Column(Integer, nullable=True)  # Ligne de début
    line_end = Column(Integer, nullable=True)  # Ligne de fin
    keywords = Column(Text, nullable=True)  # Mots-clés extraits
    category = Column(String(100), nullable=True, index=True)  # Catégorie (droits, institutions, etc.)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Index pour optimiser les recherches
    __table_args__ = (
        Index('idx_article_search', 'article_number', 'category', 'is_active'),
        Index('idx_content_search', 'content', 'keywords'),
        Index('idx_structure_search', 'chapter', 'section', 'part'),
    )

class ConstitutionStructure(Base):
    """Table pour stocker la structure de la constitution"""
    __tablename__ = "constitution_structure"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False)  # Niveau hiérarchique (1=partie, 2=chapitre, 3=section)
    title = Column(String(500), nullable=False)
    parent_id = Column(Integer, nullable=True)  # Référence vers le parent
    start_article = Column(String(10), nullable=True)  # Premier article de cette section
    end_article = Column(String(10), nullable=True)  # Dernier article de cette section
    content_summary = Column(Text, nullable=True)  # Résumé du contenu
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ConstitutionKeyword(Base):
    """Table pour stocker les mots-clés et leur contexte"""
    __tablename__ = "constitution_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), nullable=False, index=True)
    article_id = Column(Integer, nullable=False, index=True)
    context = Column(Text, nullable=True)  # Contexte autour du mot-clé
    frequency = Column(Integer, default=1)  # Fréquence dans l'article
    importance_score = Column(Integer, default=1)  # Score d'importance (1-10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConstitutionCache(Base):
    """Table pour le cache des réponses fréquentes"""
    __tablename__ = "constitution_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    question_hash = Column(String(64), nullable=False, unique=True, index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    article_references = Column(Text, nullable=True)  # Articles cités
    hit_count = Column(Integer, default=1)  # Nombre d'utilisations
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Expiration du cache
