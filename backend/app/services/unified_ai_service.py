import os
import time
import signal
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.constitution import Constitution
import openai
from openai import OpenAI
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

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedAIService:
    """
    Service IA unifié consolidant toutes les fonctionnalités IA
    avec système RAG complet et optimisations avancées
    """
    
    def __init__(self):
        # Charger la clé API
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found.")
        
        # Initialiser les composants IA
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo", 
            temperature=0.1,
            openai_api_key=self.openai_api_key,
            max_tokens=800  # Augmenté pour plus de contexte
        )
        
        # Système RAG
        self.vector_db = None
        self.qa_chain = None
        self.is_initialized = False
        
        # Configuration optimisée
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_chunks = 5  # Augmenté pour plus de contexte
        self.timeout_seconds = 8  # Augmenté pour les requêtes complexes
        
        # Types de questions avec détection améliorée
        self.question_types = {
            "identity": ["nom", "qui es-tu", "qui es tu", "ton nom", "appelle", "qui êtes-vous", "votre nom"],
            "politeness": ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye", "s'il vous plaît"],
            "constitutional": ["constitution", "article", "loi", "droit", "pouvoir", "président", "gouvernement", "république"],
            "comparison": ["différence", "comparer", "versus", "contrairement", "alors que", "contrairement à"],
            "analysis": ["analyser", "expliquer", "comment", "pourquoi", "qu'est-ce que", "définir"],
            "specific": ["durée", "mandat", "élection", "vote", "référendum", "procédure"],
            "rights": ["droits", "libertés", "garanties", "protection", "citoyens", "individuels"],
            "institutions": ["parlement", "sénat", "assemblée", "conseil", "tribunal", "cour"]
        }
        
        # Mapping de concepts juridiques
        self.legal_concepts = {
            "mandat": ["durée", "période", "élection", "renouvellement", "limite"],
            "droit": ["liberté", "garantie", "protection", "exercice", "respect"],
            "pouvoir": ["exécutif", "législatif", "judiciaire", "autorité", "compétence"],
            "citoyen": ["nationalité", "vote", "participation", "devoir", "électeur"],
            "justice": ["tribunal", "cour", "procédure", "jugement", "appel"],
            "élection": ["suffrage", "vote", "scrutin", "candidat", "campagne"]
        }

    def initialize(self) -> bool:
        """Initialise le système RAG complet"""
        logger.info("🚀 Initialisation du système RAG unifié...")
        
        try:
            # Charger les documents PDF
            pdf_docs = self._load_pdf_documents()
            
            if not pdf_docs:
                logger.warning("Aucun document PDF trouvé pour l'initialisation RAG")
                return False
            
            # Découper les documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            docs = text_splitter.split_documents(pdf_docs)
            logger.info(f"📄 {len(docs)} chunks créés (taille: {self.chunk_size}, overlap: {self.chunk_overlap})")
            
            # Créer la base vectorielle FAISS
            logger.info("🔧 Création de la base vectorielle FAISS...")
            self.vector_db = FAISS.from_documents(docs, self.embeddings)
            
            # Créer la chaîne RAG avec prompt optimisé
            custom_prompt = PromptTemplate(
                input_variables=["context", "question"],
                template="""Tu es ConstitutionIA, assistant spécialisé dans l'analyse des constitutions de la Guinée.

CONTEXTE:
{context}

QUESTION: {question}

INSTRUCTIONS STRICTES:
1. Réponds UNIQUEMENT basé sur le contexte fourni
2. Cite spécifiquement les articles et pages pertinents
3. Structure ta réponse clairement avec des points numérotés
4. Si l'information n'est pas dans le contexte, dis-le clairement
5. Utilise un langage juridique accessible mais précis
6. Sois concis mais complet (max 400 mots)
7. Mentionne la source du document quand c'est pertinent
8. Pour les questions de droit, cite les articles exacts

FORMAT DE RÉPONSE:
- Réponse structurée avec points numérotés
- Citations exactes des articles
- Explications claires et accessibles
- Sources mentionnées

RÉPONSE:"""
            )
            
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
            
            self.is_initialized = True
            logger.info("✅ Système RAG unifié initialisé avec succès!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation RAG: {e}")
            return False

    def _load_pdf_documents(self, folder_path: str = "Fichier/") -> List:
        """Charge les documents PDF avec gestion d'erreurs améliorée"""
        documents = []
        
        if not os.path.exists(folder_path):
            logger.warning(f"Le dossier {folder_path} n'existe pas.")
            return documents
        
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        
        for filename in pdf_files:
            try:
                loader = PyPDFLoader(os.path.join(folder_path, filename))
                docs = loader.load()
                
                # Améliorer les métadonnées
                for doc in docs:
                    doc.metadata['source'] = filename
                    doc.metadata['file_path'] = os.path.join(folder_path, filename)
                
                documents.extend(docs)
                logger.info(f"✅ Chargé: {filename} ({len(docs)} pages)")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors du chargement de {filename}: {e}")
        
        return documents

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question avec améliorations"""
        query_lower = query.lower()
        
        for qtype, keywords in self.question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return qtype
        
        return "general"

    def _rag_search(self, query: str) -> Dict[str, Any]:
        """Recherche RAG optimisée avec timeout et gestion d'erreurs"""
        if not self.is_initialized or not self.qa_chain:
            return {
                "answer": "Système RAG non disponible. Utilisation du mode fallback.",
                "sources": [],
                "confidence": 0.0
            }
        
        try:
            # Timeout avec gestion d'erreurs
            def timeout_handler(signum, frame):
                raise TimeoutError("Recherche RAG trop lente")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)
            
            try:
                response = self.qa_chain(query)
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
                confidence = 0.8 if len(response['result']) > 50 else 0.5
                
                return {
                    "answer": response['result'],
                    "sources": sources,
                    "confidence": confidence
                }
                
            except TimeoutError:
                signal.alarm(0)
                return {
                    "answer": "Désolé, la recherche prend trop de temps. Essayez une question plus spécifique.",
                    "sources": [],
                    "confidence": 0.0
                }
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                return {
                    "answer": "Désolé, le système IA est temporairement indisponible (quota OpenAI dépassé).",
                    "sources": [],
                    "confidence": 0.0
                }
            else:
                return {
                    "answer": f"Erreur lors de la recherche: {error_msg}",
                    "sources": [],
                    "confidence": 0.0
                }

    def _keyword_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par mots-clés améliorée avec scoring intelligent"""
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
                
                # Bonus pour les mots longs (plus spécifiques)
                for word in common_words:
                    if len(word) > 6:
                        score += 1.0
                
                # Bonus pour la proximité des mots
                if len(common_words) > 1:
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

    def _generate_fallback_response(self, query: str) -> str:
        """Génère une réponse de fallback optimisée"""
        try:
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es ConstitutionIA, assistant spécialisé dans les constitutions de la Guinée. Si tu ne trouves pas l'information demandée, guide poliment l'utilisateur vers des questions plus spécifiques sur la constitution."},
                    {"role": "user", "content": f"Question: {query}\n\nRéponse:"}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Je ne trouve pas cette information dans les documents disponibles. Pouvez-vous reformuler votre question ou poser une question différente sur la constitution ?"

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
        elif question_type == "comparison":
            return [
                "Voulez-vous comparer différentes versions ?",
                "Souhaitez-vous voir les évolutions ?",
                "Cherchez-vous les différences entre articles ?",
                "Voulez-vous analyser les changements ?"
            ]
        else:
            return [
                "Posez-moi une question sur la constitution",
                "Que voulez-vous savoir sur les droits fondamentaux ?",
                "Souhaitez-vous des informations sur le pouvoir exécutif ?",
                "Comment puis-je vous aider avec la constitution ?"
            ]

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse unifiée avec système hybride RAG + fallback"""
        start_time = time.time()
        
        try:
            # Détecter le type de question
            question_type = self._detect_question_type(query)
            query_lower = query.lower().strip()
            
            # Gestion des questions d'identité et de politesse
            if question_type == "identity":
                response = {
                    "answer": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions de la Guinée. Je peux vous aider à trouver des informations dans les documents constitutionnels et répondre à vos questions sur le droit constitutionnel.",
                    "confidence": 1.0,
                    "sources": [],
                    "search_time": time.time() - start_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?", "Souhaitez-vous des informations sur le pouvoir exécutif ?"]
                }
                
                # Tracking des métriques
                monitoring_service.track_query(
                    query=query,
                    response_time=time.time() - start_time,
                    success=True,
                    query_type=question_type,
                    used_rag=False,
                    confidence=1.0
                )
                
                return response
            
            if question_type == "politeness":
                if "merci" in query_lower:
                    response = {
                        "answer": "De rien ! N'hésitez pas si vous avez d'autres questions sur la constitution. Je suis là pour vous aider.",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                    }
                else:
                    response = {
                        "answer": "Bonjour ! Comment puis-je vous aider avec la constitution de la Guinée ?",
                        "confidence": 1.0,
                        "sources": [],
                        "search_time": time.time() - start_time,
                        "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                    }
                
                # Tracking des métriques
                monitoring_service.track_query(
                    query=query,
                    response_time=time.time() - start_time,
                    success=True,
                    query_type=question_type,
                    used_rag=False,
                    confidence=1.0
                )
                
                return response
            
            # Utiliser le système RAG si disponible
            used_rag = False
            if self.is_initialized:
                rag_result = self._rag_search(query)
                search_time = time.time() - start_time
                
                if rag_result["confidence"] > 0.3:  # Seuil plus bas pour plus de réponses
                    used_rag = True
                    response = {
                        "answer": rag_result["answer"],
                        "confidence": rag_result["confidence"],
                        "sources": rag_result["sources"],
                        "search_time": search_time,
                        "suggestions": self._generate_suggestions(query, question_type)
                    }
                    
                    # Tracking des métriques
                    monitoring_service.track_query(
                        query=query,
                        response_time=search_time,
                        success=True,
                        query_type=question_type,
                        used_rag=True,
                        confidence=rag_result["confidence"]
                    )
                    
                    return response
            
            # Fallback avec recherche par mots-clés
            keyword_results = self._keyword_search(query, constitutions, 5)
            search_time = time.time() - start_time
            
            if keyword_results:
                # Préparer le contexte avec les meilleurs chunks
                context_text = self._prepare_context(keyword_results)
                
                # Générer la réponse avec contexte
                ai_response = self._generate_ai_response(query, context_text)
                
                # Calculer la confiance basé sur les scores
                avg_score = sum(result[1] for result in keyword_results[:3]) / len(keyword_results[:3])
                confidence = min(avg_score / 10.0, 1.0)
                
                response = {
                    "answer": ai_response,
                    "confidence": confidence,
                    "sources": [{"title": result[0].title, "content": result[2][:200] + "..."} for result in keyword_results[:3]],
                    "search_time": search_time,
                    "suggestions": self._generate_suggestions(query, question_type)
                }
                
                # Tracking des métriques
                monitoring_service.track_query(
                    query=query,
                    response_time=search_time,
                    success=True,
                    query_type=question_type,
                    used_rag=used_rag,
                    confidence=confidence
                )
                
                return response
            
            # Fallback avec GPT générique
            fallback_response = self._generate_fallback_response(query)
            search_time = time.time() - start_time
            
            response = {
                "answer": fallback_response,
                "confidence": 0.1,
                "sources": [],
                "search_time": search_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
            }
            
            # Tracking des métriques
            monitoring_service.track_query(
                query=query,
                response_time=search_time,
                success=True,
                query_type=question_type,
                used_rag=False,
                confidence=0.1
            )
            
            return response
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"Erreur dans generate_response: {e}")
            
            # Tracking de l'erreur
            monitoring_service.track_error("generate_response_error", str(e))
            monitoring_service.track_query(
                query=query,
                response_time=error_time,
                success=False,
                query_type=question_type,
                used_rag=False,
                confidence=0.0
            )
            
            return {
                "answer": f"Une erreur s'est produite lors du traitement de votre demande : {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "search_time": error_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
            }

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
            system_prompt = """Tu es ConstitutionIA, un assistant spécialisé dans l'analyse des constitutions de la Guinée.

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

            response = self.llm.chat.completions.create(
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
            'élection', 'vote', 'citoyen', 'nationalité', 'constitution', 'loi',
            'république', 'démocratie', 'justice', 'tribunal', 'garantie'
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

    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système IA"""
        return {
            "is_initialized": self.is_initialized,
            "rag_available": self.qa_chain is not None,
            "vector_db_available": self.vector_db is not None,
            "openai_configured": bool(self.openai_api_key),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_chunks": self.max_chunks,
            "timeout_seconds": self.timeout_seconds
        } 