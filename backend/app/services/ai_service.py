import os
import time
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.constitution import Constitution
import openai
from openai import OpenAI
import re

class AIService:
    def __init__(self):
        # Version simplifiée sans embeddings pour l'instant
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Configuration pour différents niveaux de recherche
        self.search_levels = {
            "exact": {"max_results": 3, "threshold": 0.8},
            "semantic": {"max_results": 5, "threshold": 0.6},
            "fuzzy": {"max_results": 7, "threshold": 0.4},
            "general": {"max_results": 10, "threshold": 0.2}
        }
        
        # Types de questions détectées
        self.question_types = {
            "identity": ["nom", "qui es-tu", "qui es tu", "ton nom", "appelle", "qui êtes-vous"],
            "politeness": ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye", "s'il vous plaît"],
            "constitutional": ["constitution", "article", "loi", "droit", "pouvoir", "président", "gouvernement"],
            "comparison": ["différence", "comparer", "versus", "contrairement", "alors que"],
            "analysis": ["analyser", "expliquer", "comment", "pourquoi", "qu'est-ce que"],
            "specific": ["durée", "mandat", "élection", "vote", "référendum"]
        }

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question pour optimiser la recherche"""
        query_lower = query.lower()
        
        for qtype, keywords in self.question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return qtype
        
        return "general"

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Divise le texte en chunks avec overlap pour préserver le contexte"""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Ajuster la fin pour ne pas couper au milieu d'un mot
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size * 0.8:  # Si on trouve un espace dans les 20% derniers
                    end = start + last_space
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            
            # Calculer le prochain start avec overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks

    def _keyword_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par mots-clés améliorée avec scoring intelligent"""
        if not constitutions:
            return []
        
        results = []
        query_words = set(query.lower().split())
        
        for constitution in constitutions:
            if not constitution.content:
                continue
            
            # Diviser le contenu en chunks
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
                
                # Bonus pour les mots longs (plus spécifiques)
                for word in common_words:
                    if len(word) > 6:
                        score += 1.0
                
                # Bonus pour la proximité des mots
                if len(common_words) > 1:
                    # Vérifier si les mots sont proches dans le texte
                    for i, word1 in enumerate(query_words):
                        for word2 in query_words[i+1:]:
                            if word1 in chunk_lower and word2 in chunk_lower:
                                pos1 = chunk_lower.find(word1)
                                pos2 = chunk_lower.find(word2)
                                distance = abs(pos1 - pos2)
                                if distance < 100:  # Mots proches
                                    score += 3.0
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        # Trier par score et limiter les résultats
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _fuzzy_search(self, query: str, constitutions: List[Constitution], max_results: int = 7) -> List[Tuple[Constitution, float, str]]:
        """Recherche floue pour capturer les variations de termes"""
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
                
                # Recherche de variations et synonymes
                for word in query_words:
                    # Variations simples
                    if word in chunk_lower:
                        score += 2.0
                    elif word[:-1] in chunk_lower:  # Sans la dernière lettre
                        score += 1.5
                    elif word + 's' in chunk_lower:  # Pluriel
                        score += 1.5
                    elif word + 'ment' in chunk_lower:  # Adverbe
                        score += 1.0
                    elif word + 'tion' in chunk_lower:  # Nominalisation
                        score += 1.0
                
                # Recherche de concepts liés
                if any(term in query.lower() for term in ['droit', 'liberté']):
                    related_terms = ['garantie', 'protection', 'respect', 'exercice']
                    for term in related_terms:
                        if term in chunk_lower:
                            score += 0.5
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _multi_level_search(self, query: str, constitutions: List[Constitution]) -> List[Tuple[Constitution, float, str]]:
        """Recherche multi-niveaux pour maximiser les chances de trouver des résultats"""
        all_results = []
        
        # Niveau 1: Recherche exacte
        exact_results = self._keyword_search(query, constitutions, self.search_levels["exact"]["max_results"])
        all_results.extend(exact_results)
        
        # Niveau 2: Recherche floue si pas assez de résultats
        if len(all_results) < 3:
            fuzzy_results = self._fuzzy_search(query, constitutions, self.search_levels["fuzzy"]["max_results"])
            all_results.extend(fuzzy_results)
        
        # Niveau 3: Recherche par concepts si toujours pas assez
        if len(all_results) < 2:
            concept_results = self._concept_search(query, constitutions, 5)
            all_results.extend(concept_results)
        
        # Dédupliquer et trier
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result[0].id, result[2][:100])  # Constitution ID + début du chunk
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return sorted(unique_results, key=lambda x: x[1], reverse=True)[:10]

    def _concept_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par concepts et thèmes"""
        if not constitutions:
            return []
        
        # Mapping de concepts
        concept_mapping = {
            "mandat": ["durée", "période", "élection", "renouvellement"],
            "droit": ["liberté", "garantie", "protection", "exercice"],
            "pouvoir": ["exécutif", "législatif", "judiciaire", "autorité"],
            "citoyen": ["nationalité", "vote", "participation", "devoir"]
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
                
                # Recherche par concepts liés
                for concept, related_terms in concept_mapping.items():
                    if concept in query_lower:
                        for term in related_terms:
                            if term in chunk_lower:
                                score += 1.0
                
                if score > 0:
                    results.append((constitution, score, chunk))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def search_constitutions(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche hybride avec plusieurs stratégies"""
        return self._multi_level_search(query, constitutions)

    def _prepare_context(self, search_results: List[Tuple[Constitution, float, str]]) -> str:
        """Prépare le contexte pour l'IA avec les meilleurs chunks"""
        if not search_results:
            return ""
        
        context_parts = []
        for constitution, score, chunk in search_results[:5]:  # Top 5 résultats
            context_parts.append(f"📄 {constitution.title} (Score: {score:.2f}):\n{chunk}\n")
        
        return "\n".join(context_parts)

    def _generate_ai_response(self, query: str, context: str) -> str:
        """Génère une réponse avec OpenAI en utilisant un prompt optimisé"""
        try:
            system_prompt = """Tu es ConstitutionIA, un assistant spécialisé dans l'analyse des constitutions et documents juridiques.

INSTRUCTIONS STRICTES:
1. Réponds UNIQUEMENT en te basant sur les informations fournies dans le contexte
2. Si l'information n'est pas dans le contexte, dis clairement "Cette information n'est pas spécifiée dans le document"
3. Structure ta réponse de manière claire avec des points numérotés
4. Cite spécifiquement les articles et passages pertinents du document
5. Utilise un langage juridique approprié mais accessible
6. Réponds en français de manière concise et précise
7. Si tu trouves l'information, présente-la de manière structurée avec les citations exactes
8. Ne fais pas de suppositions ou d'interprétations non fondées sur le texte
9. Pour les questions de politesse ou d'identité, réponds simplement et poliment
10. Si la question est trop vague, demande des précisions

FORMAT DE RÉPONSE:
- Réponse structurée avec points numérotés
- Citations exactes des articles
- Explications claires et accessibles"""

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
            return f"Erreur lors de la génération de la réponse: {str(e)}"

    def _generate_fallback_response(self, query: str) -> str:
        """Génère une réponse de secours quand aucune information n'est trouvée"""
        try:
            system_prompt = """Tu es ConstitutionIA. L'utilisateur a posé une question sur la constitution, mais l'information n'est pas disponible dans les documents fournis.

INSTRUCTIONS:
1. Explique poliment que l'information n'est pas dans les documents disponibles
2. Suggère des questions alternatives liées à la constitution
3. Propose de reformuler la question
4. Reste professionnel et utile"""

            user_prompt = f"Question de l'utilisateur: {query}\n\nL'information n'est pas dans les documents constitutionnels disponibles."

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
            return "Je ne trouve pas cette information dans les documents constitutionnels disponibles. Pouvez-vous reformuler votre question ou poser une question différente sur la constitution ?"

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse basée sur la recherche dans les constitutions avec système hybride"""
        start_time = time.time()
        
        try:
            # Détection du type de question
            question_type = self._detect_question_type(query)
            query_lower = query.lower().strip()
            
            # Réponses directes pour questions spéciales
            if question_type == "identity":
                return {
                    "answer": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions et documents juridiques. Je peux vous aider à trouver des informations dans les documents constitutionnels.",
                    "confidence": 1.0,
                    "sources": [],
                    "search_time": time.time() - start_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
                }
            
            if question_type == "politeness":
                if 'merci' in query_lower:
                    return {
                        "answer": "De rien ! Je suis là pour vous aider avec vos questions sur la constitution.",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
                    }
                else:
                    return {
                        "answer": "Bonjour ! Comment puis-je vous aider avec la constitution ?",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
                    }
            
            # Recherche multi-niveaux
            search_results = self.search_constitutions(query, constitutions)
            search_time = time.time() - start_time
            
            if not search_results:
                # Fallback avec GPT générique
                fallback_response = self._generate_fallback_response(query)
                return {
                    "answer": fallback_response,
                    "confidence": 0.1,
                    "sources": [],
                    "search_time": search_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
                }
            
            # Préparation du contexte
            context_text = self._prepare_context(search_results)
            
            # Génération de la réponse avec contexte
            ai_response = self._generate_ai_response(query, context_text)
            
            # Calcul de la confiance basé sur les scores
            avg_score = sum(result[1] for result in search_results[:3]) / len(search_results[:3])
            confidence = min(avg_score / 10.0, 1.0)  # Normaliser entre 0 et 1
            
            return {
                "answer": ai_response,
                "confidence": confidence,
                "sources": [{"title": result[0].title, "content": result[2][:200] + "..."} for result in search_results[:3]],
                "search_time": search_time,
                "suggestions": self._generate_suggestions(query, question_type)
            }
            
        except Exception as e:
            return {
                "answer": f"Une erreur s'est produite lors du traitement de votre demande : {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "search_time": time.time() - start_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
            }

    def _generate_suggestions(self, query: str, question_type: str) -> List[str]:
        """Génère des suggestions contextuelles basées sur le type de question"""
        suggestions = []
        
        if question_type == "constitutional":
            suggestions = [
                "Quels sont les droits fondamentaux garantis ?",
                "Comment est organisé le pouvoir exécutif ?",
                "Quelles sont les conditions d'élection du président ?"
            ]
        elif question_type == "comparison":
            suggestions = [
                "Voulez-vous comparer différentes versions ?",
                "Souhaitez-vous voir les évolutions ?",
                "Cherchez-vous les différences entre articles ?"
            ]
        elif question_type == "analysis":
            suggestions = [
                "Pouvez-vous préciser votre question ?",
                "Sur quel aspect voulez-vous une analyse ?",
                "Quel article vous intéresse ?"
            ]
        else:
            suggestions = [
                "Posez-moi une question sur la constitution",
                "Que voulez-vous savoir sur les droits fondamentaux ?",
                "Souhaitez-vous des informations sur le pouvoir exécutif ?"
            ]
        
        return suggestions

    def analyze_constitution(self, constitution: Constitution, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyse approfondie d'une constitution"""
        if not constitution.content:
            return {"error": "Aucun contenu disponible pour l'analyse"}
        
        try:
            # Analyse de base
            content_length = len(constitution.content)
            word_count = len(constitution.content.split())
            
            # Détection des sections
            sections = self._identify_sections(constitution.content)
            
            # Analyse des mots-clés
            keywords = self._extract_keywords(constitution.content)
            
            # Recommandations
            recommendations = self._generate_recommendations(constitution.content, analysis_type)
            
            return {
                "title": constitution.title,
                "year": constitution.year,
                "content_length": content_length,
                "word_count": word_count,
                "sections": sections,
                "keywords": keywords,
                "recommendations": recommendations,
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            return {"error": f"Erreur lors de l'analyse: {str(e)}"}

    def _identify_sections(self, content: str) -> List[str]:
        """Identifie les sections principales du document"""
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('TITRE') or line.startswith('CHAPITRE') or line.startswith('Section')):
                sections.append(line)
        
        return sections[:10]  # Limiter à 10 sections

    def _extract_keywords(self, content: str) -> List[str]:
        """Extrait les mots-clés principaux"""
        # Mots-clés juridiques courants
        legal_keywords = [
            'droit', 'liberté', 'pouvoir', 'président', 'gouvernement', 'parlement',
            'élection', 'vote', 'citoyen', 'nationalité', 'constitution', 'loi'
        ]
        
        content_lower = content.lower()
        found_keywords = []
        
        for keyword in legal_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords

    def _generate_recommendations(self, content: str, analysis_type: str) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        if analysis_type == "general":
            recommendations = [
                "Document bien structuré avec des sections claires",
                "Contient des dispositions sur les droits fondamentaux",
                "Définit clairement les pouvoirs des institutions"
            ]
        elif analysis_type == "rights":
            recommendations = [
                "Vérifiez la protection des droits individuels",
                "Analysez les mécanismes de garantie",
                "Examinez les limitations possibles"
            ]
        
        return recommendations 