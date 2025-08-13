"""
Service IA optimisé pour ChatNow - Interface de conversation avec cache et recherche intelligente
Module optimisé pour les performances et la précision
"""

import logging
import hashlib
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.constitution_data import (
    ConstitutionArticle, 
    ConstitutionStructure, 
    ConstitutionKeyword,
    ConstitutionCache
)

logger = logging.getLogger(__name__)

class OptimizedChatNowService:
    """
    Service IA optimisé pour l'interface ChatNow
    Avec cache, recherche intelligente et gestion de l'historique
    """
    
    def __init__(self, db: Session):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self.db = db
        
        # Cache en mémoire pour le contenu de la constitution
        self._constitution_cache = None
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 heure
        
    def create_chat_response(self, question: str, chat_history: List[Dict] = None, user_id: Optional[str] = None) -> str:
        """
        Crée une réponse optimisée avec cache et recherche intelligente - AMÉLIORÉE AVEC RECHERCHE PROFONDE
        """
        try:
            # Vérifier le cache des réponses
            cached_response = self._check_response_cache(question)
            if cached_response:
                return cached_response
            
            # TRAITEMENT DU CONTEXTE - NOUVEAU
            context_analysis = self._analyze_question_context(question)
            logger.info(f"Analyse du contexte: {context_analysis}")
            
            # RECHERCHE PROFONDE EN PLUSIEURS TOURS
            relevant_articles = self._deep_search_with_multiple_rounds(question, context_analysis)
            
            # Si aucun article trouvé après tous les tours, générer un fallback intelligent
            if not relevant_articles:
                return self._generate_contextual_fallback_response(question, context_analysis)
            
            # Construire le contexte optimisé
            optimized_context = self._build_optimized_context(relevant_articles)
            
            # Construire l'historique de conversation avec contexte
            conversation_messages = self._build_conversation_messages_with_context(question, optimized_context, context_analysis, chat_history)
            
            # Appel à l'API OpenAI avec paramètres optimisés
            response = self._call_openai_api(conversation_messages)
            
            # Sauvegarder dans le cache
            self._save_response_cache(question, response, relevant_articles)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse optimisée: {e}")
            return "Désolé, je rencontre une difficulté technique. Pouvez-vous reformuler votre question ?"
    
    def _generate_fallback_response(self, question: str) -> str:
        """
        Génère une réponse de fallback intelligente quand aucun article n'est trouvé - AMÉLIORÉ
        """
        try:
            question_lower = question.lower()
            
            # 1. Essayer une recherche plus large avec des mots-clés généraux
            general_articles = self._search_with_general_keywords(question)
            
            if general_articles:
                context = self._build_optimized_context(general_articles[:3])
                messages = [
                    {
                        "role": "system",
                        "content": """Tu es ConstitutionIA. L'utilisateur pose une question mais les articles exacts ne sont pas trouvés.
Propose des articles généraux qui pourraient être pertinents et explique leur lien avec la question.
Sois honnête sur le fait que ce ne sont pas les articles exacts demandés, mais propose des alternatives utiles."""
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nArticles généraux disponibles:\n{context}"
                    }
                ]
                
                response = self._call_openai_api(messages)
                return response
            
            # 2. Si aucune recherche générale ne fonctionne, essayer une recherche par thème
            theme_articles = self._search_by_theme(question)
            
            if theme_articles:
                context = self._build_optimized_context(theme_articles[:2])
                messages = [
                    {
                        "role": "system",
                        "content": """Tu es ConstitutionIA. L'utilisateur pose une question sur un thème spécifique.
Propose des articles liés à ce thème et explique leur pertinence.
Suggère des reformulations de la question pour obtenir des informations plus précises."""
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nArticles thématiques disponibles:\n{context}"
                    }
                ]
                
                response = self._call_openai_api(messages)
                return response
            
            # 3. Dernier recours : réponse générique avec suggestions
            return self._generate_generic_fallback(question)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de fallback: {e}")
            return "Cette information n'est pas disponible dans la constitution actuelle."
    
    def _analyze_question_context(self, question: str) -> Dict[str, any]:
        """
        Analyse le contexte de la question pour mieux comprendre l'intention
        """
        try:
            question_lower = question.lower()
            context = {
                'question_type': 'general',
                'main_topic': None,
                'sub_topics': [],
                'intent': 'information',
                'entities': [],
                'keywords': [],
                'context_clues': []
            }
            
            # Détecter le type de question
            if any(word in question_lower for word in ['comment', 'comment se', 'comment sont']):
                context['question_type'] = 'procedure'
                context['intent'] = 'how_to'
            elif any(word in question_lower for word in ['quand', 'quand peut', 'quand doit']):
                context['question_type'] = 'timing'
                context['intent'] = 'when'
            elif any(word in question_lower for word in ['qui', 'qui peut', 'qui doit']):
                context['question_type'] = 'actor'
                context['intent'] = 'who'
            elif any(word in question_lower for word in ['quoi', 'qu\'est-ce', 'définition']):
                context['question_type'] = 'definition'
                context['intent'] = 'what_is'
            elif any(word in question_lower for word in ['pourquoi', 'raison', 'cause']):
                context['question_type'] = 'reason'
                context['intent'] = 'why'
            elif any(word in question_lower for word in ['quels', 'quelles', 'liste']):
                context['question_type'] = 'list'
                context['intent'] = 'list'
            
            # Détecter les entités principales
            entities = {
                'enfants': ['enfant', 'enfants', 'jeune', 'jeunes', 'mineur', 'mineurs', 'scolarité'],
                'éducation': ['éducation', 'enseignement', 'école', 'scolaire', 'formation'],
                'droits': ['droit', 'droits', 'liberté', 'libertés', 'garantie'],
                'citoyens': ['citoyen', 'citoyens', 'citoyenne', 'peuple'],
                'président': ['président', 'présidence', 'chef de l\'état'],
                'gouvernement': ['gouvernement', 'ministre', 'exécutif'],
                'parlement': ['parlement', 'assemblée', 'député', 'sénateur'],
                'justice': ['justice', 'tribunal', 'cour', 'judiciaire'],
                'élections': ['élection', 'vote', 'suffrage', 'scrutin'],
                'sécurité': ['sécurité', 'défense', 'ordre', 'protection'],
                'famille': ['famille', 'parent', 'mariage'],
                'travail': ['travail', 'emploi', 'profession'],
                'santé': ['santé', 'médical', 'soin'],
                'propriété': ['propriété', 'bien', 'domaine'],
                'religion': ['religion', 'culte', 'croyance'],
                'culture': ['culture', 'art', 'patrimoine'],
                'environnement': ['environnement', 'écologie', 'nature']
            }
            
            # Identifier les entités dans la question
            for entity, keywords in entities.items():
                if any(keyword in question_lower for keyword in keywords):
                    context['entities'].append(entity)
                    if not context['main_topic']:
                        context['main_topic'] = entity
            
            # Extraire les mots-clés contextuels
            context_keywords = []
            if 'enfant' in question_lower or 'enfants' in question_lower:
                context_keywords.extend(['protection', 'éducation', 'famille', 'droits'])
            if 'droit' in question_lower or 'droits' in question_lower:
                context_keywords.extend(['garantie', 'protection', 'liberté'])
            if 'citoyen' in question_lower:
                context_keywords.extend(['devoir', 'responsabilité', 'participation'])
            if 'président' in question_lower:
                context_keywords.extend(['pouvoir', 'mandat', 'élection'])
            if 'gouvernement' in question_lower:
                context_keywords.extend(['formation', 'responsabilité', 'pouvoir'])
            
            context['keywords'] = context_keywords
            
            # Ajouter des indices contextuels
            if 'droits' in question_lower and 'enfant' in question_lower:
                context['context_clues'].append('droits_fondamentaux_enfants')
            if 'éducation' in question_lower:
                context['context_clues'].append('éducation_obligatoire')
            if 'protection' in question_lower:
                context['context_clues'].append('protection_sociale')
            
            return context
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du contexte: {e}")
            return {'question_type': 'general', 'main_topic': None, 'sub_topics': [], 'intent': 'information', 'entities': [], 'keywords': [], 'context_clues': []}
    
    def _search_relevant_articles_with_context(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche d'articles avec prise en compte du contexte
        """
        try:
            # Recherche directe par numéro d'article (priorité)
            article_number_articles = self._search_by_article_number(question)
            if article_number_articles:
                return article_number_articles
            
            # Recherche contextuelle basée sur l'analyse
            context_articles = []
            
            # Recherche par entités principales
            for entity in context['entities']:
                articles = self._search_by_entity(entity)
                context_articles.extend(articles)
            
            # Recherche par mots-clés contextuels
            for keyword in context['keywords']:
                articles = self._search_by_context_keyword(keyword)
                context_articles.extend(articles)
            
            # Recherche par indices contextuels
            for clue in context['context_clues']:
                articles = self._search_by_context_clue(clue)
                context_articles.extend(articles)
            
            # Dédupliquer et trier par pertinence
            unique_articles = list({article.id: article for article in context_articles}.values())
            unique_articles.sort(key=lambda x: self._calculate_context_relevance_score(x, context), reverse=True)
            
            return unique_articles[:5]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche contextuelle: {e}")
            return []
    
    def _search_contextual_articles(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche contextuelle élargie quand la recherche principale échoue
        """
        try:
            # Recherche par thèmes généraux liés au contexte
            theme_mapping = {
                'enfants': ['éducation', 'protection', 'famille', 'droits fondamentaux'],
                'droits': ['liberté', 'garantie', 'protection', 'citoyenneté'],
                'citoyens': ['devoir', 'responsabilité', 'participation', 'droits'],
                'président': ['pouvoir exécutif', 'mandat', 'élection', 'responsabilité'],
                'gouvernement': ['formation', 'pouvoir', 'responsabilité', 'exécutif'],
                'éducation': ['enseignement', 'formation', 'droit', 'obligation'],
                'sécurité': ['défense', 'ordre', 'protection', 'sécurité nationale']
            }
            
            contextual_articles = []
            
            # Recherche par thèmes liés
            for entity in context['entities']:
                if entity in theme_mapping:
                    for theme in theme_mapping[entity]:
                        articles = self._search_by_theme(theme)
                        contextual_articles.extend(articles)
            
            # Recherche par type de question
            if context['question_type'] == 'procedure':
                contextual_articles.extend(self._search_by_theme('procédure'))
            elif context['question_type'] == 'timing':
                contextual_articles.extend(self._search_by_theme('condition'))
            elif context['question_type'] == 'actor':
                contextual_articles.extend(self._search_by_theme('responsabilité'))
            
            # Dédupliquer et limiter
            unique_articles = list({article.id: article for article in contextual_articles}.values())
            return unique_articles[:3]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche contextuelle élargie: {e}")
            return []
    
    def _generate_contextual_fallback_response(self, question: str, context: Dict[str, any]) -> str:
        """
        Génère une réponse de fallback intelligente basée sur le contexte
        """
        try:
            # Construire une réponse contextuelle
            if context['main_topic'] == 'enfants':
                return """Bien que la constitution ne mentionne pas explicitement "les droits des enfants", elle contient plusieurs articles pertinents :

• **Article 21** : Garantit le droit à l'éducation et à la formation
• **Article 19** : Protège la liberté d'expression
• **Article 20** : Consacre le droit de pétition

Ces articles établissent des protections fondamentales qui s'appliquent également aux enfants. Pour des informations plus spécifiques sur les droits des enfants, vous pourriez consulter le code civil ou les lois relatives à la protection de l'enfance."""
            
            elif context['main_topic'] == 'droits':
                return """La constitution garantit plusieurs droits fondamentaux :

• **Article 19** : Liberté d'expression
• **Article 21** : Droit à l'éducation
• **Article 20** : Droit de pétition

Pour des informations plus spécifiques, pouvez-vous préciser quel type de droits vous intéresse (droits civils, politiques, sociaux, économiques) ?"""
            
            elif context['main_topic'] == 'citoyens':
                return """La constitution définit les droits et devoirs des citoyens :

• **Article 35** : Devoir de participer aux élections
• **Article 39** : Devoir de défendre l'intégrité du territoire
• **Article 20** : Droit de pétition

Souhaitez-vous des informations sur des aspects spécifiques de la citoyenneté ?"""
            
            else:
                # Réponse générique avec suggestions contextuelles
                suggestions = []
                if context['entities']:
                    suggestions.append(f"• Consulter les articles sur {', '.join(context['entities'])}")
                if context['question_type'] == 'procedure':
                    suggestions.append("• Rechercher les procédures constitutionnelles")
                elif context['question_type'] == 'timing':
                    suggestions.append("• Consulter les conditions et délais")
                
                return f"""Cette information spécifique n'est pas directement disponible dans la constitution.

Suggestions pour obtenir des informations pertinentes :
{chr(10).join(suggestions)}

Vous pouvez également :
• Poser une question sur un article spécifique (ex: "que dit l'article 15")
• Reformuler votre question avec des termes plus précis
• Consulter les articles sur les droits fondamentaux"""
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du fallback contextuel: {e}")
            return "Cette information n'est pas disponible dans la constitution actuelle. Pouvez-vous reformuler votre question ?"
    
    def _build_conversation_messages_with_context(self, question: str, context: str, context_analysis: Dict[str, any], chat_history: List[Dict] = None) -> List[Dict]:
        """
        Construit les messages de conversation avec prise en compte du contexte
        """
        try:
            messages = []
            
            # Message système avec contexte
            system_message = f"""Tu es ConstitutionIA, un assistant spécialisé dans la constitution de la Guinée.

CONTEXTE DE LA QUESTION :
- Type : {context_analysis['question_type']}
- Intention : {context_analysis['intent']}
- Sujet principal : {context_analysis['main_topic']}
- Entités détectées : {', '.join(context_analysis['entities'])}

RÈGLES STRICTES :
1. Réponds UNIQUEMENT basé sur les articles fournis
2. Cite TOUJOURS les numéros d'articles
3. Sois précis et factuel
4. Si l'information n'est pas dans les articles, dis-le clairement
5. Propose des alternatives pertinentes quand c'est possible
6. Format de réponse : "- Article X: [résumé concis]"

CONTENU DE LA CONSTITUTION :
{context}"""
            
            messages.append({"role": "system", "content": system_message})
            
            # Ajouter l'historique de conversation
            if chat_history:
                for msg in chat_history[-4:]:  # Limiter à 4 messages récents
                    messages.append(msg)
            
            # Ajouter la question actuelle
            messages.append({"role": "user", "content": question})
            
            return messages
            
        except Exception as e:
            logger.error(f"Erreur lors de la construction des messages avec contexte: {e}")
            return self._build_conversation_messages(question, context, chat_history)
    
    def _search_by_entity(self, entity: str) -> List[ConstitutionArticle]:
        """Recherche par entité spécifique"""
        try:
            entity_keywords = {
                'enfants': ['enfant', 'jeune', 'mineur', 'scolarité'],
                'éducation': ['éducation', 'enseignement', 'école', 'formation'],
                'droits': ['droit', 'liberté', 'garantie', 'protection'],
                'citoyens': ['citoyen', 'citoyenne', 'peuple', 'national'],
                'président': ['président', 'présidence', 'chef'],
                'gouvernement': ['gouvernement', 'ministre', 'exécutif'],
                'parlement': ['parlement', 'assemblée', 'député'],
                'justice': ['justice', 'tribunal', 'cour'],
                'élections': ['élection', 'vote', 'suffrage'],
                'sécurité': ['sécurité', 'défense', 'ordre'],
                'famille': ['famille', 'parent', 'mariage'],
                'travail': ['travail', 'emploi', 'profession'],
                'santé': ['santé', 'médical', 'soin'],
                'propriété': ['propriété', 'bien', 'domaine'],
                'religion': ['religion', 'culte', 'croyance'],
                'culture': ['culture', 'art', 'patrimoine'],
                'environnement': ['environnement', 'écologie', 'nature']
            }
            
            if entity in entity_keywords:
                keywords = entity_keywords[entity]
                articles = []
                for keyword in keywords:
                    found_articles = self.db.query(ConstitutionArticle).filter(
                        and_(
                            ConstitutionArticle.content.ilike(f'%{keyword}%'),
                            ConstitutionArticle.is_active == True
                        )
                    ).limit(2).all()
                    articles.extend(found_articles)
                
                # Dédupliquer
                unique_articles = list({article.id: article for article in articles}.values())
                return unique_articles[:3]
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par entité: {e}")
            return []
    
    def _search_by_context_keyword(self, keyword: str) -> List[ConstitutionArticle]:
        """Recherche par mot-clé contextuel"""
        try:
            articles = self.db.query(ConstitutionArticle).filter(
                and_(
                    ConstitutionArticle.content.ilike(f'%{keyword}%'),
                    ConstitutionArticle.is_active == True
                )
            ).limit(2).all()
            return articles
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par mot-clé contextuel: {e}")
            return []
    
    def _search_by_context_clue(self, clue: str) -> List[ConstitutionArticle]:
        """Recherche par indice contextuel"""
        try:
            clue_mapping = {
                'droits_fondamentaux_enfants': ['éducation', 'protection', 'droit'],
                'éducation_obligatoire': ['éducation', 'enseignement', 'obligation'],
                'protection_sociale': ['protection', 'sécurité', 'garantie']
            }
            
            if clue in clue_mapping:
                keywords = clue_mapping[clue]
                articles = []
                for keyword in keywords:
                    found_articles = self.db.query(ConstitutionArticle).filter(
                        and_(
                            ConstitutionArticle.content.ilike(f'%{keyword}%'),
                            ConstitutionArticle.is_active == True
                        )
                    ).limit(1).all()
                    articles.extend(found_articles)
                
                return articles[:2]
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par indice contextuel: {e}")
            return []
    
    def _calculate_context_relevance_score(self, article: ConstitutionArticle, context: Dict[str, any]) -> float:
        """Calcule un score de pertinence basé sur le contexte"""
        try:
            score = 0.0
            content_lower = article.content.lower()
            
            # Score basé sur les entités
            for entity in context['entities']:
                if entity in content_lower:
                    score += 3.0
            
            # Score basé sur les mots-clés contextuels
            for keyword in context['keywords']:
                if keyword in content_lower:
                    score += 2.0
            
            # Score basé sur le type de question
            if context['question_type'] == 'procedure' and any(word in content_lower for word in ['procédure', 'méthode', 'processus']):
                score += 2.0
            elif context['question_type'] == 'timing' and any(word in content_lower for word in ['quand', 'délai', 'durée']):
                score += 2.0
            
            # Score basé sur la longueur (préférer les articles détaillés)
            score += min(len(article.content) / 1000, 1.0)
            
            return score
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de pertinence contextuel: {e}")
            return 0.0
    
    def _deep_search_with_multiple_rounds(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche profonde en plusieurs tours avant d'abandonner
        """
        try:
            logger.info("🔍 Début de la recherche profonde en plusieurs tours")
            
            # TOUR 1: Recherche directe par numéro d'article (priorité absolue)
            logger.info("📋 Tour 1: Recherche par numéro d'article")
            article_number_articles = self._search_by_article_number(question)
            if article_number_articles:
                logger.info(f"✅ Articles trouvés par numéro: {[a.article_number for a in article_number_articles]}")
                return article_number_articles
            
            # TOUR 2: Recherche contextuelle basée sur l'analyse
            logger.info("📋 Tour 2: Recherche contextuelle")
            context_articles = self._search_relevant_articles_with_context(question, context)
            if context_articles:
                logger.info(f"✅ Articles trouvés par contexte: {[a.article_number for a in context_articles]}")
                return context_articles
            
            # TOUR 3: Recherche contextuelle élargie
            logger.info("📋 Tour 3: Recherche contextuelle élargie")
            contextual_articles = self._search_contextual_articles(question, context)
            if contextual_articles:
                logger.info(f"✅ Articles trouvés par contexte élargi: {[a.article_number for a in contextual_articles]}")
                return contextual_articles
            
            # TOUR 4: Recherche par mots-clés étendus
            logger.info("📋 Tour 4: Recherche par mots-clés étendus")
            extended_keywords = self._generate_extended_keywords(question, context)
            extended_articles = self._search_by_extended_keywords(extended_keywords)
            if extended_articles:
                logger.info(f"✅ Articles trouvés par mots-clés étendus: {[a.article_number for a in extended_articles]}")
                return extended_articles
            
            # TOUR 5: Recherche par thèmes généraux
            logger.info("📋 Tour 5: Recherche par thèmes généraux")
            theme_articles = self._search_by_general_themes(question, context)
            if theme_articles:
                logger.info(f"✅ Articles trouvés par thèmes généraux: {[a.article_number for a in theme_articles]}")
                return theme_articles
            
            # TOUR 6: Recherche par similarité sémantique
            logger.info("📋 Tour 6: Recherche par similarité sémantique")
            semantic_articles = self._search_by_semantic_similarity(question, context)
            if semantic_articles:
                logger.info(f"✅ Articles trouvés par similarité sémantique: {[a.article_number for a in semantic_articles]}")
                return semantic_articles
            
            # TOUR 7: Recherche dans tous les articles avec scoring
            logger.info("📋 Tour 7: Recherche exhaustive avec scoring")
            exhaustive_articles = self._search_exhaustive_with_scoring(question, context)
            if exhaustive_articles:
                logger.info(f"✅ Articles trouvés par recherche exhaustive: {[a.article_number for a in exhaustive_articles]}")
                return exhaustive_articles
            
            logger.warning("❌ Aucun article trouvé après 7 tours de recherche")
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche profonde: {e}")
            return []
    
    def _generate_extended_keywords(self, question: str, context: Dict[str, any]) -> List[str]:
        """
        Génère des mots-clés étendus basés sur la question et le contexte
        """
        try:
            question_lower = question.lower()
            extended_keywords = []
            
            # Mots-clés spécifiques pour "mandat présidentiel"
            if any(word in question_lower for word in ['mandat', 'président', 'durée', 'période']):
                extended_keywords.extend(['mandat', 'président', 'élection', 'durée', 'période', 'sept ans', 'renouvelable'])
            
            # Mots-clés pour les droits
            if any(word in question_lower for word in ['droit', 'droits', 'liberté']):
                extended_keywords.extend(['droit', 'liberté', 'garantie', 'protection', 'fondamental'])
            
            # Mots-clés pour les devoirs
            if any(word in question_lower for word in ['devoir', 'devoirs', 'obligation']):
                extended_keywords.extend(['devoir', 'obligation', 'responsabilité', 'participation'])
            
            # Mots-clés pour l'éducation
            if any(word in question_lower for word in ['éducation', 'école', 'enseignement']):
                extended_keywords.extend(['éducation', 'enseignement', 'formation', 'école', 'gratuit'])
            
            # Mots-clés pour la famille
            if any(word in question_lower for word in ['famille', 'parent', 'mariage']):
                extended_keywords.extend(['famille', 'mariage', 'parent', 'enfant'])
            
            # Mots-clés pour le travail
            if any(word in question_lower for word in ['travail', 'emploi', 'profession']):
                extended_keywords.extend(['travail', 'emploi', 'rémunération', 'syndicat', 'grève'])
            
            # Mots-clés pour la santé
            if any(word in question_lower for word in ['santé', 'médical', 'soin']):
                extended_keywords.extend(['santé', 'médical', 'soin', 'bien-être'])
            
            # Mots-clés généraux si aucun mot-clé spécifique
            if not extended_keywords:
                extended_keywords = ['droit', 'garantie', 'protection', 'responsabilité', 'pouvoir', 'institution']
            
            logger.info(f"Mots-clés étendus générés: {extended_keywords}")
            return extended_keywords
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des mots-clés étendus: {e}")
            return ['droit', 'garantie', 'protection']
    
    def _search_by_extended_keywords(self, keywords: List[str]) -> List[ConstitutionArticle]:
        """
        Recherche par mots-clés étendus
        """
        try:
            all_articles = []
            
            for keyword in keywords:
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(3).all()
                all_articles.extend(articles)
            
            # Dédupliquer et trier par pertinence
            unique_articles = list({article.id: article for article in all_articles}.values())
            return unique_articles[:5]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par mots-clés étendus: {e}")
            return []
    
    def _search_by_general_themes(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche par thèmes généraux
        """
        try:
            question_lower = question.lower()
            theme_articles = []
            
            # Thèmes généraux
            general_themes = {
                'droits_fondamentaux': ['droit', 'liberté', 'garantie', 'protection'],
                'institutions': ['institution', 'organe', 'autorité', 'pouvoir'],
                'citoyenneté': ['citoyen', 'devoir', 'responsabilité', 'participation'],
                'éducation_sociale': ['éducation', 'formation', 'enseignement', 'école'],
                'famille_société': ['famille', 'mariage', 'parent', 'enfant'],
                'travail_économie': ['travail', 'emploi', 'rémunération', 'économie'],
                'santé_bien_être': ['santé', 'médical', 'soin', 'bien-être'],
                'sécurité_ordre': ['sécurité', 'ordre', 'protection', 'défense']
            }
            
            # Rechercher dans tous les thèmes
            for theme, keywords in general_themes.items():
                for keyword in keywords:
                    if keyword in question_lower:
                        articles = self.db.query(ConstitutionArticle).filter(
                            and_(
                                ConstitutionArticle.content.ilike(f'%{keyword}%'),
                                ConstitutionArticle.is_active == True
                            )
                        ).limit(2).all()
                        theme_articles.extend(articles)
                        break
            
            # Dédupliquer et limiter
            unique_articles = list({article.id: article for article in theme_articles}.values())
            return unique_articles[:3]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par thèmes généraux: {e}")
            return []
    
    def _search_by_semantic_similarity(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche par similarité sémantique
        """
        try:
            # Rechercher des articles qui pourraient être sémantiquement liés
            question_words = question.lower().split()
            
            # Mots-clés sémantiques
            semantic_keywords = []
            for word in question_words:
                if len(word) > 3:  # Ignorer les mots trop courts
                    semantic_keywords.append(word)
            
            # Ajouter des mots-clés contextuels
            if context['main_topic']:
                semantic_keywords.append(context['main_topic'])
            
            semantic_articles = []
            for keyword in semantic_keywords[:5]:  # Limiter à 5 mots-clés
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(1).all()
                semantic_articles.extend(articles)
            
            # Dédupliquer
            unique_articles = list({article.id: article for article in semantic_articles}.values())
            return unique_articles[:3]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par similarité sémantique: {e}")
            return []
    
    def _search_exhaustive_with_scoring(self, question: str, context: Dict[str, any]) -> List[ConstitutionArticle]:
        """
        Recherche exhaustive dans tous les articles avec scoring
        """
        try:
            # Récupérer tous les articles actifs
            all_articles = self.db.query(ConstitutionArticle).filter(
                ConstitutionArticle.is_active == True
            ).all()
            
            # Calculer un score pour chaque article
            scored_articles = []
            question_lower = question.lower()
            
            for article in all_articles:
                score = 0
                content_lower = article.content.lower()
                
                # Score basé sur les mots de la question
                question_words = question_lower.split()
                for word in question_words:
                    if len(word) > 3 and word in content_lower:
                        score += 1
                
                # Score basé sur le contexte
                if context['main_topic'] and context['main_topic'] in content_lower:
                    score += 2
                
                # Score basé sur les entités
                for entity in context['entities']:
                    if entity in content_lower:
                        score += 1
                
                # Score basé sur les mots-clés
                for keyword in context['keywords']:
                    if keyword in content_lower:
                        score += 1
                
                # Score basé sur la longueur (préférer les articles détaillés)
                score += min(len(article.content) / 1000, 1.0)
                
                if score > 0:
                    scored_articles.append((article, score))
            
            # Trier par score et retourner les meilleurs
            scored_articles.sort(key=lambda x: x[1], reverse=True)
            return [article for article, score in scored_articles[:3]]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche exhaustive: {e}")
            return []
    
    def _search_with_general_keywords(self, question: str) -> List[ConstitutionArticle]:
        """
        Recherche avec des mots-clés généraux - AMÉLIORÉ
        """
        try:
            question_lower = question.lower()
            
            # Mots-clés généraux adaptés au contexte de la question
            general_keywords = []
            
            # Ajouter des mots-clés basés sur le contexte de la question
            if any(word in question_lower for word in ['gouvernement', 'ministre', 'formation']):
                general_keywords.extend(['exécutif', 'pouvoir', 'responsabilité'])
            
            if any(word in question_lower for word in ['liberté', 'expression', 'opinion']):
                general_keywords.extend(['droit', 'garantie', 'protection'])
            
            if any(word in question_lower for word in ['devoir', 'obligation', 'contrainte']):
                general_keywords.extend(['responsabilité', 'obligation', 'devoir'])
            
            if any(word in question_lower for word in ['révision', 'modifier', 'changer']):
                general_keywords.extend(['constitution', 'procédure', 'amendement'])
            
            if any(word in question_lower for word in ['promulgation', 'publication', 'entrée']):
                general_keywords.extend(['loi', 'procédure', 'publication'])
            
            if any(word in question_lower for word in ['trahison', 'crime', 'infraction']):
                general_keywords.extend(['responsabilité', 'crime', 'infraction'])
            
            if any(word in question_lower for word in ['urgence', 'crise', 'exceptionnel']):
                general_keywords.extend(['pouvoir', 'exception', 'crise'])
            
            if any(word in question_lower for word in ['dissolution', 'dissoudre']):
                general_keywords.extend(['pouvoir', 'procédure', 'fin'])
            
            # Mots-clés généraux par défaut
            if not general_keywords:
                general_keywords = ['droit', 'garantie', 'protection', 'responsabilité', 'pouvoir', 'institution']
            
            similar_articles = []
            for keyword in general_keywords:
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(3).all()
                similar_articles.extend(articles)
            
            # Dédupliquer et limiter
            unique_articles = list({article.id: article for article in similar_articles}.values())
            return unique_articles[:5]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avec mots-clés généraux: {e}")
            return []
    
    def _search_by_theme(self, question: str) -> List[ConstitutionArticle]:
        """
        Recherche par thème basée sur le contenu de la question
        """
        try:
            question_lower = question.lower()
            
            # Définir des thèmes et leurs mots-clés associés
            themes = {
                'droits_fondamentaux': ['droit', 'liberté', 'garantie', 'protection', 'fondamental'],
                'institutions': ['institution', 'organe', 'autorité', 'structure'],
                'pouvoirs': ['pouvoir', 'compétence', 'attribution', 'prérogative'],
                'procédures': ['procédure', 'méthode', 'processus', 'modalité'],
                'responsabilités': ['responsabilité', 'devoir', 'obligation', 'compte'],
                'élections': ['élection', 'vote', 'suffrage', 'scrutin', 'électoral'],
                'législation': ['loi', 'législation', 'législatif', 'vote loi'],
                'justice': ['justice', 'tribunal', 'cour', 'judiciaire'],
                'sécurité': ['sécurité', 'défense', 'ordre', 'protection'],
                'économie': ['économie', 'financier', 'budget', 'fiscal']
            }
            
            # Identifier le thème le plus pertinent
            theme_scores = {}
            for theme, keywords in themes.items():
                score = sum(1 for keyword in keywords if keyword in question_lower)
                if score > 0:
                    theme_scores[theme] = score
            
            if not theme_scores:
                return []
            
            # Prendre le thème avec le score le plus élevé
            best_theme = max(theme_scores, key=theme_scores.get)
            theme_keywords = themes[best_theme]
            
            # Rechercher des articles liés à ce thème
            theme_articles = []
            for keyword in theme_keywords[:3]:  # Limiter à 3 mots-clés
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(2).all()
                theme_articles.extend(articles)
            
            # Dédupliquer et limiter
            unique_articles = list({article.id: article for article in theme_articles}.values())
            return unique_articles[:3]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par thème: {e}")
            return []
    
    def _generate_generic_fallback(self, question: str) -> str:
        """
        Génère une réponse de fallback générique avec suggestions
        """
        try:
            # Analyser le type de question pour donner des suggestions pertinentes
            question_lower = question.lower()
            
            suggestions = []
            
            if any(word in question_lower for word in ['gouvernement', 'ministre']):
                suggestions.append("• Demander des informations sur le pouvoir exécutif")
                suggestions.append("• Consulter les articles sur le Président de la République")
                suggestions.append("• Rechercher les compétences du Premier ministre")
            
            elif any(word in question_lower for word in ['liberté', 'expression']):
                suggestions.append("• Consulter les articles sur les droits fondamentaux")
                suggestions.append("• Rechercher les garanties constitutionnelles")
                suggestions.append("• Voir les limites des libertés")
            
            elif any(word in question_lower for word in ['devoir', 'obligation']):
                suggestions.append("• Consulter les articles sur les devoirs des citoyens")
                suggestions.append("• Rechercher les responsabilités constitutionnelles")
                suggestions.append("• Voir les obligations des institutions")
            
            elif any(word in question_lower for word in ['révision', 'modifier']):
                suggestions.append("• Consulter les articles sur la révision constitutionnelle")
                suggestions.append("• Rechercher les procédures d'amendement")
                suggestions.append("• Voir les limites de révision")
            
            else:
                suggestions.append("• Reformuler votre question avec des termes plus spécifiques")
                suggestions.append("• Consulter les articles sur les droits fondamentaux")
                suggestions.append("• Rechercher des informations sur les institutions")
            
            suggestions_text = "\n".join(suggestions)
            
            return f"""Cette information spécifique n'est pas disponible dans la constitution actuelle.

Suggestions pour obtenir des informations pertinentes :
{suggestions_text}

Vous pouvez également :
• Poser une question sur un article spécifique (ex: "que dit l'article 15")
• Demander des informations sur un thème général (ex: "droits des citoyens")
• Consulter les articles sur les institutions de la République"""
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du fallback générique: {e}")
            return "Cette information n'est pas disponible dans la constitution actuelle. Pouvez-vous reformuler votre question ?"
    
    def _find_similar_articles(self, question: str) -> List[ConstitutionArticle]:
        """
        Trouve des articles similaires basés sur des mots-clés généraux
        """
        try:
            # Mots-clés généraux pour la recherche
            general_keywords = ['droit', 'garantie', 'protection', 'responsabilité', 'pouvoir', 'institution']
            
            similar_articles = []
            for keyword in general_keywords:
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(2).all()
                similar_articles.extend(articles)
            
            # Dédupliquer et limiter
            unique_articles = list({article.id: article for article in similar_articles}.values())
            return unique_articles[:3]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'articles similaires: {e}")
            return []
    
    def _check_response_cache(self, question: str) -> Optional[str]:
        """
        Vérifie si une réponse existe en cache - AMÉLIORÉ
        """
        try:
            question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
            
            cached = self.db.query(ConstitutionCache).filter(
                and_(
                    ConstitutionCache.question_hash == question_hash,
                    ConstitutionCache.expires_at > datetime.now()
                )
            ).first()
            
            if cached:
                # Vérifier si la réponse n'est pas trop ancienne (max 24h)
                from datetime import timedelta
                if cached.created_at < datetime.now() - timedelta(hours=24):
                    logger.info(f"Cache expiré pour: {question[:50]}...")
                    return None
                
                # Mettre à jour le compteur d'utilisation
                cached.hit_count += 1
                cached.last_used = datetime.now()
                self.db.commit()
                
                logger.info(f"Réponse trouvée en cache pour: {question[:50]}...")
                return cached.response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du cache: {e}")
            return None
    
    def _search_relevant_articles(self, question: str) -> List[ConstitutionArticle]:
        """
        Recherche intelligente des articles pertinents avec recherche contextuelle
        """
        try:
            question_lower = question.lower()
            
            # 1. PRIORITÉ: Recherche directe par numéro d'article
            article_number_articles = self._search_by_article_number(question)
            if article_number_articles:
                logger.info(f"Articles trouvés par numéro: {[a.article_number for a in article_number_articles]}")
                return article_number_articles
            
            # 2. Recherche par mots-clés
            keywords = self._extract_question_keywords(question)
            logger.info(f"Mots-clés extraits: {keywords}")
            
            # Si aucun mot-clé spécifique trouvé, faire une recherche plus large
            if not keywords or 'général' in keywords:
                logger.info("Recherche générale activée")
                return self._search_general_articles(question)
            
            # 3. Recherche par mots-clés dans la table ConstitutionKeyword
            keyword_articles = self._search_by_keywords(keywords)
            
            # 4. Recherche par contenu (recherche textuelle améliorée)
            content_articles = self._search_by_content(keywords)
            
            # 5. Recherche par synonymes et mots liés
            synonym_articles = self._search_by_synonyms(question_lower)
            
            # 6. Combiner toutes les recherches et dédupliquer
            all_articles = list(set(keyword_articles + content_articles + synonym_articles))
            
            # 7. Trier par pertinence
            all_articles.sort(key=lambda x: self._calculate_relevance_score(x, question), reverse=True)
            
            logger.info(f"Articles trouvés: {len(all_articles)}")
            for article in all_articles[:3]:
                logger.info(f"  - Article {article.article_number}: {article.content[:50]}...")
            
            return all_articles[:5]  # Retourner les 5 plus pertinents
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'articles: {e}")
            return []
    
    def _search_by_article_number(self, question: str) -> List[ConstitutionArticle]:
        """Recherche directe par numéro d'article"""
        try:
            import re
            # Rechercher les patterns: "article 22", "l'article 26", "article 44 parle"
            patterns = [
                r'article\s+(\d+)',
                r"l'article\s+(\d+)",
                r'articles?\s+(\d+)',
                r'(\d+)'
            ]
            
            article_numbers = []
            for pattern in patterns:
                matches = re.findall(pattern, question.lower())
                article_numbers.extend(matches)
            
            if article_numbers:
                # Nettoyer et dédupliquer les numéros
                article_numbers = list(set([num.strip() for num in article_numbers if num.strip().isdigit()]))
                logger.info(f"Numéros d'articles détectés: {article_numbers}")
                
                if article_numbers:
                    articles = self.db.query(ConstitutionArticle).filter(
                        and_(
                            ConstitutionArticle.article_number.in_(article_numbers),
                            ConstitutionArticle.is_active == True
                        )
                    ).all()
                    
                    if articles:
                        logger.info(f"Articles trouvés par numéro: {[a.article_number for a in articles]}")
                        return articles
            
            return []
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche par numéro d'article: {e}")
            return []
    
    def _search_general_articles(self, question: str) -> List[ConstitutionArticle]:
        """Recherche générale dans tous les articles"""
        try:
            all_articles = self.db.query(ConstitutionArticle).filter(
                ConstitutionArticle.is_active == True
            ).all()
            
            # Calculer la pertinence pour tous les articles
            scored_articles = []
            for article in all_articles:
                score = self._calculate_relevance_score(article, question)
                if score > 0:  # Seulement les articles avec un score positif
                    scored_articles.append((article, score))
            
            # Trier par score et retourner les meilleurs
            scored_articles.sort(key=lambda x: x[1], reverse=True)
            return [article for article, score in scored_articles[:5]]
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche générale: {e}")
            return []
    
    def _search_by_keywords(self, keywords: List[str]) -> List[ConstitutionArticle]:
        """Recherche par mots-clés dans la table ConstitutionKeyword"""
        try:
            return self.db.query(ConstitutionArticle).join(
                ConstitutionKeyword,
                ConstitutionArticle.article_number == ConstitutionKeyword.article_id
            ).filter(
                and_(
                    ConstitutionKeyword.keyword.in_(keywords),
                    ConstitutionArticle.is_active == True
                )
            ).order_by(
                ConstitutionKeyword.importance_score.desc()
            ).limit(5).all()
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche par mots-clés: {e}")
            return []
    
    def _search_by_content(self, keywords: List[str]) -> List[ConstitutionArticle]:
        """Recherche par contenu textuel"""
        try:
            content_articles = []
            for keyword in keywords[:3]:
                articles = self.db.query(ConstitutionArticle).filter(
                    and_(
                        ConstitutionArticle.content.ilike(f'%{keyword}%'),
                        ConstitutionArticle.is_active == True
                    )
                ).limit(3).all()
                content_articles.extend(articles)
            return content_articles
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche par contenu: {e}")
            return []
    
    def _search_by_synonyms(self, question_lower: str) -> List[ConstitutionArticle]:
        """Recherche par synonymes et mots liés"""
        try:
            synonym_articles = []
            
            # Mots liés pour les questions sur les enfants
            if any(word in question_lower for word in ['enfant', 'jeune', 'école', 'éducation']):
                child_related_words = ['enfant', 'jeune', 'école', 'éducation', 'enseignement', 'scolaire', 'formation']
                for word in child_related_words:
                    articles = self.db.query(ConstitutionArticle).filter(
                        and_(
                            ConstitutionArticle.content.ilike(f'%{word}%'),
                            ConstitutionArticle.is_active == True
                        )
                    ).limit(2).all()
                    synonym_articles.extend(articles)
            
            return synonym_articles
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche par synonymes: {e}")
            return []
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """
        Extrait les mots-clés pertinents de la question avec expansion sémantique - AMÉLIORÉ
        """
        # Mots-clés importants de la constitution avec leurs synonymes - ÉTENDU
        keyword_mapping = {
            'droit': ['droit', 'droits', 'garantie', 'garanties', 'protection', 'fondamental'],
            'liberté': ['liberté', 'libertés', 'libre', 'expression', 'conscience', 'opinion'],
            'président': ['président', 'présidence', 'chef', 'dirigeant', 'élection présidentielle', 'mandat présidentiel'],
            'gouvernement': ['gouvernement', 'ministre', 'ministère', 'exécutif', 'formation gouvernement', 'premier ministre'],
            'parlement': ['parlement', 'assemblée', 'député', 'sénateur', 'législatif', 'assemblée nationale', 'sénat'],
            'tribunal': ['tribunal', 'cour', 'justice', 'judiciaire', 'constitutionnelle', 'suprême'],
            'élection': ['élection', 'électoral', 'vote', 'voter', 'scrutin', 'électeur', 'suffrage'],
            'citoyen': ['citoyen', 'citoyenne', 'citoyens', 'nationalité', 'peuple', 'national'],
            'république': ['république', 'républicain', 'état', 'nation'],
            'constitution': ['constitution', 'constitutionnel', 'révision', 'amendement'],
            'pouvoir': ['pouvoir', 'pouvoirs', 'autorité', 'compétence', 'prérogative'],
            'institution': ['institution', 'institutions', 'organe', 'structure', 'organisme'],
            'responsabilité': ['responsabilité', 'responsable', 'devoir', 'obligation'],
            'mandat': ['mandat', 'durée', 'période', 'exercice', 'sept ans'],
            'session': ['session', 'séance', 'réunion', 'débat', 'parlementaire'],
            'article': ['article', 'articles'],
            'chapitre': ['chapitre', 'chapitres'],
            'section': ['section', 'sections'],
            'titre': ['titre', 'titres'],
            # Mots-clés spécifiques pour les enfants et l'éducation
            'enfant': ['enfant', 'enfants', 'jeune', 'jeunes', 'mineur', 'mineurs', 'scolarité', 'école', 'éducation'],
            'éducation': ['éducation', 'enseignement', 'école', 'scolaire', 'formation', 'apprentissage'],
            'protection': ['protection', 'protéger', 'sécurité', 'bien-être', 'sauvegarde'],
            'famille': ['famille', 'parent', 'parents', 'maternité', 'paternité', 'mariage'],
            'santé': ['santé', 'médical', 'soin', 'soins', 'hôpital', 'médicale'],
            'travail': ['travail', 'emploi', 'profession', 'métier', 'carrière', 'rémunération'],
            'économie': ['économie', 'économique', 'financier', 'budget', 'argent', 'fiscal'],
            'sécurité': ['sécurité', 'défense', 'armée', 'police', 'ordre', 'militaire'],
            'culture': ['culture', 'culturel', 'art', 'artistique', 'patrimoine'],
            'environnement': ['environnement', 'écologie', 'nature', 'pollution', 'écologique'],
            # Nouveaux mots-clés pour améliorer la précision
            'asile': ['asile', 'réfugié', 'persécution', 'protection internationale'],
            'propriété': ['propriété', 'propriétaire', 'bien', 'domaine', 'expropriation'],
            'logement': ['logement', 'habitation', 'domicile', 'résidence', 'habitat'],
            'religion': ['religion', 'religieux', 'culte', 'croyance', 'confession'],
            'révision': ['révision', 'modifier', 'changer', 'amender', 'réviser'],
            'promulgation': ['promulgation', 'promulguer', 'publication', 'entrée en vigueur'],
            'haute trahison': ['haute trahison', 'trahison', 'traître', 'trahison nationale'],
            'état d\'urgence': ['état d\'urgence', 'urgence', 'crise', 'exceptionnel', 'siège'],
            'dissolution': ['dissolution', 'dissoudre', 'dissous', 'dissoudre assemblée'],
            'obligation': ['obligation', 'obligatoire', 'devoir', 'contrainte', 'forcé'],
            'participation': ['participation', 'participer', 'engagement', 'implication'],
            'contrôle': ['contrôle', 'surveillance', 'vérification', 'inspection'],
            'indépendance': ['indépendance', 'indépendant', 'autonomie', 'séparation'],
            'transparence': ['transparence', 'transparent', 'public', 'ouvert'],
            'égalité': ['égalité', 'égal', 'équité', 'juste', 'équitable'],
            'dignité': ['dignité', 'respect', 'honneur', 'considération'],
            'intégrité': ['intégrité', 'intègre', 'honnête', 'probité'],
            'souveraineté': ['souveraineté', 'souverain', 'indépendant', 'autonome'],
            'démocratie': ['démocratie', 'démocratique', 'populaire', 'républicain'],
            'territoire': ['territoire', 'territorial', 'national', 'pays'],
            'langue': ['langue', 'linguistique', 'français', 'nationale'],
            'diversité': ['diversité', 'divers', 'variété', 'pluralisme'],
            'tolérance': ['tolérance', 'tolérant', 'acceptation', 'respect'],
            'paix': ['paix', 'pacifique', 'harmonie', 'conciliation'],
            'développement': ['développement', 'développer', 'progrès', 'croissance'],
            'bien-être': ['bien-être', 'bienêtre', 'santé', 'bonheur'],
            'solidarité': ['solidarité', 'solidaire', 'entraide', 'coopération'],
            'justice': ['justice', 'juste', 'équité', 'équitable'],
            'ordre': ['ordre', 'organisation', 'structure', 'discipline'],
            'stabilité': ['stabilité', 'stable', 'équilibre', 'équilibré']
        }
        
        question_lower = question.lower()
        keywords = []
        
        # Extraire les mots-clés avec expansion sémantique
        for main_keyword, synonyms in keyword_mapping.items():
            for synonym in synonyms:
                if synonym in question_lower:
                    keywords.append(main_keyword)
                    break
        
        # Ajouter les mots-clés contextuels basés sur la question
        context_keywords = self._extract_context_keywords(question_lower)
        keywords.extend(context_keywords)
        
        # Ajouter les mots de la question qui contiennent des chiffres (articles)
        import re
        article_numbers = re.findall(r'\d+', question)
        keywords.extend(article_numbers)
        
        # Si aucun mot-clé trouvé, essayer une recherche plus large
        if not keywords:
            # Mots communs qui pourraient indiquer le sujet
            general_words = ['que', 'quoi', 'comment', 'pourquoi', 'quand', 'où', 'qui', 'dis', 'dit', 'disent']
            for word in general_words:
                if word in question_lower:
                    # Recherche plus large dans tous les articles
                    keywords.append('général')
                    break
        
        return list(set(keywords))  # Dédupliquer
    
    def _extract_context_keywords(self, question_lower: str) -> List[str]:
        """
        Extrait des mots-clés contextuels basés sur le type de question
        """
        context_keywords = []
        
        # Détecter le type de question
        if any(word in question_lower for word in ['comment', 'comment se', 'comment sont', 'comment peut']):
            context_keywords.extend(['procédure', 'méthode', 'processus'])
        
        if any(word in question_lower for word in ['quand', 'quand peut', 'quand doit']):
            context_keywords.extend(['condition', 'moment', 'circonstance'])
        
        if any(word in question_lower for word in ['qui', 'qui peut', 'qui doit']):
            context_keywords.extend(['personne', 'autorité', 'responsable'])
        
        if any(word in question_lower for word in ['quoi', 'qu\'est-ce', 'définition']):
            context_keywords.extend(['définition', 'concept', 'principe'])
        
        if any(word in question_lower for word in ['pourquoi', 'raison', 'cause']):
            context_keywords.extend(['justification', 'motif', 'fondement'])
        
        if any(word in question_lower for word in ['obligation', 'obligatoire', 'devoir', 'contrainte']):
            context_keywords.extend(['obligation', 'devoir', 'responsabilité'])
        
        if any(word in question_lower for word in ['formation', 'former', 'créer', 'établir']):
            context_keywords.extend(['formation', 'création', 'établissement'])
        
        if any(word in question_lower for word in ['dissolution', 'dissoudre', 'dissous']):
            context_keywords.extend(['dissolution', 'fin', 'terminaison'])
        
        if any(word in question_lower for word in ['urgence', 'crise', 'exceptionnel']):
            context_keywords.extend(['urgence', 'exception', 'crise'])
        
        if any(word in question_lower for word in ['trahison', 'traître']):
            context_keywords.extend(['trahison', 'infraction', 'crime'])
        
        return context_keywords
    
    def _calculate_relevance_score(self, article: ConstitutionArticle, question: str) -> float:
        """
        Calcule un score de pertinence pour un article
        """
        score = 0.0
        question_lower = question.lower()
        content_lower = article.content.lower()
        
        # Score basé sur les mots-clés communs
        keywords = article.keywords.split(', ') if article.keywords else []
        for keyword in keywords:
            if keyword.lower() in question_lower:
                score += 2.0
        
        # Score basé sur le numéro d'article mentionné
        if article.article_number in question:
            score += 5.0
        
        # Score basé sur la catégorie
        if article.category and article.category.lower() in question_lower:
            score += 3.0
        
        # Score basé sur la longueur du contenu (préférer les articles détaillés)
        score += min(len(article.content) / 1000, 2.0)
        
        return score
    
    def _build_optimized_context(self, articles: List[ConstitutionArticle]) -> str:
        """
        Construit un contexte optimisé à partir des articles pertinents
        """
        if not articles:
            return "Aucun article pertinent trouvé dans la constitution."
        
        context_parts = []
        total_length = 0
        max_context_length = 4000  # Limite optimisée
        
        for article in articles:
            article_context = f"Article {article.article_number}"
            if article.title:
                article_context += f" - {article.title}"
            
            # Limiter la longueur du contenu de l'article
            content_preview = article.content[:800] + "..." if len(article.content) > 800 else article.content
            
            article_context += f":\n{content_preview}\n"
            
            if total_length + len(article_context) > max_context_length:
                break
            
            context_parts.append(article_context)
            total_length += len(article_context)
        
        return "\n".join(context_parts)
    
    def _build_conversation_messages(self, question: str, context: str, chat_history: List[Dict] = None) -> List[Dict]:
        """
        Construit les messages de conversation avec l'historique - OPTIMISÉ
        """
        messages = [
            {
                "role": "system",
                "content": """Tu es ConstitutionIA, un assistant spécialisé dans l'analyse de la constitution de la Guinée.

RÈGLES STRICTES:
1) Réponds UNIQUEMENT à partir du contenu fourni
2) Cite impérativement les articles avec leurs numéros
3) Sois PRÉCIS et CONCIS (maximum 200 mots)
4) Si l'information n'est pas dans le contexte, dis "Cette information n'est pas disponible dans la constitution"
5) Structure ta réponse avec des points clairs
6) Évite les répétitions et les phrases vagues

FORMAT DE RÉPONSE:
- Article X: [résumé concis]
- Article Y: [résumé concis]
- [conclusion brève si nécessaire]

TON STYLE: Amical, professionnel, précis, avec citations exactes."""
            }
        ]
        
        # Ajouter l'historique de conversation (limité à 4 derniers messages)
        if chat_history:
            recent_history = chat_history[-4:]
            for msg in recent_history:
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg.get('content', '')
                    })
        
        # Ajouter le contexte et la question actuelle
        messages.append({
            "role": "user",
            "content": f"Contexte de la constitution:\n{context}\n\nQuestion: {question}"
        })
        
        return messages
    
    def _call_openai_api(self, messages: List[Dict]) -> str:
        """
        Appel optimisé à l'API OpenAI - PERFORMANCE AMÉLIORÉE
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,  # Réduit pour des réponses plus concises
            temperature=0.3,  # Plus déterministe pour la précision
            presence_penalty=0.0,  # Supprimé pour éviter la répétition
            frequency_penalty=0.0,  # Supprimé pour éviter la répétition
            timeout=10  # Timeout pour éviter les attentes longues
        )
        
        return response.choices[0].message.content.strip()
    
    def _save_response_cache(self, question: str, response: str, articles: List[ConstitutionArticle]):
        """
        Sauvegarde la réponse dans le cache
        """
        try:
            question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
            
            # Références aux articles cités
            article_refs = [f"Article {art.article_number}" for art in articles]
            
            # Expiration dans 24 heures
            expires_at = datetime.now() + timedelta(hours=24)
            
            cache_entry = ConstitutionCache(
                question_hash=question_hash,
                question=question,
                response=response,
                article_references=', '.join(article_refs),
                expires_at=expires_at
            )
            
            self.db.add(cache_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
            self.db.rollback()
    
    def get_constitution_context(self) -> str:
        """
        Récupère le contexte de la constitution avec cache
        """
        current_time = time.time()
        
        # Vérifier si le cache est valide
        if (self._constitution_cache is None or 
            self._cache_timestamp is None or 
            current_time - self._cache_timestamp > self._cache_duration):
            
            # Récupérer le contenu depuis la base de données
            articles = self.db.query(ConstitutionArticle).filter(
                ConstitutionArticle.is_active == True
            ).all()
            
            # Construire le contexte
            context_parts = []
            for article in articles[:20]:  # Limiter aux 20 premiers articles
                context_parts.append(f"Article {article.article_number}: {article.content[:200]}...")
            
            self._constitution_cache = "\n\n".join(context_parts)
            self._cache_timestamp = current_time
            
            logger.info("Cache de constitution mis à jour")
        
        return self._constitution_cache
    
    def get_conversation_suggestions(self, constitution_title: str) -> List[str]:
        """
        Génère des suggestions de questions optimisées
        """
        suggestions = [
            "Peux-tu m'expliquer les principes fondamentaux de cette constitution ?",
            "Quels sont les droits et devoirs des citoyens ?",
            "Comment fonctionne le pouvoir exécutif ?",
            "Quelle est la durée du mandat présidentiel ?",
            "Comment sont organisées les élections ?",
            "Quels sont les pouvoirs du Parlement ?",
            "Comment fonctionne le système judiciaire ?",
            "Quels sont les mécanismes de protection des droits ?",
            "Comment peut-on modifier cette constitution ?",
            "Quels sont les principes de la séparation des pouvoirs ?"
        ]
        return suggestions
    
    def get_welcome_message(self, constitution_title: str) -> str:
        """
        Génère un message de bienvenue optimisé
        """
        return f"""👋 Bienvenue dans ChatNow optimisé !

Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse de la constitution : **{constitution_title}**

💡 **Comment puis-je vous aider ?**
• Posez des questions sur le contenu de la constitution
• Demandez des explications sur les principes constitutionnels
• Interrogez-moi sur les droits et devoirs des citoyens
• Explorez le fonctionnement des institutions

🎯 **Exemples de questions :**
• "Que dit la constitution sur les droits des citoyens ?"
• "Comment fonctionne le pouvoir judiciaire ?"
• "Quelle est la durée du mandat présidentiel ?"

⚡ **Nouveau :** Réponses optimisées avec cache et recherche intelligente !

Je suis là pour vous accompagner dans votre exploration de cette constitution ! 🚀"""

# Instance globale du service (sera initialisée avec la DB)
chatnow_service = None

def initialize_chatnow_service(db: Session):
    """Initialise le service ChatNow avec la base de données"""
    global chatnow_service
    chatnow_service = OptimizedChatNowService(db)
