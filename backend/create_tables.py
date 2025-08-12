#!/usr/bin/env python3
"""
Script pour créer les nouvelles tables articles et metadata
"""

from app.database import engine, Base
from app.models.constitution import Constitution
from app.models.user import User
from app.models.pdf_import import Article, Metadata

def create_tables():
    """Créer toutes les tables"""
    print("🔄 Création des tables...")
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tables créées avec succès!")
    print("📋 Tables disponibles:")
    print("   - constitutions")
    print("   - users")
    print("   - articles (nouvelle)")
    print("   - metadata (nouvelle)")

if __name__ == "__main__":
    create_tables() 