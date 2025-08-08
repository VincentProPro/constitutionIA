from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.schemas.constitution import Constitution
from app.models.constitution import Constitution as ConstitutionModel
from app.services.optimized_ai_service import get_optimized_ai_service
from app.services.pdf_analyzer import PDFAnalyzer
from app.services.monitoring_service import monitoring_service
import openai
from app.core.config import settings
from pathlib import Path

router = APIRouter()

class AIQuery(BaseModel):
    query: str
    context: Optional[str] = None
    max_results: int = 5
    user_id: Optional[str] = "default"  # Ajout de l'user_id
    session_id: Optional[str] = None  # Ajout du session_id pour les guests

class AIResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    suggestions: List[str]
    search_time: Optional[float] = None
    method: Optional[str] = None

class PDFChatRequest(BaseModel):
    question: str
    filename: str
    context: Optional[str] = None

class PDFChatResponse(BaseModel):
    response: str
    filename: str
    confidence: float

class SearchResult(BaseModel):
    constitution: Constitution
    relevance_score: float
    matched_chunk: str

class EnhancedSearchResponse(BaseModel):
    results: List[SearchResult]
    total_found: int
    search_time: float
    query: str

@router.post("/chat", response_model=AIResponse)
async def chat_with_ai(
    query: AIQuery,
    db: Session = Depends(get_db)
):
    """Chat avec le copilot IA pour la recherche de constitutions"""
    import time
    start_time = time.time()
    
    try:
        ai_service = get_optimized_ai_service()
        
        # Récupérer les constitutions
        constitutions = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True).all()
        
        search_time = time.time() - start_time
        
        # Génération de la réponse IA avec le service optimisé
        response = ai_service.generate_response(
            query.query,
            constitutions,
            context=query.context,
            user_id=query.user_id,  # Ajout de l'user_id
            session_id=query.session_id  # Ajout du session_id
        )
        
        # Convertir les résultats en format attendu
        sources = []
        if response.get("sources"):
            for source in response["sources"]:
                if isinstance(source, dict):
                    sources.append(source)
                else:
                    # Si c'est un tuple (constitution, score, chunk)
                    sources.append({
                        "title": source[0].title if hasattr(source[0], 'title') else "Document",
                        "content": source[2][:200] + "..." if len(source) > 2 else ""
                    })
        
        return AIResponse(
            answer=response["answer"],
            sources=sources,
            confidence=response["confidence"],
            suggestions=response["suggestions"],
            search_time=search_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

@router.post("/search/semantic", response_model=EnhancedSearchResponse)
async def semantic_search(
    query: str,
    max_results: int = 10,
    db: Session = Depends(get_db)
):
    """Recherche sémantique améliorée dans les constitutions"""
    import time
    start_time = time.time()
    
    try:
        ai_service = get_optimized_ai_service()
        
        # Utiliser la recherche optimisée
        constitutions = db.query(ConstitutionModel).filter(ConstitutionModel.is_active == True).all()
        
        # Recherche optimisée avec cache
        response = ai_service.generate_response(query, constitutions)
        
        # Convertir en format de recherche
        if response["confidence"] > 0.3:
            return EnhancedSearchResponse(
                results=[SearchResult(
                    constitution=ConstitutionModel(title="Document optimisé"),
                    relevance_score=response["confidence"],
                    matched_chunk=response["answer"][:200]
                )],
                total_found=1,
                search_time=response["search_time"],
                query=query
            )
        
        # Fallback avec recherche par mots-clés
        keyword_results = ai_service._fast_keyword_search(query, constitutions)
        
        # Combiner les résultats
        combined_results = {}
        
        for constitution, score, chunk in semantic_results:
            combined_results[constitution.id] = {
                'constitution': constitution,
                'semantic_score': score,
                'keyword_score': 0,
                'chunk': chunk
            }
        
        for constitution, score, chunk in keyword_results:
            if constitution.id in combined_results:
                combined_results[constitution.id]['keyword_score'] = score
            else:
                combined_results[constitution.id] = {
                    'constitution': constitution,
                    'semantic_score': 0,
                    'keyword_score': score,
                    'chunk': chunk
                }
        
        # Calculer le score final
        final_results = []
        for result in combined_results.values():
            final_score = (result['semantic_score'] * 0.7 + result['keyword_score'] * 0.3)
            final_results.append(SearchResult(
                constitution=result['constitution'],
                relevance_score=final_score,
                matched_chunk=result['chunk']
            ))
        
        # Trier par score
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        search_time = time.time() - start_time
        
        return EnhancedSearchResponse(
            results=final_results[:max_results],
            total_found=len(final_results),
            search_time=search_time,
            query=query
        )
        
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
        "Comment est organisée l'administration publique ?",
        "Quelles sont les libertés individuelles ?",
        "Comment fonctionne le parlement ?",
        "Quels sont les symboles de la République ?",
        "Comment est organisé le gouvernement ?"
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
        ai_service = get_optimized_ai_service()
        # Pour l'analyse, utiliser une approche simplifiée
        analysis = {
            "title": constitution.title,
            "year": constitution.year,
            "content_length": len(constitution.content) if constitution.content else 0,
            "word_count": len(constitution.content.split()) if constitution.content else 0,
            "analysis_type": analysis_type,
            "status": "analyzed"
        }
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

@router.post("/chat/pdf", response_model=PDFChatResponse)
async def chat_with_pdf(
    request: PDFChatRequest
):
    """Chat avec l'IA sur un fichier PDF spécifique - Version améliorée"""
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
        
        # Extraire le texte du PDF avec améliorations
        pdf_text = pdf_analyzer.extract_text_from_pdf(str(file_path))
        if not pdf_text:
            raise HTTPException(status_code=500, detail="Impossible d'extraire le texte du PDF")
        
        # Extraire la structure du document
        structured_content = pdf_analyzer.extract_structured_content(str(file_path))
        
        # Préparer le contexte enrichi
        context_info = f"""
        Nom du fichier: {request.filename}
        Nombre d'articles trouvés: {structured_content.get('total_articles', 0)}
        Longueur du document: {structured_content.get('text_length', 0)} caractères
        """
        
        if 'sections' in structured_content:
            context_info += f"\nSections identifiées: {len(structured_content['sections'])}"
        
        # Limiter le texte pour éviter les tokens excessifs mais garder plus de contexte
        max_chars = 8000  # Augmenter la limite
        if len(pdf_text) > max_chars:
            # Essayer de garder le début et la fin du document
            half_chars = max_chars // 2
            pdf_text = pdf_text[:half_chars] + "\n\n... [CONTENU TRONQUÉ] ...\n\n" + pdf_text[-half_chars:]
        
        # Créer le prompt amélioré pour l'IA
        system_prompt = """Tu es un assistant juridique spécialisé dans l'analyse des constitutions et documents juridiques.

INSTRUCTIONS IMPORTANTES:
1. Réponds UNIQUEMENT en te basant sur les informations fournies dans le document
2. Cite spécifiquement les articles ou passages pertinents
3. Structure ta réponse de manière claire avec des points
4. Si l'information n'est pas dans le document, dis-le clairement
5. Utilise un langage juridique approprié mais accessible
6. Réponds en français"""

        user_prompt = f"""Question: {request.question}

Contexte du document:
{context_info}

Contenu du document:
{pdf_text}

Réponds de manière structurée en citant les passages pertinents. Si l'information n'est pas dans le document, indique-le clairement."""

        # Appeler l'API OpenAI
        response = openai.ChatCompletion.create(
            api_key=openai_api_key,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,
            temperature=0.3  # Plus déterministe
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Calculer un score de confiance basé sur la présence d'informations dans la réponse
        confidence = 0.8  # Score de base
        if "n'est pas dans le document" in ai_response.lower() or "pas d'information" in ai_response.lower():
            confidence = 0.3
        elif any(word in ai_response.lower() for word in ["article", "section", "constitution"]):
            confidence = 0.9
        
        return PDFChatResponse(
            response=ai_response,
            filename=request.filename,
            confidence=confidence
        )
        
    except Exception as e:
        print(f"Erreur lors du chat PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chat avec le PDF: {str(e)}")

@router.get("/status")
async def get_ai_system_status():
    """Obtenir le statut du système IA optimisé"""
    try:
        ai_service = get_optimized_ai_service()
        status = ai_service.get_system_status()
        cache_stats = ai_service.get_cache_stats()
        
        return {
            "system_status": status,
            "cache_stats": cache_stats,
            "message": "Statut du système IA optimisé récupéré avec succès",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du statut: {str(e)}")

@router.post("/cache/clear")
async def clear_ai_cache():
    """Vider le cache du système IA"""
    try:
        ai_service = get_optimized_ai_service()
        ai_service.clear_cache()
        
        return {
            "message": "Cache vidé avec succès",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du vidage du cache: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats():
    """Obtenir les statistiques du cache"""
    try:
        ai_service = get_optimized_ai_service()
        cache_stats = ai_service.get_cache_stats()
        
        return {
            "cache_stats": cache_stats,
            "message": "Statistiques du cache récupérées avec succès",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des stats cache: {str(e)}")

@router.get("/metrics")
async def get_ai_metrics():
    """Obtenir les métriques de performance du système IA"""
    try:
        metrics = monitoring_service.get_performance_metrics()
        return {
            "metrics": metrics,
            "message": "Métriques récupérées avec succès",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des métriques: {str(e)}")

@router.get("/metrics/recent")
async def get_recent_metrics(hours: int = 24):
    """Obtenir les métriques récentes"""
    try:
        recent_metrics = monitoring_service.get_recent_activity(hours)
        return {
            "recent_metrics": recent_metrics,
            "message": "Métriques récentes récupérées avec succès",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des métriques récentes: {str(e)}")

@router.post("/metrics/export")
async def export_metrics():
    """Exporter les métriques vers un fichier JSON"""
    try:
        filepath = monitoring_service.export_metrics()
        if filepath:
            return {
                "filepath": filepath,
                "message": "Métriques exportées avec succès",
                "success": True
            }
        else:
            return {
                "message": "Échec de l'export des métriques",
                "success": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export des métriques: {str(e)}")

@router.post("/metrics/reset")
async def reset_metrics():
    """Réinitialiser toutes les métriques"""
    try:
        monitoring_service.reset_metrics()
        return {
            "message": "Métriques réinitialisées avec succès",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation des métriques: {str(e)}")

@router.post("/feedback")
async def submit_feedback(query_id: str, rating: int, feedback: str = ""):
    """Soumettre un feedback utilisateur"""
    try:
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Le rating doit être entre 1 et 5")
        
        monitoring_service.track_user_feedback(query_id, rating, feedback)
        return {
            "message": "Feedback enregistré avec succès",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement du feedback: {str(e)}")

@router.get("/pdf/structure/{filename}")
async def get_pdf_structure(filename: str):
    """Obtenir la structure d'un fichier PDF"""
    try:
        file_path = Path("Fichier") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier PDF non trouvé")
        
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY non configurée")
        
        pdf_analyzer = PDFAnalyzer(openai_api_key)
        structured_content = pdf_analyzer.extract_structured_content(str(file_path))
        
        return {
            "filename": filename,
            "structure": structured_content,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse de la structure: {str(e)}") 

@router.post("/session/create")
async def create_guest_session():
    """Crée une nouvelle session pour un utilisateur guest"""
    import uuid
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "expires_in": 3600,  # 1 heure
        "message": "Session guest créée avec succès"
    }

@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Récupère l'historique de conversation d'une session"""
    ai_service = get_optimized_ai_service()
    user_id = f"guest_{session_id}"
    history = ai_service._get_conversation_history(user_id)
    
    return {
        "session_id": session_id,
        "history": history,
        "message_count": len(history)
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Supprime une session et son historique"""
    ai_service = get_optimized_ai_service()
    user_id = f"guest_{session_id}"
    
    if user_id in ai_service.conversation_memory:
        del ai_service.conversation_memory[user_id]
    
    if session_id in ai_service.session_timestamps:
        del ai_service.session_timestamps[session_id]
    
    return {
        "session_id": session_id,
        "message": "Session supprimée avec succès"
    }

@router.get("/sessions/stats")
async def get_sessions_stats():
    """Récupère les statistiques des sessions"""
    ai_service = get_optimized_ai_service()
    
    auth_users = len([uid for uid in ai_service.conversation_memory.keys() if uid.startswith("auth_")])
    guest_users = len([uid for uid in ai_service.conversation_memory.keys() if uid.startswith("guest_")])
    temp_users = len([uid for uid in ai_service.conversation_memory.keys() if uid.startswith("temp_")])
    
    return {
        "total_sessions": len(ai_service.conversation_memory),
        "authenticated_users": auth_users,
        "guest_users": guest_users,
        "temporary_users": temp_users,
        "active_sessions": len(ai_service.session_timestamps)
    } 

@router.post("/init-rag")
async def initialize_rag():
    """Force l'initialisation du système RAG"""
    try:
        ai_service = get_optimized_ai_service()
        
        # Forcer l'initialisation
        success = ai_service._initialize_rag_lazy()
        
        if success:
            return {
                "success": True,
                "message": "Système RAG initialisé avec succès",
                "status": ai_service.get_system_status()
            }
        else:
            return {
                "success": False,
                "message": "Échec de l'initialisation du RAG",
                "status": ai_service.get_system_status()
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de l'initialisation: {str(e)}",
            "error": str(e)
        } 