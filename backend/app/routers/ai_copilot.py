from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.schemas.constitution import Constitution
from app.models.constitution import Constitution as ConstitutionModel
from app.services.ai_service import AIService
from app.services.pdf_analyzer import PDFAnalyzer
import openai
from app.core.config import settings
from pathlib import Path

router = APIRouter()

class AIQuery(BaseModel):
    query: str
    context: Optional[str] = None
    max_results: int = 5

class AIResponse(BaseModel):
    answer: str
    sources: List[Constitution]
    confidence: float
    suggestions: List[str]

class PDFChatRequest(BaseModel):
    question: str
    filename: str
    context: Optional[str] = None

class PDFChatResponse(BaseModel):
    response: str
    filename: str

@router.post("/chat", response_model=AIResponse)
async def chat_with_ai(
    query: AIQuery,
    db: Session = Depends(get_db)
):
    """Chat avec le copilot IA pour la recherche de constitutions"""
    try:
        ai_service = AIService()
        
        # Recherche sémantique dans les constitutions
        relevant_constitutions = ai_service.search_constitutions(
            query.query, 
            db, 
            max_results=query.max_results
        )
        
        # Génération de la réponse IA
        response = ai_service.generate_response(
            query.query,
            relevant_constitutions,
            context=query.context
        )
        
        return AIResponse(
            answer=response["answer"],
            sources=relevant_constitutions,
            confidence=response["confidence"],
            suggestions=response["suggestions"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

@router.post("/search/semantic", response_model=List[Constitution])
async def semantic_search(
    query: str,
    max_results: int = 10,
    db: Session = Depends(get_db)
):
    """Recherche sémantique dans les constitutions"""
    try:
        ai_service = AIService()
        results = ai_service.search_constitutions(query, db, max_results)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")

@router.get("/suggestions")
async def get_ai_suggestions():
    """Obtenir des suggestions de questions pour l'IA"""
    suggestions = [
        "Quels sont les droits fondamentaux garantis par la constitution ?",
        "Comment est organisé le pouvoir exécutif ?",
        "Quelles sont les procédures de révision constitutionnelle ?",
        "Comment sont protégés les droits des citoyens ?",
        "Quelle est la structure du pouvoir judiciaire ?",
        "Comment fonctionne le système électoral ?",
        "Quels sont les principes de la démocratie ?",
        "Comment est organisée l'administration publique ?"
    ]
    return {"suggestions": suggestions}

@router.post("/analyze")
async def analyze_constitution(
    constitution_id: int,
    analysis_type: str = "general",
    db: Session = Depends(get_db)
):
    """Analyser une constitution spécifique avec l'IA"""
    constitution = db.query(ConstitutionModel).filter(
        ConstitutionModel.id == constitution_id,
        ConstitutionModel.is_active == True
    ).first()
    
    if not constitution:
        raise HTTPException(status_code=404, detail="Constitution non trouvée")
    
    try:
        ai_service = AIService()
        analysis = ai_service.analyze_constitution(constitution, analysis_type)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

@router.post("/chat/pdf", response_model=PDFChatResponse)
async def chat_with_pdf(
    request: PDFChatRequest
):
    """Chat avec l'IA sur un fichier PDF spécifique"""
    try:
        # Vérifier que le fichier existe
        file_path = Path("Fichier") / request.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier PDF non trouvé")
        
        # Initialiser l'analyseur PDF
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY non configurée")
        
        pdf_analyzer = PDFAnalyzer(openai_api_key)
        
        # Extraire le texte du PDF
        pdf_text = pdf_analyzer.extract_text_from_pdf(str(file_path))
        if not pdf_text:
            raise HTTPException(status_code=500, detail="Impossible d'extraire le texte du PDF")
        
        # Limiter le texte pour éviter les tokens excessifs
        max_chars = 4000
        if len(pdf_text) > max_chars:
            pdf_text = pdf_text[:max_chars] + "..."
        
        # Créer le prompt pour l'IA
        prompt = f"""
        Tu es un assistant spécialisé dans l'analyse des constitutions et documents juridiques.
        
        Contexte du document: {request.context or 'Constitution de la Guinée'}
        Nom du fichier: {request.filename}
        
        Contenu du document:
        {pdf_text}
        
        Question de l'utilisateur: {request.question}
        
        Réponds de manière claire, précise et structurée en français. 
        Cite des passages spécifiques du document quand c'est pertinent.
        Si la question n'est pas directement liée au contenu du document, 
        indique-le poliment et propose une réponse basée sur tes connaissances générales.
        
        Réponse:
        """
        
        # Appeler l'API OpenAI
        response = openai.ChatCompletion.create(
            api_key=openai_api_key,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant juridique spécialisé dans l'analyse des constitutions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        return PDFChatResponse(
            response=ai_response,
            filename=request.filename
        )
        
    except Exception as e:
        print(f"Erreur lors du chat PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chat avec le PDF: {str(e)}") 