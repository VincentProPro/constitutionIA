import os
import time
import sys
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.constitution import Constitution
import openai
import re

# RAG imports
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# Set UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class RAGAIService:
    def __init__(self):
        # Charger la clé API
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found. Please set it in your .env file.")
        
        # Initialiser les composants RAG optimisés
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        # Utiliser GPT-3.5-turbo pour plus de rapidité
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=self.openai_api_key)
        
        # Base vectorielle FAISS
        self.vector_db = None
        self.qa_chain = None
        
        # Types de questions
        self.question_types = {
            "identity": ["ton nom", "qui es-tu", "qui es tu", "comment t'appelles-tu", "comment t'appelles tu"],
            "politeness": ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye"],
            "constitutional": ["constitution", "article", "loi", "droit", "pouvoir"],
            "comparison": ["différence", "comparer", "versus", "contrairement"],
            "analysis": ["analyser", "expliquer", "comment", "pourquoi"],
            "specific": ["durée", "mandat", "élection", "vote"]
        }

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question"""
        query_lower = query.lower()
        
        # Détection spéciale pour les questions d'identité (plus précise)
        identity_keywords = ["ton nom", "qui es-tu", "qui es tu", "comment t'appelles-tu", "comment t'appelles tu"]
        if any(keyword in query_lower for keyword in identity_keywords):
            return "identity"
        
        # Détection spéciale pour les questions de politesse
        politeness_keywords = ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye"]
        if any(keyword in query_lower for keyword in politeness_keywords):
            return "politeness"
        
        # Détection pour les autres types
        for qtype, keywords in self.question_types.items():
            if qtype not in ["identity", "politeness"] and any(keyword in query_lower for keyword in keywords):
                return qtype
        return "general"

    def _load_pdf_documents(self, folder_path: str = "Fichier/"):
        """Charge les documents PDF"""
        documents = []
        
        if not os.path.exists(folder_path):
            print(f"Warning: Le dossier {folder_path} n'existe pas.")
            return documents
        
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        if not pdf_files:
            print(f"Warning: Aucun fichier PDF trouvé dans {folder_path}")
            return documents
        
        for filename in pdf_files:
            try:
                loader = PyPDFLoader(os.path.join(folder_path, filename))
                documents.extend(loader.load())
                print(f"Chargé: {filename}")
            except Exception as e:
                print(f"Erreur lors du chargement de {filename}: {e}")
        
        return documents

    def _initialize_rag_system(self):
        """Initialise le système RAG avec FAISS"""
        try:
            # Charger les documents PDF
            pdf_docs = self._load_pdf_documents()
            
            if not pdf_docs:
                print("Aucun document PDF chargé. Utilisation du mode fallback.")
                return False
            
            # Découper les documents en chunks optimisés
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1500,  # Chunks plus grands pour moins de chunks
                chunk_overlap=100  # Moins de recouvrement
            )
            docs = text_splitter.split_documents(pdf_docs)
            print(f"{len(docs)} chunks créés à partir de {len(pdf_docs)} documents")
            
            # Créer la base vectorielle FAISS
            print("Création de la base vectorielle FAISS...")
            self.vector_db = FAISS.from_documents(docs, self.embeddings)
            
            # Créer la chaîne RAG optimisée
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_db.as_retriever(
                    search_type="similarity", 
                    search_kwargs={"k": 3}  # Réduire le nombre de chunks
                ),
                return_source_documents=True
            )
            
            print("Système RAG initialisé avec succès!")
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation RAG: {e}")
            return False

    def _rag_search(self, query: str) -> Dict[str, Any]:
        """Recherche avec le système RAG optimisé"""
        if not self.qa_chain:
            return {
                "answer": "Système RAG non disponible (quota OpenAI dépassé). Utilisation du mode fallback.",
                "sources": [],
                "confidence": 0.0
            }
        
        try:
            # Timeout pour éviter les réponses trop lentes
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Recherche RAG trop lente")
            
            # Définir un timeout de 5 secondes
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            try:
                response = self.qa_chain(query)
                signal.alarm(0)  # Annuler le timeout
                
                # Extraire les sources
                sources = []
                for doc in response['source_documents']:
                    sources.append({
                        "title": doc.metadata.get('source', 'Document'),
                        "content": doc.page_content[:200] + "...",
                        "page": doc.metadata.get('page', 'N/A')
                    })
                
                return {
                    "answer": response['result'],
                    "sources": sources,
                    "confidence": 0.8  # RAG avec GPT-3.5-turbo
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
                    "answer": "Désolé, le système IA est temporairement indisponible (quota OpenAI dépassé). Veuillez recharger votre compte OpenAI ou réessayer plus tard.",
                    "sources": [],
                    "confidence": 0.0
                }
            else:
                return {
                    "answer": f"Erreur lors de la recherche RAG: {error_msg}",
                    "sources": [],
                    "confidence": 0.0
                }

    def _keyword_search(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche par mots-clés (fallback)"""
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

    def _generate_fallback_response(self, query: str) -> str:
        """Réponse de secours avec GPT générique"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            system_prompt = """Tu es ConstitutionIA. L'information demandée n'est pas dans les documents constitutionnels disponibles.

INSTRUCTIONS:
1. Explique poliment que l'information n'est pas disponible
2. Suggère des questions alternatives sur la constitution
3. Propose de reformuler la question
4. Reste professionnel et utile"""

            user_prompt = f"Question: {query}\n\nL'information n'est pas dans les documents constitutionnels."

            response = client.chat.completions.create(
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

    def search_constitutions(self, query: str, constitutions: List[Constitution], max_results: int = 5) -> List[Tuple[Constitution, float, str]]:
        """Recherche hybride : RAG + mots-clés"""
        # Essayer d'abord le RAG
        if self.qa_chain:
            rag_result = self._rag_search(query)
            if rag_result["confidence"] > 0.5:
                # Convertir le résultat RAG en format attendu
                # Pour l'instant, on utilise la recherche par mots-clés comme fallback
                pass
        
        # Fallback vers la recherche par mots-clés
        return self._keyword_search(query, constitutions, max_results)

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse avec système RAG hybride"""
        start_time = time.time()
        
        try:
            question_type = self._detect_question_type(query)
            query_lower = query.lower().strip()
            
            # Réponses directes pour questions spéciales (seulement pour les vraies questions d'identité)
            if question_type == "identity" and any(keyword in query_lower for keyword in ["ton nom", "qui es-tu", "qui es tu", "comment t'appelles-tu", "comment t'appelles tu"]):
                return {
                    "answer": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions et documents juridiques. Je utilise un système RAG avancé pour vous fournir des réponses précises.",
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
            
            # Essayer le RAG d'abord
            if self.qa_chain:
                rag_result = self._rag_search(query)
                search_time = time.time() - start_time
                
                if rag_result["confidence"] > 0.5:
                    return {
                        "answer": rag_result["answer"],
                        "confidence": rag_result["confidence"],
                        "sources": rag_result["sources"],
                        "search_time": search_time,
                        "suggestions": self._generate_suggestions(query, question_type)
                    }
            
            # Fallback avec GPT générique
            fallback_response = self._generate_fallback_response(query)
            return {
                "answer": fallback_response,
                "confidence": 0.1,
                "sources": [],
                "search_time": time.time() - start_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
            }
            
        except Exception as e:
            return {
                "answer": f"Une erreur s'est produite : {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "search_time": time.time() - start_time,
                "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
            }

    def _prepare_context(self, search_results: List[Tuple[Constitution, float, str]]) -> str:
        """Prépare le contexte"""
        if not search_results:
            return ""
        
        context_parts = []
        for constitution, score, chunk in search_results[:5]:
            context_parts.append(f"📄 {constitution.filename} (Score: {score:.2f}):\n{chunk}\n")
        
        return "\n".join(context_parts)

    def _generate_ai_response(self, query: str, context: str) -> str:
        """Génère une réponse avec OpenAI"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            system_prompt = """Tu es ConstitutionIA, assistant spécialisé dans l'analyse des constitutions.

INSTRUCTIONS:
1. Réponds UNIQUEMENT basé sur le contexte fourni
2. Structure ta réponse clairement avec des points numérotés
3. Cite spécifiquement les articles pertinents
4. Utilise un langage juridique accessible
5. Si l'information n'est pas dans le contexte, dis-le clairement
6. Réponds en français de manière concise"""

            user_prompt = f"Question: {query}\n\nContexte:\n{context}\n\nRéponse:"

            response = client.chat.completions.create(
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

    def initialize(self):
        """Initialise le système RAG"""
        return self._initialize_rag_system() 