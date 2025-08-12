import os
import time
import signal
import hashlib
import json
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.constitution import Constitution
import openai
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import numpy as np
import logging
from app.services.monitoring_service import monitoring_service
from app.core.config import settings
import random

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance singleton du service optimisé
_optimized_service_instance = None

def get_optimized_ai_service():
    """Retourne l'instance singleton du service IA optimisé"""
    global _optimized_service_instance
    if _optimized_service_instance is None:
        _optimized_service_instance = OptimizedAIService()
    return _optimized_service_instance

class OptimizedAIService:
    """
    Service IA optimisé avec cache, fallback intelligent et RAG simplifié
    Résout les problèmes de performance et de coûts
    """

    def __init__(self):
        # Charger la clé API depuis la configuration centralisée
        self.openai_api_key = settings.OPENAI_API_KEY
        if not self.openai_api_key:
            logger.error("❌ OPENAI_API_KEY non définie dans la configuration")
            raise ValueError("OPENAI_API_KEY environment variable not found.")

        logger.info(f"✅ Clé API chargée: {'OUI' if self.openai_api_key else 'NON'}")

        # Cache en mémoire pour les réponses
        self.response_cache = {}
        self.embedding_cache = {}

        # Mémoire de conversation améliorée pour multi-utilisateurs
        self.conversation_memory = {}
        self.max_conversation_history = 10
        self.session_timeout = 3600  # 1 heure pour les sessions guest
        self.session_timestamps = {}  # Pour nettoyer les sessions expirées

        # Configuration optimisée pour performance
        self.chunk_size = 2000  # Chunks plus gros
        self.chunk_overlap = 100  # Moins d'overlap
        self.max_chunks = 2  # Moins de chunks
        self.timeout_seconds = 5  # Timeout plus court

        # Seuils pour décider de la méthode
        self.simple_query_threshold = 3  # Mots pour requête simple
        self.cache_ttl = 3600  # 1 heure de cache

        # Types de questions avec détection améliorée
        self.question_types = {
            "identity": ["nom", "qui es-tu", "qui es tu", "ton nom", "appelle", "qui êtes-vous", "votre nom"],
            "politeness": ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye", "s'il vous plaît"],
            "constitutional": ["constitution", "article", "loi", "droit", "pouvoir", "président", "gouvernement", "république"],
            "comparison": ["différence", "comparer", "versus", "contrairement", "alors que", "contrairement à"],
            "analysis": ["analyser", "expliquer", "comment", "pourquoi", "qu'est-ce que", "définir"],
            "specific": ["durée", "mandat", "élection", "vote", "référendum", "procédure", "nombre de mandat", "combien de mandat"],
            "rights": ["droits", "libertés", "garanties", "protection", "citoyens", "individuels"],
            "institutions": ["parlement", "sénat", "assemblée", "conseil", "tribunal", "cour"],
            "correction": ["faux", "incorrect", "pas ça", "non", "erreur", "corrige", "c'est faux", "ce n'est pas ça"]
        }

        # Réponses pré-calculées pour questions fréquentes
        self.precomputed_responses = {
            "identity": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions de la Guinée. Je peux vous aider à trouver des informations dans les documents constitutionnels et répondre à vos questions sur le droit constitutionnel.",
            "politeness_hello": "Bonjour ! Comment puis-je vous aider avec la constitution de la Guinée ?",
            "politeness_thanks": "De rien ! N'hésitez pas si vous avez d'autres questions sur la constitution. Je suis là pour vous aider.",
            "error_timeout": "Désolé, la recherche prend trop de temps. Essayez une question plus spécifique.",
            "error_quota": "Désolé, le système IA est temporairement indisponible (quota OpenAI dépassé).",
            "not_found": "Je ne trouve pas cette information dans les documents disponibles. Pouvez-vous reformuler votre question ou poser une question différente sur la constitution ?"
        }

        # Initialiser les composants IA (lazy loading)
        self.embeddings = None
        self.llm = None
        self.vector_db = None
        self.qa_chain = None
        self.is_initialized = False
        
        # Chemin pour persister la base vectorielle
        self.vector_db_path = "vector_db_cache"

    def _get_cache_key(self, query: str) -> str:
        """Génère une clé de cache pour une requête"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def _get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Récupère une réponse du cache"""
        cache_key = self._get_cache_key(query)
        cached = self.response_cache.get(cache_key)

        if cached and time.time() - cached.get('timestamp', 0) < self.cache_ttl:
            logger.info(f"Cache hit pour: {query[:50]}...")
            # Incrémenter les hits
            if not hasattr(self, 'cache_hits'):
                self.cache_hits = 0
            self.cache_hits += 1
            return cached['response']

        # Incrémenter les misses
        if not hasattr(self, 'cache_misses'):
            self.cache_misses = 0
        self.cache_misses += 1
        return None

    def _cache_response(self, query: str, response: Dict[str, Any]):
        """Met en cache une réponse"""
        cache_key = self._get_cache_key(query)
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        logger.info(f"Réponse mise en cache: {query[:50]}...")

    def _is_simple_query(self, query: str) -> bool:
        """Détermine si une requête est simple (pas besoin de RAG)"""
        words = query.lower().split()

        # Questions d'identité ou de politesse
        if self._detect_question_type(query) in ["identity", "politeness"]:
            return True

        # Requêtes courtes
        if len(words) <= self.simple_query_threshold:
            return True

        # Questions basiques
        simple_keywords = ["qui", "quoi", "quand", "où", "comment", "pourquoi"]
        if any(word in words for word in simple_keywords) and len(words) <= 5:
            return True

        # Questions de définition simples
        definition_keywords = ["qu'est-ce que", "définir", "expliquer", "définition"]
        if any(keyword in query.lower() for keyword in definition_keywords) and len(words) <= 8:
            return True

        # Questions avec "constitution" mais courtes
        if "constitution" in query.lower() and len(words) <= 6:
            return True

        return False

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question avec améliorations"""
        query_lower = query.lower()

        # Vérifier d'abord les questions spécifiques pour éviter les faux positifs
        if any(keyword in query_lower for keyword in ["nombre de mandat", "combien de mandat", "durée", "élection", "vote", "référendum", "procédure"]):
            return "specific"
            
        # Vérifier les questions d'identité avec des mots plus précis
        if any(keyword in query_lower for keyword in ["qui es-tu", "qui es tu", "ton nom", "appelle", "qui êtes-vous", "votre nom"]):
            return "identity"
            
        # Vérifier les autres types
        for qtype, keywords in self.question_types.items():
            if qtype not in ["identity", "specific"]:  # Éviter les doublons
                if any(keyword in query_lower for keyword in keywords):
                    return qtype

        return "general"

    def _fast_keyword_search(self, query: str, constitutions: List[Constitution]) -> Dict[str, Any]:
        """Recherche rapide par mots-clés (fallback)"""
        start_time = time.time()

        if not constitutions:
            # Proposer une reformulation intelligente
            reformulation_suggestions = self._suggest_reformulation(query)
            return {
                "answer": f"Je ne trouve pas d'informations spécifiques pour '{query}'. {reformulation_suggestions['message']}",
                "confidence": 0.1,
                "sources": [],
                "search_time": time.time() - start_time,
                "method": "keyword_fallback",
                "suggestions": reformulation_suggestions['suggestions']
            }

        # Recherche simple par mots-clés
        query_words = set(query.lower().split())
        best_match = None
        best_score = 0

        for constitution in constitutions:
            if not constitution.content:
                continue

            content_lower = constitution.content.lower()
            score = 0

            # Score pour correspondance exacte
            if query.lower() in content_lower:
                score += 10

            # Score pour mots individuels
            for word in query_words:
                if word in content_lower:
                    score += 2

            if score > best_score:
                best_score = score
                best_match = constitution

        if best_match and best_score > 5:
            # Extraire un passage pertinent
            content_lower = best_match.content.lower()
            query_lower = query.lower()

            # Trouver le passage le plus pertinent
            start_pos = content_lower.find(query_lower)
            if start_pos == -1:
                # Chercher le premier mot
                words = query_lower.split()
                for word in words:
                    start_pos = content_lower.find(word)
                    if start_pos != -1:
                        break

            if start_pos != -1:
                # Extraire un passage autour de la correspondance
                start = max(0, start_pos - 200)
                end = min(len(best_match.content), start_pos + 600)
                passage = best_match.content[start:end]

                return {
                    "answer": f"Voici ce que j'ai trouvé dans {best_match.title}:\n\n{passage}\n\nCette information provient du document constitutionnel.",
                    "confidence": min(best_score / 20.0, 0.8),
                    "sources": [{"title": best_match.title, "content": passage[:200] + "..."}],
                    "search_time": time.time() - start_time,
                    "method": "keyword_search"
                }

        # Proposer une reformulation intelligente
        reformulation_suggestions = self._suggest_reformulation(query)
        return {
            "answer": f"Je ne trouve pas d'informations spécifiques pour '{query}'. {reformulation_suggestions['message']}",
            "confidence": 0.1,
            "sources": [],
            "search_time": time.time() - start_time,
            "method": "keyword_fallback",
            "suggestions": reformulation_suggestions['suggestions']
        }

    def _initialize_rag_lazy(self):
        """Initialise le RAG seulement si nécessaire (lazy loading)"""
        if self.is_initialized:
            logger.info("✅ RAG déjà initialisé")
            return True

        try:
            logger.info("🚀 Initialisation lazy du système RAG...")
            logger.info(f"📋 Clé API présente: {'OUI' if self.openai_api_key else 'NON'}")

            # Vérifier la clé API
            if not self.openai_api_key:
                logger.error("❌ OPENAI_API_KEY non définie")
                return False

            # Initialiser les composants seulement si nécessaire
            if not self.embeddings:
                logger.info("📡 Initialisation des embeddings...")
                try:
                    self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
                    logger.info("✅ Embeddings initialisés")
                except Exception as e:
                    logger.error(f"❌ Erreur embeddings: {e}")
                    return False

            if not self.llm:
                logger.info("🤖 Initialisation du LLM...")
                try:
                    self.llm = ChatOpenAI(
                        model_name="gpt-3.5-turbo", 
                        temperature=0.1,
                        openai_api_key=self.openai_api_key,
                        max_tokens=600  # Réduit pour plus de rapidité
                    )
                    logger.info("✅ LLM initialisé")
                except Exception as e:
                    logger.error(f"❌ Erreur LLM: {e}")
                    return False

            # Charger ou créer la base vectorielle
            if not self.vector_db:
                # Essayer de charger la base vectorielle persistante
                if self._load_vector_db_from_cache():
                    logger.info("✅ Base vectorielle chargée depuis le cache")
                else:
                    logger.info("📚 Création d'une nouvelle base vectorielle...")
                    pdf_docs = self._load_pdf_documents()
                    if not pdf_docs:
                        logger.warning("❌ Aucun document trouvé")
                        return False

                    logger.info(f"📄 {len(pdf_docs)} documents chargés")

                    # Découper avec paramètres optimisés
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                        length_function=len,
                        separators=["\n\n", "\n", ". ", " ", ""]
                    )
                    docs = text_splitter.split_documents(pdf_docs)
                    logger.info(f"📄 {len(docs)} chunks créés (optimisé)")

                    # Créer la base vectorielle
                    logger.info("🔍 Création de la base vectorielle FAISS...")
                    try:
                        self.vector_db = FAISS.from_documents(docs, self.embeddings)
                        logger.info("✅ Base vectorielle FAISS créée")
                        
                        # Sauvegarder la base vectorielle
                        self._save_vector_db_to_cache()
                        logger.info("💾 Base vectorielle sauvegardée")
                    except Exception as e:
                        logger.error(f"❌ Erreur FAISS: {e}")
                        return False

                # Créer la chaîne RAG optimisée
                custom_prompt = PromptTemplate(
                    input_variables=["context", "question"],
                    template="""Tu es ConstitutionIA, assistant spécialisé dans l'analyse des constitutions de la Guinée.

CONTEXTE:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Réponds UNIQUEMENT basé sur le contexte fourni
2. Cite spécifiquement les articles pertinents
3. Sois concis (max 200 mots)
4. Si l'information n'est pas dans le contexte, dis-le clairement
5. Utilise un langage juridique accessible

RÉPONSE:"""
                )

                try:
                    self.qa_chain = RetrievalQA.from_chain_type(
                        llm=self.llm,
                        chain_type="stuff",
                        retriever=self.vector_db.as_retriever(
                            search_type="similarity", 
                            search_kwargs={"k": self.max_chunks}
                        ),
                        return_source_documents=True,
                        chain_type_kwargs={"prompt": custom_prompt}
                    )
                    logger.info("✅ Chaîne RAG créée")
                except Exception as e:
                    logger.error(f"❌ Erreur chaîne RAG: {e}")
                    return False

            self.is_initialized = True
            logger.info("✅ Système RAG optimisé initialisé!")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation RAG: {str(e)}")
            logger.error(f"❌ Type d'erreur: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _load_pdf_documents(self, folder_path: str = "Fichier/") -> List:
        """Charge les documents depuis la base de données au lieu des fichiers PDF"""
        from app.database import SessionLocal
        from app.models.constitution import Constitution
        from app.models.pdf_import import Article
        from langchain.schema import Document
        
        documents = []
        db = SessionLocal()
        
        try:
            logger.info("📚 Chargement des documents depuis la base de données...")
            
            # Récupérer toutes les constitutions avec leurs articles
            constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
            
            if not constitutions:
                logger.warning("❌ Aucune constitution active trouvée en base de données")
                return documents
            
            logger.info(f"📋 {len(constitutions)} constitutions trouvées")
            
            for constitution in constitutions:
                # Récupérer tous les articles de cette constitution
                articles = db.query(Article).filter(Article.constitution_id == constitution.id).all()
                
                if not articles:
                    logger.info(f"📄 Constitution '{constitution.title}' - Aucun article trouvé")
                    continue
                
                logger.info(f"📄 Constitution '{constitution.title}' - {len(articles)} articles")
                
                # Créer des documents LangChain à partir des articles
                for article in articles:
                    if not article.content or len(article.content.strip()) < 10:
                        continue  # Ignorer les articles vides ou trop courts
                    
                    # Créer le contenu du document
                    content = f"Article {article.article_number}"
                    if article.title:
                        content += f": {article.title}\n\n"
                    else:
                        content += "\n\n"
                    content += article.content
                    
                    # Créer le document LangChain
                    doc = Document(
                        page_content=content,
                        metadata={
                            'source': constitution.filename,
                            'constitution_id': constitution.id,
                            'constitution_title': constitution.title,
                            'article_number': article.article_number,
                            'article_title': article.title,
                            'part': article.part,
                            'section': article.section,
                            'page_number': article.page_number,
                            'file_path': f"db://constitution_{constitution.id}/article_{article.id}"
                        }
                    )
                    documents.append(doc)
            
            logger.info(f"✅ {len(documents)} documents créés depuis la base de données")
            
            # Si aucun document n'a été créé, essayer de charger depuis les fichiers PDF comme fallback
            if not documents:
                logger.warning("⚠️ Aucun document créé depuis la base, tentative de chargement depuis les fichiers PDF...")
                documents = self._load_pdf_documents_fallback(folder_path)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement depuis la base de données: {str(e)}")
            logger.warning("⚠️ Fallback vers le chargement depuis les fichiers PDF...")
            return self._load_pdf_documents_fallback(folder_path)
        finally:
            db.close()

    def _load_pdf_documents_fallback(self, folder_path: str = "Fichier/") -> List:
        """Méthode de fallback pour charger depuis les fichiers PDF (ancienne méthode)"""
        documents = []

        logger.info(f"📁 Chargement de fallback depuis le dossier: {folder_path}")
        if not os.path.exists(folder_path):
            logger.warning(f"❌ Le dossier {folder_path} n'existe pas.")
            return documents

        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        logger.info(f"📄 Fichiers PDF trouvés: {pdf_files}")

        for filename in pdf_files:
            try:
                file_path = os.path.join(folder_path, filename)
                logger.info(f"📖 Chargement de: {filename}")
                
                loader = PyPDFLoader(file_path)
                docs = loader.load()

                # Améliorer les métadonnées
                for doc in docs:
                    doc.metadata['source'] = filename
                    doc.metadata['file_path'] = file_path

                documents.extend(docs)
                logger.info(f"✅ {filename} chargé: {len(docs)} pages")

            except Exception as e:
                logger.error(f"❌ Erreur lors du chargement de {filename}: {str(e)}")
                continue

        logger.info(f"📚 Total fallback: {len(documents)} documents chargés")
        return documents

    def _save_vector_db_to_cache(self):
        """Sauvegarde la base vectorielle dans le cache"""
        try:
            if self.vector_db and os.path.exists(self.vector_db_path):
                import shutil
                shutil.rmtree(self.vector_db_path)
            
            if self.vector_db:
                self.vector_db.save_local(self.vector_db_path)
                logger.info(f"💾 Base vectorielle sauvegardée dans {self.vector_db_path}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la base vectorielle: {e}")

    def _load_vector_db_from_cache(self):
        """Charge la base vectorielle depuis le cache"""
        try:
            if os.path.exists(self.vector_db_path) and self.embeddings:
                self.vector_db = FAISS.load_local(self.vector_db_path, self.embeddings)
                logger.info(f"📂 Base vectorielle chargée depuis {self.vector_db_path}")
                return True
            else:
                logger.info("📂 Aucune base vectorielle en cache trouvée")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de la base vectorielle: {e}")
            return False

    def refresh_vector_db(self):
        """Force le rafraîchissement de la base vectorielle"""
        try:
            logger.info("🔄 Rafraîchissement de la base vectorielle...")
            
            # Supprimer l'ancienne base vectorielle
            if os.path.exists(self.vector_db_path):
                import shutil
                shutil.rmtree(self.vector_db_path)
                logger.info("🗑️ Ancienne base vectorielle supprimée")
            
            # Réinitialiser les composants
            self.vector_db = None
            self.qa_chain = None
            self.is_initialized = False
            
            # Recréer la base vectorielle
            success = self._initialize_rag_lazy()
            if success:
                logger.info("✅ Base vectorielle rafraîchie avec succès")
            else:
                logger.error("❌ Échec du rafraîchissement de la base vectorielle")
            
            return success
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement: {e}")
            return False

    def _rag_search_optimized(self, query: str) -> Dict[str, Any]:
        """Recherche RAG optimisée avec timeout et gestion d'erreurs"""
        logger.info(f"🔍 Vérification RAG - is_initialized: {self.is_initialized}")
        logger.info(f"🔍 État des composants RAG:")
        logger.info(f"   - embeddings: {self.embeddings is not None}")
        logger.info(f"   - llm: {self.llm is not None}")
        logger.info(f"   - vector_db: {self.vector_db is not None}")
        logger.info(f"   - qa_chain: {self.qa_chain is not None}")
        
        if not self.is_initialized:
            logger.warning("❌ RAG non initialisé - tentative d'initialisation...")
            init_success = self._initialize_rag_lazy()
            logger.info(f"🔄 Résultat initialisation: {init_success}")
            
            if not init_success:
                return {
                    "answer": "Système RAG non disponible. Utilisation du mode fallback.",
                    "sources": [],
                    "confidence": 0.0,
                    "method": "rag_unavailable"
                }

        try:
            # Timeout avec gestion d'erreurs
            def timeout_handler(signum, frame):
                raise TimeoutError("Recherche RAG trop lente")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)

            try:
                response = self.qa_chain.invoke({"query": query})  # Utiliser invoke au lieu de __call__
                signal.alarm(0)  # Annuler le timeout

                # Extraire les sources avec plus de détails
                sources = []
                for doc in response['source_documents']:
                    sources.append({
                        "title": doc.metadata.get('source', 'Document'),
                        "content": doc.page_content[:200] + "...",
                        "page": doc.metadata.get('page', 'N/A')
                    })

                # Calculer la confiance basée sur la qualité de la réponse
                confidence = 0.8 if len(response['result']) > 30 else 0.5

                return {
                    "answer": response['result'],
                    "sources": sources,
                    "confidence": confidence,
                    "method": "rag_search"
                }

            except TimeoutError:
                signal.alarm(0)
                return {
                    "answer": self.precomputed_responses["error_timeout"],
                    "sources": [],
                    "confidence": 0.0,
                    "method": "rag_timeout"
                }

        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                return {
                    "answer": self.precomputed_responses["error_quota"],
                    "sources": [],
                    "confidence": 0.0,
                    "method": "rag_quota_error"
                }
            else:
                return {
                    "answer": f"Erreur lors de la recherche: {error_msg}",
                    "sources": [],
                    "confidence": 0.0,
                    "method": "rag_error"
                }

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None, user_id: str = "default", session_id: str = None) -> Dict[str, Any]:
        """
        Génère une réponse intelligente avec mémoire de conversation multi-utilisateurs
        """
        start_time = time.time()
        
        # Générer un ID utilisateur unique
        unique_user_id = self._generate_user_id(user_id, session_id)
        
        # Ajouter la requête à l'historique
        self._add_to_conversation(unique_user_id, "user", query)
        
        # Détecter si c'est une correction
        is_correction = self._detect_correction(query)
        
        # Récupérer le contexte de la conversation
        conversation_context = self._get_context_from_history(unique_user_id)
        
        # Si c'est une correction, utiliser un prompt spécial
        if is_correction and conversation_context:
            response = self._handle_correction(query, conversation_context, constitutions)
        else:
            # Logique normale pour les nouvelles questions avec contexte
            response = self._generate_normal_response_with_context(query, constitutions, context, conversation_context, unique_user_id)
        
        # Ajouter la réponse à l'historique
        self._add_to_conversation(unique_user_id, "assistant", response.get("answer", ""))
        
        # Ajouter les métadonnées de performance
        response["search_time"] = time.time() - start_time
        response["is_correction"] = is_correction
        response["user_session"] = {
            "user_id": unique_user_id,
            "is_authenticated": user_id != "default",
            "is_guest": session_id is not None
        }
        
        return response

    def _generate_normal_response_with_context(self, query: str, constitutions: List[Constitution], context: str = None, conversation_context: str = "", user_id: str = "default") -> Dict[str, Any]:
        """Génère une réponse normale en tenant compte du contexte de conversation"""
        # Vérifier le cache d'abord
        cached_response = self._get_cached_response(query)
        if cached_response:
            logger.info(f"Cache hit pour: {query}...")
            return cached_response

        # Détecter le type de question
        question_type = self._detect_question_type(query)
        
        # Réponses pré-calculées pour questions simples
        if question_type in ["identity", "politeness"]:
            response = self._handle_simple_question(query, question_type)
            self._cache_response(query, response)
            return response

        # Si il y a un contexte de conversation, l'utiliser pour améliorer la réponse
        if conversation_context and len(conversation_context) > 50:
            response = self._generate_contextual_response(query, constitutions, conversation_context, question_type)
            if response:
                self._cache_response(query, response)
                return response

        # Recherche RAG optimisée
        try:
            rag_response = self._rag_search_optimized(query)
            if rag_response and rag_response.get("answer"):
                # S'assurer que les suggestions sont présentes
                if "suggestions" not in rag_response:
                    rag_response["suggestions"] = self._generate_suggestions(query, question_type)
                self._cache_response(query, rag_response)
                return rag_response
        except Exception as e:
            logger.error(f"Erreur RAG: {e}")

        # Fallback avec recherche par mots-clés
        keyword_response = self._fast_keyword_search(query, constitutions)
        # S'assurer que les suggestions sont présentes
        if "suggestions" not in keyword_response:
            keyword_response["suggestions"] = self._generate_suggestions(query, question_type)
        self._cache_response(query, keyword_response)
        return keyword_response

    def _generate_contextual_response(self, query: str, constitutions: List[Constitution], conversation_context: str, question_type: str) -> Optional[Dict[str, Any]]:
        """Génère une réponse contextuelle en utilisant l'historique de conversation"""
        try:
            # Utiliser GPT pour générer une réponse contextuelle
            contextual_prompt = f"""
            CONTEXTE DE LA CONVERSATION:
            {conversation_context}
            
            NOUVELLE QUESTION: "{query}"
            
            Tu es ConstitutionIA, un assistant spécialisé dans la constitution de la Guinée.
            
            INSTRUCTIONS:
            1. Analyse le contexte de la conversation
            2. Comprends la progression logique de la discussion
            3. Donne une réponse cohérente avec le sujet en cours
            4. Fais référence aux échanges précédents si pertinent
            5. Reste focalisé sur la constitution de la Guinée
            6. Cite des articles spécifiques si possible
            
            RÉPONSE CONTEXTUELLE:
            """
            
            if self.llm is None:
                self._initialize_rag_lazy()
            
            response = self.llm.predict(contextual_prompt)
            
            return {
                "answer": response,
                "method": "contextual_dialog",
                "confidence": 0.8,
                "sources": [],
                "suggestions": self._generate_suggestions(query, question_type)
            }
            
        except Exception as e:
            logger.error(f"Erreur dans la génération de réponse contextuelle: {e}")
            return None

    def _handle_correction(self, query: str, conversation_context: str, constitutions: List[Constitution]) -> Dict[str, Any]:
        """Gère les corrections de l'utilisateur avec analyse contextuelle améliorée"""
        try:
            # Analyser le contexte pour comprendre ce qui doit être corrigé
            context_analysis = self._analyze_correction_context(query, conversation_context)
            
            # Utiliser GPT pour comprendre la correction avec contexte enrichi
            correction_prompt = f"""
            CONTEXTE DE LA CONVERSATION:
            {conversation_context}
            
            ANALYSE DU CONTEXTE:
            - Sujet principal: {context_analysis.get('main_topic', 'Non identifié')}
            - Dernière question: {context_analysis.get('last_question', 'Non identifié')}
            - Ma dernière réponse: {context_analysis.get('last_response', 'Non identifié')}
            - Type de correction: {context_analysis.get('correction_type', 'Général')}
            
            CORRECTION DE L'UTILISATEUR: "{query}"
            
            Tu es ConstitutionIA, un assistant spécialisé dans la constitution de la Guinée.
            L'utilisateur dit que ma réponse précédente est incorrecte.
            
            INSTRUCTIONS:
            1. Analyse ma réponse précédente dans le contexte
            2. Comprends ce que l'utilisateur veut corriger spécifiquement
            3. Donne une réponse plus précise et vérifiée
            4. Cite les articles spécifiques de la constitution si possible
            5. Sois humble et reconnais si tu as fait une erreur
            6. Reste cohérent avec le sujet de la conversation
            7. Si tu n'es pas sûr, demande des clarifications
            
            RÉPONSE CORRIGÉE:
            """
            
            # Utiliser le LLM pour générer une réponse corrigée
            if self.llm is None:
                self._initialize_rag_lazy()
            
            response = self.llm.predict(correction_prompt)
            
            return {
                "answer": response,
                "method": "correction_dialog",
                "confidence": 0.8,
                "sources": [],
                "context_analysis": context_analysis,
                "suggestions": [
                    "Pouvez-vous me donner plus de détails sur ce qui était incorrect ?",
                    "Voulez-vous que je vérifie un aspect spécifique ?",
                    "Avez-vous une source différente à me proposer ?"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la correction: {e}")
            return {
                "answer": "Je comprends que ma réponse précédente n'était pas correcte. Pouvez-vous me donner plus de détails sur ce que vous voulez que je corrige ?",
                "method": "correction_fallback",
                "confidence": 0.5,
                "sources": [],
                "suggestions": [
                    "Pouvez-vous préciser ce qui était faux ?",
                    "Avez-vous une information différente ?",
                    "Voulez-vous que je recherche autre chose ?"
                ]
            }

    def _analyze_correction_context(self, query: str, conversation_context: str) -> Dict[str, str]:
        """Analyse le contexte pour comprendre la correction"""
        analysis = {
            "main_topic": "Non identifié",
            "last_question": "Non identifié", 
            "last_response": "Non identifié",
            "correction_type": "Général"
        }
        
        try:
            # Extraire les informations du contexte
            lines = conversation_context.split('\n')
            user_messages = []
            assistant_messages = []
            
            for line in lines:
                if line.startswith("Utilisateur:"):
                    user_messages.append(line.replace("Utilisateur:", "").strip())
                elif line.startswith("Assistant:"):
                    assistant_messages.append(line.replace("Assistant:", "").strip())
            
            # Identifier le sujet principal
            all_text = conversation_context.lower()
            topics = {
                "mandat présidentiel": ["mandat", "président", "élection", "durée"],
                "droits constitutionnels": ["droits", "libertés", "citoyens"],
                "institutions": ["gouvernement", "parlement", "cour"],
                "procédures": ["procédure", "vote", "référendum"],
                "articles constitutionnels": ["article", "constitution", "loi"]
            }
            
            for topic, keywords in topics.items():
                if any(keyword in all_text for keyword in keywords):
                    analysis["main_topic"] = topic
                    break
            
            # Identifier la dernière question et réponse
            if user_messages:
                analysis["last_question"] = user_messages[-1]
            if assistant_messages:
                analysis["last_response"] = assistant_messages[-1]
            
            # Identifier le type de correction
            query_lower = query.lower()
            if "faux" in query_lower or "incorrect" in query_lower:
                analysis["correction_type"] = "Information incorrecte"
            elif "pas ça" in query_lower or "non" in query_lower:
                analysis["correction_type"] = "Réponse inappropriée"
            elif "erreur" in query_lower:
                analysis["correction_type"] = "Erreur technique"
            else:
                analysis["correction_type"] = "Clarification demandée"
                
        except Exception as e:
            logger.error(f"Erreur dans l'analyse du contexte: {e}")
        
        return analysis

    def _generate_normal_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse normale (logique existante)"""
        # Vérifier le cache d'abord
        cache_key = self._get_cache_key(query)
        cached_response = self._get_cached_response(query)
        if cached_response:
            logger.info(f"Cache hit pour: {query}...")
            return cached_response

        # Détecter le type de question
        question_type = self._detect_question_type(query)
        
        # Réponses pré-calculées pour questions simples
        if question_type in ["identity", "politeness"]:
            response = self._handle_simple_question(query, question_type)
            self._cache_response(query, response)
            return response

        # Forcer l'initialisation du RAG si pas encore fait
        if not self.is_initialized:
            logger.info("🔄 Initialisation forcée du RAG...")
            self._initialize_rag_lazy()

        # Recherche RAG optimisée
        try:
            rag_response = self._rag_search_optimized(query)
            if rag_response and rag_response.get("answer"):
                # S'assurer que les suggestions sont présentes
                if "suggestions" not in rag_response:
                    rag_response["suggestions"] = self._generate_suggestions(query, question_type)
                # S'assurer que le method est correctement défini
                if rag_response.get("method") == "rag_unavailable":
                    # Si RAG n'était pas disponible, utiliser le fallback
                    keyword_response = self._fast_keyword_search(query, constitutions)
                    if "suggestions" not in keyword_response:
                        keyword_response["suggestions"] = self._generate_suggestions(query, question_type)
                    self._cache_response(query, keyword_response)
                    return keyword_response
                else:
                    # RAG a fonctionné
                    self._cache_response(query, rag_response)
                    return rag_response
        except Exception as e:
            logger.error(f"Erreur RAG: {e}")

        # Fallback avec recherche par mots-clés
        keyword_response = self._fast_keyword_search(query, constitutions)
        # S'assurer que les suggestions sont présentes
        if "suggestions" not in keyword_response:
            keyword_response["suggestions"] = self._generate_suggestions(query, question_type)
        self._cache_response(query, keyword_response)
        return keyword_response

    def _generate_suggestions(self, query: str, question_type: str) -> List[str]:
        """Génère des suggestions contextuelles optimisées"""
        if question_type == "constitutional":
            return [
                "Quels sont les droits fondamentaux garantis ?",
                "Comment est organisé le pouvoir exécutif ?",
                "Quelles sont les conditions d'élection du président ?",
                "Comment fonctionne le parlement ?"
            ]
        elif question_type == "rights":
            return [
                "Quels sont les droits des citoyens ?",
                "Comment sont protégées les libertés ?",
                "Quelles sont les garanties constitutionnelles ?",
                "Comment fonctionne la justice ?"
            ]
        elif question_type == "institutions":
            return [
                "Comment est organisé le gouvernement ?",
                "Quel est le rôle du président ?",
                "Comment fonctionne le système électoral ?",
                "Quelles sont les compétences du parlement ?"
            ]
        else:
            return [
                "Posez-moi une question sur la constitution",
                "Que voulez-vous savoir sur les droits fondamentaux ?",
                "Souhaitez-vous des informations sur le pouvoir exécutif ?",
                "Comment puis-je vous aider avec la constitution ?"
            ]

    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système IA optimisé"""
        return {
            "is_initialized": self.is_initialized,
            "rag_available": self.qa_chain is not None,
            "vector_db_available": self.vector_db is not None,
            "openai_configured": bool(self.openai_api_key),
            "cache_size": len(self.response_cache),
            "cache_hits": getattr(self, 'cache_hits', 0),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_chunks": self.max_chunks,
            "timeout_seconds": self.timeout_seconds,
            "simple_query_threshold": self.simple_query_threshold
        }

    def clear_cache(self):
        """Vide le cache"""
        self.response_cache.clear()
        self.embedding_cache.clear()
        logger.info("Cache vidé")

    def _suggest_reformulation(self, query: str) -> Dict[str, Any]:
        """Propose une reformulation intelligente de la question"""
        query_lower = query.lower()
        words = query_lower.split()
        
        # Analyser les mots-clés présents
        detected_keywords = []
        for word in words:
            if word in ["mandat", "mandats", "président", "présidence", "élection", "élections"]:
                detected_keywords.append("pouvoir_exécutif")
            elif word in ["droits", "droit", "libertés", "citoyens", "protection"]:
                detected_keywords.append("droits_fondamentaux")
            elif word in ["parlement", "assemblée", "sénat", "législatif"]:
                detected_keywords.append("pouvoir_législatif")
            elif word in ["constitution", "article", "loi"]:
                detected_keywords.append("constitution")
            elif word in ["nombre", "combien", "durée", "limite"]:
                detected_keywords.append("quantitatif")
        
        # Générer des suggestions basées sur les mots-clés détectés
        suggestions = []
        message = "Essayez de reformuler votre question avec plus de détails."
        
        if "pouvoir_exécutif" in detected_keywords:
            suggestions.extend([
                "Quel est le nombre de mandats présidentiels autorisés ?",
                "Combien de mandats peut exercer un président ?",
                "Quelle est la durée d'un mandat présidentiel ?",
                "Quelles sont les conditions de réélection du président ?"
            ])
            message = "Je peux vous aider avec les questions sur le pouvoir exécutif et la présidence."
            
        elif "droits_fondamentaux" in detected_keywords:
            suggestions.extend([
                "Quels sont les droits fondamentaux garantis ?",
                "Quels droits sont protégés par la constitution ?",
                "Comment sont protégés les droits des citoyens ?",
                "Quelles sont les libertés individuelles reconnues ?"
            ])
            message = "Je peux vous aider avec les questions sur les droits et libertés."
            
        elif "pouvoir_législatif" in detected_keywords:
            suggestions.extend([
                "Comment fonctionne le parlement ?",
                "Quelles sont les compétences de l'assemblée ?",
                "Comment sont élus les députés ?",
                "Quel est le rôle du pouvoir législatif ?"
            ])
            message = "Je peux vous aider avec les questions sur le pouvoir législatif."
            
        elif "constitution" in detected_keywords:
            suggestions.extend([
                "Quels sont les principes fondamentaux de la constitution ?",
                "Comment est organisée la constitution ?",
                "Quels sont les articles importants ?",
                "Quelle est la structure de la constitution ?"
            ])
            message = "Je peux vous aider avec les questions sur la constitution."
            
        elif "quantitatif" in detected_keywords:
            suggestions.extend([
                "Pouvez-vous préciser sur quoi porte votre question ?",
                "Souhaitez-vous des informations sur les mandats ?",
                "Voulez-vous connaître les durées ou limites ?",
                "Quel aspect quantitatif vous intéresse ?"
            ])
            message = "Pouvez-vous préciser votre question avec plus de contexte ?"
            
        else:
            # Suggestions générales si aucun mot-clé spécifique
            suggestions.extend([
                "Quels sont les droits fondamentaux garantis ?",
                "Comment est organisé le pouvoir exécutif ?",
                "Quelles sont les conditions d'élection du président ?",
                "Comment fonctionne le parlement ?",
                "Quels sont les principes de la constitution ?"
            ])
            message = "Essayez une de ces questions ou reformulez avec plus de détails."
        
        return {
            "message": message,
            "suggestions": suggestions
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "response_cache_size": len(self.response_cache),
            "embedding_cache_size": len(self.embedding_cache),
            "cache_ttl": self.cache_ttl,
            "cache_hits": getattr(self, 'cache_hits', 0),
            "cache_misses": getattr(self, 'cache_misses', 0)
        } 

    def _generate_user_id(self, user_id: str = None, session_id: str = None) -> str:
        """Génère un ID utilisateur unique basé sur l'authentification ou la session"""
        if user_id and user_id != "default":
            # Utilisateur authentifié
            return f"auth_{user_id}"
        elif session_id:
            # Utilisateur guest avec session
            return f"guest_{session_id}"
        else:
            # Session temporaire (fallback)
            return f"temp_{int(time.time())}"

    def _cleanup_expired_sessions(self):
        """Nettoie les sessions guest expirées"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, timestamp in self.session_timestamps.items():
            if current_time - timestamp > self.session_timeout:
                expired_sessions.append(session_id)
        
        # Supprimer les sessions expirées
        for session_id in expired_sessions:
            if session_id in self.conversation_memory:
                del self.conversation_memory[session_id]
            if session_id in self.session_timestamps:
                del self.session_timestamps[session_id]
        
        if expired_sessions:
            logger.info(f"Nettoyage de {len(expired_sessions)} sessions expirées")

    def _update_session_timestamp(self, user_id: str):
        """Met à jour le timestamp d'une session"""
        if user_id.startswith("guest_"):
            session_id = user_id.replace("guest_", "")
            self.session_timestamps[session_id] = time.time()

    def _get_conversation_history(self, user_id: str = "default") -> List[Dict]:
        """Récupère l'historique de conversation pour un utilisateur avec nettoyage"""
        # Nettoyer les sessions expirées périodiquement
        if random.random() < 0.1:  # 10% de chance de nettoyer
            self._cleanup_expired_sessions()
        
        return self.conversation_memory.get(user_id, [])

    def _add_to_conversation(self, user_id: str, role: str, content: str):
        """Ajoute un message à l'historique de conversation avec gestion de session"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        # Ajouter le message
        self.conversation_memory[user_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Garder seulement les derniers messages
        if len(self.conversation_memory[user_id]) > self.max_conversation_history:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-self.max_conversation_history:]
        
        # Mettre à jour le timestamp de session pour les guests
        self._update_session_timestamp(user_id)

    def _detect_correction(self, query: str) -> bool:
        """Détecte si l'utilisateur corrige une réponse précédente"""
        query_lower = query.lower().strip()
        correction_keywords = ["faux", "incorrect", "pas ça", "non", "erreur", "corrige", "c'est faux", "ce n'est pas ça"]
        return any(keyword in query_lower for keyword in correction_keywords)

    def _get_context_from_history(self, user_id: str = "default") -> str:
        """Récupère le contexte de la conversation précédente"""
        history = self._get_conversation_history(user_id)
        if len(history) < 2:
            return ""
        
        # Prendre les 4 derniers échanges (2 tours de conversation)
        recent_history = history[-8:]  # 4 échanges (user + assistant)
        context = "CONTEXTE DE LA CONVERSATION:\n"
        
        for i, msg in enumerate(recent_history):
            if msg["role"] == "user":
                context += f"Utilisateur: {msg['content']}\n"
            elif msg["role"] == "assistant":
                context += f"Assistant: {msg['content']}\n"
        
        # Ajouter un résumé du sujet principal
        main_topics = self._extract_main_topics(recent_history)
        if main_topics:
            context += f"\nSUJETS PRINCIPAUX: {', '.join(main_topics)}\n"
        
        return context

    def _extract_main_topics(self, history: List[Dict]) -> List[str]:
        """Extrait les sujets principaux de la conversation"""
        topics = []
        keywords = {
            "constitution": ["constitution", "article", "loi", "droit"],
            "mandat": ["mandat", "président", "élection", "durée"],
            "droits": ["droits", "libertés", "citoyens", "garanties"],
            "institutions": ["gouvernement", "parlement", "cour", "tribunal"],
            "procédure": ["procédure", "vote", "référendum", "élection"]
        }
        
        all_text = " ".join([msg["content"].lower() for msg in history])
        
        for topic, topic_keywords in keywords.items():
            if any(keyword in all_text for keyword in topic_keywords):
                topics.append(topic)
        
        return topics

    def _handle_simple_question(self, query: str, question_type: str) -> Dict[str, Any]:
        """Gère les questions simples (identité, politesse)"""
        query_lower = query.lower().strip()
        
        if question_type == "identity":
            return {
                "answer": self.precomputed_responses["identity"],
                "confidence": 1.0,
                "sources": [],
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"],
                "method": "precomputed"
            }
        
        if question_type == "politeness":
            if "merci" in query_lower:
                return {
                    "answer": self.precomputed_responses["politeness_thanks"],
                    "confidence": 1.0,
                    "sources": [],
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"],
                    "method": "precomputed"
                }
            else:
                return {
                    "answer": self.precomputed_responses["politeness_hello"],
                    "confidence": 1.0,
                    "sources": [],
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"],
                    "method": "precomputed"
                }
        
        return {
            "answer": "Comment puis-je vous aider avec la constitution de la Guinée ?",
            "confidence": 0.5,
            "sources": [],
            "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"],
            "method": "fallback"
        } 