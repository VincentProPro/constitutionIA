#!/usr/bin/env python3
"""
Script pour ajouter des données de test dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models.constitution import Constitution, ConstitutionStatus
from app.models.user import User
from app.routers.auth import get_password_hash
from app.database import Base

def create_tables():
    """Créer les tables dans la base de données"""
    Base.metadata.create_all(bind=engine)

def seed_constitutions():
    """Ajouter des constitutions de test"""
    db = SessionLocal()
    
    # Vérifier si des constitutions existent déjà
    existing = db.query(Constitution).count()
    if existing > 0:
        print("Des constitutions existent déjà dans la base de données")
        db.close()
        return
    
    constitutions_data = [
        {
            "title": "Constitution de la République de Guinée (1958)",
            "year": 1958,
            "country": "Guinée",
            "status": ConstitutionStatus.ACTIVE,
            "content": """
            PRÉAMBULE
            Le peuple de Guinée, par ses représentants réunis en Assemblée nationale,
            proclame son adhésion aux droits et libertés définis par la Déclaration universelle
            des droits de l'homme et par la Charte des Nations unies.
            
            TITRE PREMIER - DE LA SOUVERAINETÉ
            Article 1er : La Guinée est une République démocratique et sociale.
            Article 2 : La souveraineté nationale appartient au peuple qui l'exerce par ses représentants
            et par voie de référendum.
            
            TITRE II - DES DROITS ET LIBERTÉS
            Article 3 : Tous les citoyens sont égaux devant la loi.
            Article 4 : La liberté de conscience, de culte et d'opinion est garantie.
            Article 5 : La liberté de réunion et d'association est garantie.
            """,
            "summary": "Première constitution de la Guinée indépendante, établissant les principes démocratiques et les droits fondamentaux."
        },
        {
            "title": "Constitution de la République de Guinée (1990)",
            "year": 1990,
            "country": "Guinée",
            "status": ConstitutionStatus.ACTIVE,
            "content": """
            PRÉAMBULE
            Le peuple de Guinée, soucieux de consolider l'unité nationale,
            de promouvoir la démocratie et de garantir les droits fondamentaux,
            adopte la présente Constitution.
            
            TITRE PREMIER - DE L'ÉTAT ET DE LA SOUVERAINETÉ
            Article 1er : La Guinée est une République unitaire, indivisible, laïque, démocratique et sociale.
            Article 2 : La souveraineté nationale appartient au peuple qui l'exerce par ses représentants élus.
            
            TITRE II - DES DROITS ET LIBERTÉS FONDAMENTAUX
            Article 3 : Tous les citoyens sont égaux devant la loi.
            Article 4 : La liberté de conscience, de culte et d'opinion est garantie.
            Article 5 : La liberté de réunion et d'association est garantie.
            Article 6 : Le droit de propriété est inviolable et sacré.
            
            TITRE III - DU POUVOIR EXÉCUTIF
            Article 7 : Le Président de la République est le chef de l'État.
            Article 8 : Le Président de la République est élu au suffrage universel direct.
            """,
            "summary": "Constitution démocratique établissant un régime présidentiel et garantissant les libertés fondamentales."
        },
        {
            "title": "Constitution de la République de Guinée (2010)",
            "year": 2010,
            "country": "Guinée",
            "status": ConstitutionStatus.ACTIVE,
            "content": """
            PRÉAMBULE
            Le peuple de Guinée, soucieux de consolider l'unité nationale,
            de promouvoir la démocratie et de garantir les droits fondamentaux,
            adopte la présente Constitution.
            
            TITRE PREMIER - DE L'ÉTAT ET DE LA SOUVERAINETÉ
            Article 1er : La Guinée est une République unitaire, indivisible, laïque, démocratique et sociale.
            Article 2 : La souveraineté nationale appartient au peuple qui l'exerce par ses représentants élus.
            
            TITRE II - DES DROITS ET LIBERTÉS FONDAMENTAUX
            Article 3 : Tous les citoyens sont égaux devant la loi.
            Article 4 : La liberté de conscience, de culte et d'opinion est garantie.
            Article 5 : La liberté de réunion et d'association est garantie.
            Article 6 : Le droit de propriété est inviolable et sacré.
            
            TITRE III - DU POUVOIR EXÉCUTIF
            Article 7 : Le Président de la République est le chef de l'État.
            Article 8 : Le Président de la République est élu au suffrage universel direct.
            
            TITRE IV - DU POUVOIR LÉGISLATIF
            Article 9 : Le pouvoir législatif est exercé par l'Assemblée nationale.
            Article 10 : Les députés sont élus au suffrage universel direct.
            
            TITRE V - DU POUVOIR JUDICIAIRE
            Article 11 : Le pouvoir judiciaire est indépendant du pouvoir exécutif et du pouvoir législatif.
            Article 12 : Les juges ne sont soumis qu'à l'autorité de la loi.
            """,
            "summary": "Constitution actuelle de la Guinée, renforçant la séparation des pouvoirs et les garanties démocratiques."
        },
        {
            "title": "Constitution de la République de Guinée (2025) - Projet",
            "year": 2025,
            "country": "Guinée",
            "status": ConstitutionStatus.IN_DEVELOPMENT,
            "content": """
            PROJET DE CONSTITUTION 2025
            [Document en cours de développement]
            
            PRÉAMBULE
            Le peuple de Guinée, conscient de son histoire et de ses responsabilités,
            soucieux de consolider l'unité nationale et de promouvoir un développement durable,
            adopte la présente Constitution.
            
            TITRE PREMIER - PRINCIPES FONDAMENTAUX
            Article 1er : La Guinée est une République démocratique, sociale et environnementale.
            Article 2 : La souveraineté nationale appartient au peuple.
            
            TITRE II - DROITS ET LIBERTÉS
            Article 3 : Tous les citoyens sont égaux devant la loi.
            Article 4 : Les droits fondamentaux sont garantis.
            Article 5 : La protection de l'environnement est un devoir collectif.
            """,
            "summary": "Projet de nouvelle constitution en cours d'élaboration pour 2025."
        }
    ]
    
    for data in constitutions_data:
        constitution = Constitution(**data)
        db.add(constitution)
    
    db.commit()
    print(f"Ajouté {len(constitutions_data)} constitutions de test")
    db.close()

def seed_users():
    """Ajouter des utilisateurs de test"""
    db = SessionLocal()
    
    # Vérifier si des utilisateurs existent déjà
    existing = db.query(User).count()
    if existing > 0:
        print("Des utilisateurs existent déjà dans la base de données")
        db.close()
        return
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@constitutionia.gn",
            "full_name": "Administrateur",
            "hashed_password": get_password_hash("admin123"),
            "is_superuser": True
        },
        {
            "username": "user",
            "email": "user@constitutionia.gn",
            "full_name": "Utilisateur Test",
            "hashed_password": get_password_hash("user123"),
            "is_superuser": False
        }
    ]
    
    for data in users_data:
        user = User(**data)
        db.add(user)
    
    db.commit()
    print(f"Ajouté {len(users_data)} utilisateurs de test")
    db.close()

def main():
    """Fonction principale"""
    print("Création des tables...")
    create_tables()
    
    print("Ajout des constitutions de test...")
    seed_constitutions()
    
    print("Ajout des utilisateurs de test...")
    seed_users()
    
    print("✅ Données de test ajoutées avec succès!")
    print("\nComptes de test créés:")
    print("- Username: admin, Password: admin123")
    print("- Username: user, Password: user123")

if __name__ == "__main__":
    main() 