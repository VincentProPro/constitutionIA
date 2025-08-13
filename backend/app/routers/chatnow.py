"""
Routeur spécialisé pour ChatNow - Interface de conversation indépendante
Module totalement autonome qui fonctionne directement avec le fichier PDF
"""

import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.schemas.chatnow import (
    ChatNowRequest,
    ChatNowResponse,
    ChatNowErrorResponse
)
from app.services.chatnow_service import initialize_chatnow_service
from app.services.constitution_parser import ConstitutionParser
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatnow", tags=["ChatNow"])

# Chemin vers le fichier TXT de constitution
CONSTITUTION_TXT_PATH = "Correction/02.txt"

def extract_txt_content(file_path: str) -> str:
    """
    Extrait le contenu textuel du fichier TXT
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier TXT non trouvé: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
            return text_content.strip()
            
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier TXT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la lecture du fichier TXT: {str(e)}"
        )

def get_constitution_context() -> str:
    """
    Récupère le contexte de la constitution depuis le fichier TXT
    """
    try:
        txt_content = extract_txt_content(CONSTITUTION_TXT_PATH)
        
        # Limiter le contenu pour éviter un contexte trop long
        max_length = 12000  # Limite plus élevée pour le texte brut
        if len(txt_content) > max_length:
            txt_content = txt_content[:max_length] + "...\n\n[Contenu tronqué pour optimiser les performances]"
        
        return f"Constitution de la Guinée (fichier: 02.txt)\n\nContenu extrait:\n{txt_content}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contexte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du contenu de la constitution"
        )

@router.get("/health")
async def chatnow_health_check():
    """
    Endpoint de santé pour ChatNow
    """
    try:
        # Vérifier que le fichier TXT existe
        if not os.path.exists(CONSTITUTION_TXT_PATH):
            return {
                "status": "error",
                "service": "ChatNow",
                "timestamp": datetime.now(),
                "version": "1.0.0",
                "error": f"Fichier TXT non trouvé: {CONSTITUTION_TXT_PATH}"
            }
        
        return {
            "status": "healthy",
            "service": "ChatNow",
            "timestamp": datetime.now(),
            "version": "1.0.0",
            "txt_file": CONSTITUTION_TXT_PATH,
            "txt_exists": True
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "ChatNow",
            "timestamp": datetime.now(),
            "version": "1.0.0",
            "error": str(e)
        }

@router.post("/chat", response_model=ChatNowResponse)
async def chatnow_conversation(request: ChatNowRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal de conversation pour ChatNow optimisé
    Avec cache, recherche intelligente et base de données
    """
    try:
        # Valider la question
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La question ne peut pas être vide"
            )
        
        # Initialiser le service ChatNow avec la base de données
        initialize_chatnow_service(db)
        from app.services.chatnow_service import chatnow_service
        
        # Vérifier que le fichier TXT existe
        if not os.path.exists(CONSTITUTION_TXT_PATH):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fichier de constitution non trouvé: {CONSTITUTION_TXT_PATH}"
            )
        
        # Générer la réponse avec le service optimisé
        response_text = chatnow_service.create_chat_response(
            question=request.question,
            chat_history=request.chat_history if hasattr(request, 'chat_history') else None,
            user_id=request.user_id
        )
        
        # Générer des suggestions pour la suite
        suggestions = chatnow_service.get_conversation_suggestions("Constitution de la Guinée")
        
        logger.info(f"ChatNow optimisé - Question: '{request.question[:50]}...' - Fichier: {CONSTITUTION_TXT_PATH}")
        
        return ChatNowResponse(
            response=response_text,
            constitution_title="Constitution de la Guinée (02.txt) - Optimisé",
            timestamp=datetime.now(),
            suggestions=suggestions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la conversation ChatNow optimisé: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération de la réponse"
        )

@router.post("/init-database")
async def initialize_constitution_database(db: Session = Depends(get_db)):
    """
    Endpoint pour initialiser la base de données de constitution
    Parse le fichier 02.txt et stocke les données structurées
    """
    try:
        from app.services.constitution_parser import ConstitutionParser
        
        # Vérifier que le fichier TXT existe
        if not os.path.exists(CONSTITUTION_TXT_PATH):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fichier de constitution non trouvé: {CONSTITUTION_TXT_PATH}"
            )
        
        # Créer le parser
        parser = ConstitutionParser(db)
        
        # Parser le fichier
        logger.info("Début du parsing de la constitution...")
        parsed_data = parser.parse_constitution_file(CONSTITUTION_TXT_PATH)
        
        # Sauvegarder dans la base de données
        success = parser.save_to_database(parsed_data)
        
        if success:
            return {
                "status": "success",
                "message": "Base de données de constitution initialisée avec succès",
                "statistics": {
                    "articles": parsed_data['total_articles'],
                    "sections": parsed_data['total_sections'],
                    "keywords": len(parsed_data['keywords'])
                },
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la sauvegarde des données"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'initialisation de la base de données"
        )

@router.get("/info")
async def get_chatnow_info():
    """
    Endpoint pour obtenir les informations sur ChatNow
    """
    try:
        txt_exists = os.path.exists(CONSTITUTION_TXT_PATH)
        
        info = {
            "service": "ChatNow",
            "description": "Module de conversation IA indépendant pour la constitution",
            "txt_file": CONSTITUTION_TXT_PATH,
            "txt_exists": txt_exists,
            "timestamp": datetime.now(),
            "version": "1.0.0"
        }
        
        if txt_exists:
            # Obtenir la taille du fichier
            file_size = os.path.getsize(CONSTITUTION_TXT_PATH)
            info["txt_size_bytes"] = file_size
            info["txt_size_kb"] = round(file_size / 1024, 2)
        
        return info
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations ChatNow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des informations"
        )
