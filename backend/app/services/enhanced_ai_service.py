import os
import time
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.constitution import Constitution
import openai
from openai import OpenAI
import re

class EnhancedAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Configuration multi-niveaux
        self.search_levels = {
            "exact": {"max_results": 3, "threshold": 0.8},
            "semantic": {"max_results": 5, "threshold": 0.6},
            "fuzzy": {"max_results": 7, "threshold": 0.4},
            "general": {"max_results": 10, "threshold": 0.2}
        }
        
        # Types de questions
        self.question_types = {
            "identity": ["nom", "qui es-tu", "qui es tu", "ton nom", "appelle"],
            "politeness": ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye"],
            "constitutional": ["constitution", "article", "loi", "droit", "pouvoir"],
            "comparison": ["différence", "comparer", "versus", "contrairement"],
            "analysis": ["analyser", "expliquer", "comment", "pourquoi"],
            "specific": ["durée", "mandat", "élection", "vote"]
        }

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question"""
        query_lower = query.lower()
        
        for qtype, keywords in self.question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return qtype
        return "general"

    def _multi_level_search(self, query: str, constitutions: List[Constitution]) -> List[Tuple[Constitution, float, str]]:
        """Recherche multi-niveaux"""
        all_results = []
        
        # Niveau 1: Recherche exacte
        exact_results = self._keyword_search(query, constitutions, 3)
        all_results.extend(exact_results)
        
        # Niveau 2: Recherche floue si pas assez
        if len(all_results) < 3:
            fuzzy_results = self._fuzzy_search(query, constitutions, 5)
            all_results.extend(fuzzy_results)
        
        # Niveau 3: Recherche par concepts
        if len(all_results) < 2:
            concept_results = self._concept_search(query, constitutions, 5)
            all_results.extend(concept_results)
        
        # Dédupliquer et trier
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result[0].id, result[2][:100])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return sorted(unique_results, key=lambda x: x[1], reverse=True)[:10]

    def _keyword_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par mots-clés améliorée"""
        if not constitutions:
            return []
        
        results = []
        query_words = set(query.lower().split())
        
        for constitution in constitutions:
            if not constitution.content:
                continue
            
            chunks = self._chunk_text(constitution.content)
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                score = 0.0
                
                # Score pour correspondance exacte
                if query.lower() in chunk_lower:
                    score += 10.0
                
                # Score pour mots individuels
                chunk_words = set(chunk_lower.split())
                common_words = query_words.intersection(chunk_words)
                score += len(common_words) * 2.0
                
                # Bonus pour mots longs
                for word in common_words:
                    if len(word) > 6:
                        score += 1.0
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _fuzzy_search(self, query: str, constitutions: List[Constitution], max_results: int = 7) -> List[Tuple[Constitution, float, str]]:
        """Recherche floue"""
        if not constitutions:
            return []
        
        results = []
        query_words = query.lower().split()
        
        for constitution in constitutions:
            if not constitution.content:
                continue
            
            chunks = self._chunk_text(constitution.content)
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                score = 0.0
                
                for word in query_words:
                    if word in chunk_lower:
                        score += 2.0
                    elif word[:-1] in chunk_lower:
                        score += 1.5
                    elif word + 's' in chunk_lower:
                        score += 1.5
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _concept_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par concepts"""
        concept_mapping = {
            "mandat": ["durée", "période", "élection", "renouvellement"],
            "droit": ["liberté", "garantie", "protection", "exercice"],
            "pouvoir": ["exécutif", "législatif", "judiciaire", "autorité"]
        }
        
        results = []
        query_lower = query.lower()
        
        for constitution in constitutions:
            if not constitution.content:
                continue
            
            chunks = self._chunk_text(constitution.content)
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                score = 0.0
                
                for concept, related_terms in concept_mapping.items():
                    if concept in query_lower:
                        for term in related_terms:
                            if term in chunk_lower:
                                score += 1.0
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Divise le texte en chunks"""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size * 0.8:
                    end = start + last_space
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks

    def _prepare_context(self, search_results: List[Tuple[Constitution, float, str]]) -> str:
        """Prépare le contexte"""
        if not search_results:
            return ""
        
        context_parts = []
        for constitution, score, chunk in search_results[:5]:
            context_parts.append(f"📄 {constitution.title} (Score: {score:.2f}):\n{chunk}\n")
        
        return "\n".join(context_parts)

    def _generate_ai_response(self, query: str, context: str) -> str:
        """Génère une réponse avec OpenAI"""
        try:
            system_prompt = """Tu es ConstitutionIA, assistant spécialisé dans l'analyse des constitutions.

INSTRUCTIONS:
1. Réponds UNIQUEMENT basé sur le contexte fourni
2. Structure ta réponse clairement avec des points numérotés
3. Cite spécifiquement les articles pertinents
4. Utilise un langage juridique accessible
5. Si l'information n'est pas dans le contexte, dis-le clairement
6. Réponds en français de manière concise"""

            user_prompt = f"Question: {query}\n\nContexte:\n{context}\n\nRéponse:"

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"

    def _generate_fallback_response(self, query: str) -> str:
        """Réponse de secours avec GPT générique"""
        try:
            system_prompt = """Tu es ConstitutionIA. L'information demandée n'est pas dans les documents constitutionnels disponibles.

INSTRUCTIONS:
1. Explique poliment que l'information n'est pas disponible
2. Suggère des questions alternatives sur la constitution
3. Propose de reformuler la question
4. Reste professionnel et utile"""

            user_prompt = f"Question: {query}\n\nL'information n'est pas dans les documents constitutionnels."

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Je ne trouve pas cette information dans les documents disponibles. Pouvez-vous reformuler votre question ?"

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse avec système hybride"""
        start_time = time.time()
        
        try:
            question_type = self._detect_question_type(query)
            query_lower = query.lower().strip()
            
            # Réponses directes
            if question_type == "identity":
                return {
                    "answer": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions et documents juridiques.",
                    "confidence": 1.0,
                    "sources": [],
                    "search_time": time.time() - start_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                }
            
            if question_type == "politeness":
                if 'merci' in query_lower:
                    return {
                        "answer": "De rien ! Je suis là pour vous aider avec vos questions sur la constitution.",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                    }
                else:
                    return {
                        "answer": "Bonjour ! Comment puis-je vous aider avec la constitution ?",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                    }
            
            # Recherche multi-niveaux
            search_results = self._multi_level_search(query, constitutions)
            search_time = time.time() - start_time
            
            if not search_results:
                # Fallback avec GPT générique
                fallback_response = self._generate_fallback_response(query)
                return {
                    "answer": fallback_response,
                    "confidence": 0.1,
                    "sources": [],
                    "search_time": search_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                }
            
            # Préparation du contexte
            context_text = self._prepare_context(search_results)
            
            # Génération de la réponse
            ai_response = self._generate_ai_response(query, context_text)
            
            # Calcul de la confiance
            avg_score = sum(result[1] for result in search_results[:3]) / len(search_results[:3])
            confidence = min(avg_score / 10.0, 1.0)
            
            return {
                "answer": ai_response,
                "confidence": confidence,
                "sources": [{"title": result[0].title, "content": result[2][:200] + "..."} for result in search_results[:3]],
                "search_time": search_time,
                "suggestions": self._generate_suggestions(query, question_type)
            }
            
        except Exception as e:
            return {
                "answer": f"Une erreur s'est produite : {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "search_time": time.time() - start_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
            }

    def _generate_suggestions(self, query: str, question_type: str) -> List[str]:
        """Génère des suggestions contextuelles"""
        if question_type == "constitutional":
            return [
                "Quels sont les droits fondamentaux garantis ?",
                "Comment est organisé le pouvoir exécutif ?",
                "Quelles sont les conditions d'élection du président ?"
            ]
        elif question_type == "comparison":
            return [
                "Voulez-vous comparer différentes versions ?",
                "Souhaitez-vous voir les évolutions ?",
                "Cherchez-vous les différences entre articles ?"
            ]
        else:
            return [
                "Posez-moi une question sur la constitution",
                "Que voulez-vous savoir sur les droits fondamentaux ?",
                "Souhaitez-vous des informations sur le pouvoir exécutif ?"
            ] 