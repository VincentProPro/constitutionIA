"""
Schémas Pydantic pour l'API ChatNow
Module totalement indépendant
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ChatNowRequest(BaseModel):
    """Schéma pour les requêtes de chat ChatNow optimisé"""
    question: str
    user_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class ChatNowResponse(BaseModel):
    """Schéma pour les réponses de chat ChatNow"""
    response: str
    constitution_title: str
    timestamp: datetime
    suggestions: List[str]

class ChatNowErrorResponse(BaseModel):
    """Schéma pour les erreurs ChatNow"""
    error: str
    detail: str
    timestamp: datetime
