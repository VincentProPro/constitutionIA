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
from openai import OpenAI

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

@router.post("/refresh-vector-db")
async def refresh_vector_database():
    """Rafraîchit la base vectorielle avec les nouvelles données"""
    try:
        ai_service = get_optimized_ai_service()
        success = ai_service.refresh_vector_db()
        
        if success:
            return {
                "status": "success",
                "message": "Base vectorielle rafraîchie avec succès",
                "timestamp": time.time()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Échec du rafraîchissement de la base vectorielle"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du rafraîchissement: {str(e)}"
        )

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
    request: PDFChatRequest,
    db: Session = Depends(get_db)
):
    """Chat avec l'IA sur un fichier PDF spécifique - Utilise les données de la base"""
    try:
        # Trouver la constitution correspondante au fichier (active uniquement)
        constitution = db.query(ConstitutionModel).filter(
            ConstitutionModel.filename == request.filename,
            ConstitutionModel.is_active == True
        ).first()
        
        if not constitution:
            raise HTTPException(
                status_code=404, 
                detail=f"Constitution '{request.filename}' non trouvée ou supprimée. Veuillez sélectionner une constitution active."
            )
        
        # Utiliser le service IA optimisé avec les données de la base
        ai_service = get_optimized_ai_service()
        
        # Récupérer les articles de cette constitution
        from app.models.pdf_import import Article
        articles = db.query(Article).filter(Article.constitution_id == constitution.id).all()
        
        if not articles:
            raise HTTPException(status_code=400, detail="Aucun article trouvé pour cette constitution")
        
        # Créer un contexte spécifique à cette constitution
        context_parts = []
        context_parts.append(f"CONSTITUTION: {constitution.title}")
        context_parts.append("")
        context_parts.append("IMPORTANT: Utilisez uniquement le titre de la constitution, jamais le nom du fichier technique.")
        context_parts.append("")
        
        # Rechercher les articles pertinents pour la question
        import re
        def tokenize(text: str):
            return re.findall(r"\w+", text.lower())
        
        # Stopwords FR minimales
        stop = {"le","la","les","de","des","du","un","une","et","en","d","l","au","aux","que","qui","dans","sur","pour","par","auprès","avec","sans","ne","pas","est","sont","ou","à","au","aux","se","ce","cet","cette"}
        question_tokens = [t for t in tokenize(request.question) if t not in stop]
        
        # Scorer les articles par pertinence
        scored_articles = []
        for article in articles:
            content_tokens = tokenize(article.content)
            score = sum(content_tokens.count(qt) for qt in question_tokens)
            
            # Bonus pour les mots-clés spécifiques
            if "mandat" in question_tokens and "mandat" in content_tokens:
                score += 5
            if "président" in question_tokens and "président" in content_tokens:
                score += 5
            if "durée" in question_tokens and any(word in content_tokens for word in ["ans", "années", "durée"]):
                score += 3
            
            scored_articles.append((score, article))
        
        # Trier par score et prendre les plus pertinents
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        relevant_articles = [article for score, article in scored_articles[:5] if score > 0]
        
        # Si aucun article pertinent, prendre les premiers articles
        if not relevant_articles:
            relevant_articles = articles[:3]
        
        # Construire le contexte avec les articles pertinents (limiter la taille)
        for article in relevant_articles:
            # Limiter le contenu de chaque article pour éviter l'erreur de contexte
            content = article.content[:500] + "..." if len(article.content) > 500 else article.content
            context_parts.append(f"Article {article.article_number}: {content}")
        
        context = "\n\n".join(context_parts)
        
        # Créer un prompt spécifique à cette constitution
        system_prompt = f"""Tu es un assistant spécialisé dans l'analyse de la constitution: {constitution.title}

RÈGLES STRICTES:
1) Réponds UNIQUEMENT à partir des articles de cette constitution spécifique
2) Cite impérativement l'article exact avec son numéro
3) Si l'information n'est pas dans cette constitution, réponds: "Cette information n'est pas présente dans cette constitution"
4) Réponds en français de manière claire et structurée
5) Indique toujours la source: "Selon l'article X..."
6) N'utilise JAMAIS le nom du fichier technique ni le titre de la constitution dans la réponse
7) Cite seulement le numéro d'article, pas le nom du document
"""

        user_prompt = f"""Question: {request.question}

Contexte de la constitution {constitution.title}:
{context}

Réponds en te basant uniquement sur cette constitution spécifique.
IMPORTANT: Cite seulement le numéro d'article (ex: "Selon l'article 44..."), sans mentionner le nom du fichier ni le titre de la constitution."""

        # Utiliser directement OpenAI pour une réponse précise
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Calculer la confiance
            confidence = 0.8
            if "n'est pas présente" in ai_response.lower():
                confidence = 0.3
            elif "article" in ai_response.lower() and constitution.title.lower() in ai_response.lower():
                confidence = 0.9
            
            return PDFChatResponse(
                response=ai_response,
                filename=request.filename,
                confidence=confidence
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur OpenAI: {str(e)}")
        
    except HTTPException:
        # Relancer les erreurs HTTP explicites telles quelles
        raise
    except Exception as e:
        print(f"Erreur lors du chat PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chat avec le PDF: {str(e)}")

@router.post("/chat/articles", response_model=PDFChatResponse)
async def chat_with_articles(
    request: PDFChatRequest,
    db: Session = Depends(get_db)
):
    """Chat avec l'IA en utilisant les articles stockés en base de données"""
    try:
        # Rechercher la constitution par nom de fichier
        constitution = db.query(ConstitutionModel).filter(
            ConstitutionModel.filename == request.filename,
            ConstitutionModel.is_active == True
        ).first()
        
        if not constitution:
            raise HTTPException(status_code=404, detail="Constitution non trouvée en base de données")
        
        # Récupérer tous les articles de cette constitution
        from app.models.pdf_import import Article
        articles = db.query(Article).filter(
            Article.constitution_id == constitution.id
        ).order_by(Article.article_number).all()
        
        if not articles:
            raise HTTPException(status_code=404, detail="Aucun article trouvé pour cette constitution")
        
        # Préparer le contexte à partir des articles
        articles_context = []
        for article in articles:
            article_text = f"Article {article.article_number}"
            if article.title:
                article_text += f" - {article.title}"
            article_text += f": {article.content}"
            articles_context.append(article_text)
        
        # Rechercher les articles les plus pertinents pour la question
        import re
        def tokenize(text: str):
            return re.findall(r"\w+", text.lower())
        
        # Stopwords FR minimales
        stop = {"le","la","les","de","des","du","un","une","et","en","d","l","au","aux","que","qui","dans","sur","pour","par","auprès","avec","sans","ne","pas","est","sont","ou","à","au","aux","se","ce","cet","cette"}
        question_tokens = [t for t in tokenize(request.question) if t not in stop]
        
        # Scorer les articles par pertinence
        scored_articles = []
        for article in articles:
            content_tokens = tokenize(article.content)
            score = sum(content_tokens.count(qt) for qt in question_tokens)
            
            # Bonus pour les mots-clés importants
            if any(keyword in article.content.lower() for keyword in ["droit", "liberté", "pouvoir", "élection", "gouvernement"]):
                score += 1
            
            scored_articles.append((score, article))
        
        # Trier par score et prendre les plus pertinents
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        relevant_articles = [article for score, article in scored_articles[:10] if score > 0]
        
        # Si aucun article pertinent, prendre les premiers articles
        if not relevant_articles:
            relevant_articles = [article for score, article in scored_articles[:5]]
        
        # Construire le contexte à partir des articles pertinents
        context_chunks = []
        total_chars = 0
        max_context_chars = 8000
        
        for article in relevant_articles:
            article_text = f"Article {article.article_number}"
            if article.title:
                article_text += f" - {article.title}"
            article_text += f": {article.content}"
            
            if total_chars + len(article_text) <= max_context_chars:
                context_chunks.append(article_text)
                total_chars += len(article_text)
            else:
                break
        
        articles_context_for_llm = "\n\n".join(context_chunks)
        
        # Informations sur la constitution
        context_info = f"""
        Constitution: {constitution.title}
        Fichier source: {constitution.filename}
        Nombre total d'articles: {len(articles)}
        Articles pertinents utilisés: {len(relevant_articles)}
        """
        
        # Créer le prompt pour l'IA
        system_prompt = """Tu es un assistant juridique spécialisé dans les constitutions.

RÈGLES STRICTES:
1) Réponds UNIQUEMENT à partir des articles fournis (contexte). N'invente pas.
2) Cite impérativement les articles entre « guillemets » et indique le numéro d'article.
3) Structure la réponse en points clairs et courts.
4) Si l'information n'est pas présente dans les articles, réponds explicitement: "Je ne trouve pas cette information dans les articles de cette constitution."
5) Réponds en français.
6) Utilise les articles stockés en base de données, pas l'extraction directe du PDF.
"""

        user_prompt = f"""Question: {request.question}

Informations sur la constitution:
{context_info}

Articles de la constitution (stockés en base de données):
{articles_context_for_llm}

Réponds de manière structurée en citant les articles pertinents. Si l'information n'est pas dans les articles, indique-le clairement."""

        # Appeler l'API OpenAI
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY non configurée")
        
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Calculer un score de confiance basé sur la pertinence des articles
        if relevant_articles:
            avg_score = sum(score for score, _ in scored_articles[:len(relevant_articles)]) / len(relevant_articles)
            confidence = min(0.95, max(0.3, avg_score / 10))  # Normaliser entre 0.3 et 0.95
        else:
            confidence = 0.3
        
        return PDFChatResponse(
            response=ai_response,
            filename=request.filename,
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chat avec les articles: {str(e)}")

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