import openai
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.constitution import Constitution
from app.core.config import settings
# from sentence_transformers import SentenceTransformer
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity

class AIService:
    def __init__(self):
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
    
    def search_constitutions(self, query: str, db: Session, max_results: int = 5) -> List[Constitution]:
        """Recherche simple dans les constitutions"""
        # Récupérer toutes les constitutions
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        
        if not constitutions:
            return []
        
        # Recherche simple par mots-clés
        query_lower = query.lower()
        results = []
        
        for constitution in constitutions:
            score = 0
            title_lower = constitution.title.lower()
            content_lower = constitution.content.lower()
            
            # Score basé sur la présence de mots-clés
            if query_lower in title_lower:
                score += 3
            if query_lower in content_lower:
                score += 1
            
            # Score basé sur les mots individuels
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Ignorer les mots trop courts
                    if word in title_lower:
                        score += 2
                    if word in content_lower:
                        score += 0.5
            
            if score > 0:
                results.append((constitution, score))
        
        # Trier par score et retourner les meilleurs résultats
        results.sort(key=lambda x: x[1], reverse=True)
        return [constitution for constitution, score in results[:max_results]]
    
    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Générer une réponse IA basée sur les constitutions trouvées"""
        if not constitutions:
            return {
                "answer": "Je n'ai pas trouvé d'informations pertinentes dans les constitutions disponibles.",
                "confidence": 0.0,
                "suggestions": []
            }
        
        # Préparer le contexte
        context_text = ""
        for constitution in constitutions:
            context_text += f"Constitution {constitution.year} ({constitution.title}):\n"
            context_text += f"{constitution.content[:2000]}...\n\n"
        
        if context:
            context_text = f"Contexte: {context}\n\n" + context_text
        
        # Générer la réponse avec OpenAI si disponible
        if settings.OPENAI_API_KEY:
            try:
                response = openai.ChatCompletion.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un assistant spécialisé dans l'analyse des constitutions. Réponds de manière claire et précise en te basant uniquement sur les informations fournies."
                        },
                        {
                            "role": "user",
                            "content": f"Question: {query}\n\nContexte des constitutions:\n{context_text}"
                        }
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content
                confidence = 0.8  # Confiance élevée pour OpenAI
                
            except Exception as e:
                answer = self._generate_simple_response(query, constitutions)
                confidence = 0.6
        else:
            answer = self._generate_simple_response(query, constitutions)
            confidence = 0.6
        
        # Générer des suggestions
        suggestions = self._generate_suggestions(query)
        
        return {
            "answer": answer,
            "confidence": confidence,
            "suggestions": suggestions
        }
    
    def _generate_simple_response(self, query: str, constitutions: List[Constitution]) -> str:
        """Générer une réponse simple sans OpenAI"""
        response = f"Basé sur l'analyse des constitutions disponibles, voici ce que j'ai trouvé concernant votre question : '{query}'\n\n"
        
        for constitution in constitutions:
            response += f"Dans la Constitution de {constitution.year} :\n"
            response += f"- {constitution.title}\n"
            if constitution.summary:
                response += f"- Résumé : {constitution.summary[:200]}...\n"
            response += "\n"
        
        return response
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Générer des suggestions de questions liées"""
        suggestions = [
            "Pouvez-vous me donner plus de détails sur ce sujet ?",
            "Y a-t-il des différences entre les différentes versions de la constitution ?",
            "Comment cette disposition a-t-elle évolué au fil du temps ?",
            "Quels sont les droits et obligations associés ?"
        ]
        return suggestions
    
    def analyze_constitution(self, constitution: Constitution, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyser une constitution spécifique"""
        analysis = {
            "constitution_id": constitution.id,
            "title": constitution.title,
            "year": constitution.year,
            "analysis_type": analysis_type,
            "summary": constitution.summary or "Aucun résumé disponible",
            "key_points": [],
            "recommendations": []
        }
        
        # Analyse basique du contenu
        content = constitution.content.lower()
        
        # Détecter les sections importantes
        if "droits" in content or "libertés" in content:
            analysis["key_points"].append("Droits et libertés fondamentaux")
        
        if "pouvoir" in content and "exécutif" in content:
            analysis["key_points"].append("Organisation du pouvoir exécutif")
        
        if "judiciaire" in content:
            analysis["key_points"].append("Structure du pouvoir judiciaire")
        
        if "élection" in content or "vote" in content:
            analysis["key_points"].append("Système électoral")
        
        # Recommandations
        if not analysis["key_points"]:
            analysis["recommendations"].append("Considérer une analyse plus détaillée du contenu")
        
        return analysis 