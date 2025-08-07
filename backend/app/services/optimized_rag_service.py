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

load_dotenv()

class OptimizedRAGService:
    def __init__(self):
        # Charger la clé API
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found.")
        
        # Initialiser les composants optimisés
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo", 
            temperature=0.1,  # Réduire la température pour plus de cohérence
            openai_api_key=self.openai_api_key,
            max_tokens=600  # Limiter les tokens pour plus de rapidité
        )
        
        # Système RAG
        self.qa_chain = None
        self.vector_db = None
        
        # Configuration optimisée pour performance
        self.chunk_size = 1000  # Chunks plus petits pour plus de précision
        self.chunk_overlap = 100  # Recouvrement optimal
        self.max_chunks = 3  # Moins de chunks pour plus de rapidité
        self.timeout_seconds = 6  # Timeout optimisé

    def _load_pdf_documents(self, folder_path: str = "Fichier/"):
        """Charge les documents PDF avec gestion d'erreurs améliorée"""
        documents = []
        
        if not os.path.exists(folder_path):
            print(f"Le dossier {folder_path} n'existe pas.")
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
                print(f"✅ Chargé: {filename} ({len(docs)} pages)")
                
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {filename}: {e}")
        
        return documents

    def _initialize_rag_system(self):
        """Initialise le système RAG avec optimisations"""
        try:
            # Charger les documents PDF
            pdf_docs = self._load_pdf_documents()
            
            if not pdf_docs:
                print("Aucun document PDF chargé.")
                return False
            
            # Découper les documents avec des paramètres optimisés
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            docs = text_splitter.split_documents(pdf_docs)
            print(f"📄 {len(docs)} chunks créés (taille: {self.chunk_size}, overlap: {self.chunk_overlap})")
            
            # Créer la base vectorielle FAISS avec index optimisé
            print("🔧 Création de la base vectorielle FAISS...")
            self.vector_db = FAISS.from_documents(docs, self.embeddings)
            
            # Créer la chaîne RAG avec prompt personnalisé pour plus de précision
            custom_prompt = PromptTemplate(
                input_variables=["context", "question"],
                template="""Tu es ConstitutionIA, assistant spécialisé dans l'analyse des constitutions.

CONTEXTE:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Réponds UNIQUEMENT basé sur le contexte fourni
2. Cite spécifiquement les articles et pages pertinents
3. Structure ta réponse clairement avec des points numérotés
4. Si l'information n'est pas dans le contexte, dis-le clairement
5. Utilise un langage juridique accessible
6. Sois concis et précis (max 300 mots)

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
            
            print("✅ Système RAG optimisé initialisé avec succès!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation RAG: {e}")
            return False

    def _rag_search(self, query: str) -> Dict[str, Any]:
        """Recherche RAG optimisée avec timeout et gestion d'erreurs"""
        if not self.qa_chain:
            return {
                "answer": "Système RAG non disponible. Utilisation du mode fallback.",
                "sources": [],
                "confidence": 0.0
            }
        
        try:
            # Timeout avec gestion d'erreurs améliorée
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

    def generate_response(self, query: str, constitutions: List[Constitution], context: str = None) -> Dict[str, Any]:
        """Génère une réponse optimisée"""
        start_time = time.time()
        
        try:
            # Détecter le type de question
            question_type = self._detect_question_type(query)
            
            # Gestion des questions d'identité et de politesse
            if question_type == "identity":
                return {
                    "answer": "Je suis ConstitutionIA, votre assistant spécialisé dans l'analyse des constitutions de la Guinée. Je peux vous aider à trouver des informations dans les documents constitutionnels.",
                    "confidence": 1.0,
                    "sources": [],
                    "search_time": time.time() - start_time,
                    "suggestions": ["Posez-moi une question sur la constitution", "Que voulez-vous savoir sur les droits fondamentaux ?"]
                }
            
            if question_type == "politeness":
                if "merci" in query.lower():
                    return {
                        "answer": "De rien ! N'hésitez pas si vous avez d'autres questions sur la constitution.",
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
            
            # Utiliser le système RAG optimisé
            rag_result = self._rag_search(query)
            search_time = time.time() - start_time
            
            if rag_result["confidence"] > 0.3:  # Seuil plus bas pour plus de réponses
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
                "search_time": search_time,
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

    def _detect_question_type(self, query: str) -> str:
        """Détecte le type de question pour optimiser la réponse"""
        query_lower = query.lower()
        
        # Questions d'identité
        identity_keywords = ["qui es-tu", "qui es tu", "ton nom", "appelle", "qui êtes-vous", "votre nom"]
        if any(keyword in query_lower for keyword in identity_keywords):
            return "identity"
        
        # Questions de politesse
        politeness_keywords = ["merci", "bonjour", "salut", "hello", "hi", "au revoir", "bye"]
        if any(keyword in query_lower for keyword in politeness_keywords):
            return "politeness"
        
        # Questions constitutionnelles
        constitutional_keywords = ["constitution", "article", "loi", "droit", "pouvoir", "président", "gouvernement"]
        if any(keyword in query_lower for keyword in constitutional_keywords):
            return "constitutional"
        
        return "general"

    def _generate_fallback_response(self, query: str) -> str:
        """Génère une réponse de fallback optimisée"""
        try:
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es ConstitutionIA, assistant spécialisé dans les constitutions. Si tu ne trouves pas l'information demandée, guide poliment l'utilisateur vers des questions plus spécifiques."},
                    {"role": "user", "content": f"Question: {query}\n\nRéponse:"}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Je ne trouve pas cette information dans les documents disponibles. Pouvez-vous reformuler votre question ?"

    def _generate_suggestions(self, query: str, question_type: str) -> List[str]:
        """Génère des suggestions contextuelles optimisées"""
        if question_type == "constitutional":
            return [
                "Quels sont les droits fondamentaux garantis ?",
                "Comment est organisé le pouvoir exécutif ?",
                "Quelles sont les conditions d'élection du président ?"
            ]
        else:
            return [
                "Posez-moi une question sur la constitution",
                "Que voulez-vous savoir sur les droits fondamentaux ?",
                "Souhaitez-vous des informations sur le pouvoir exécutif ?"
            ]

    def initialize(self):
        """Initialise le système RAG optimisé"""
        print("🚀 Initialisation du système RAG optimisé...")
        return self._initialize_rag_system() 