import os
import sys
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

# 1. Charger la clé API
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key or openai_api_key == "votre_clé_api_ici":
    raise ValueError("OPENAI_API_KEY environment variable not found or not set. Please set it in your .env file.")

# 2. Charger et lire les documents PDF
def load_pdf_documents(folder_path):
    documents = []
    if not os.path.exists(folder_path):
        print(f"Warning: Le dossier {folder_path} n'existe pas. Creation du dossier...")
        os.makedirs(folder_path, exist_ok=True)
        print(f"Dossier {folder_path} cree. Veuillez y placer vos fichiers PDF.")
        return documents
    
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"Warning: Aucun fichier PDF trouve dans {folder_path}")
        return documents
    
    for filename in pdf_files:
        try:
            loader = PyPDFLoader(os.path.join(folder_path, filename))
            documents.extend(loader.load())
            print(f"Charge: {filename}")
        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {e}")
    
    return documents

pdf_docs = load_pdf_documents("pdfs/")  # Dossier contenant les PDF

if not pdf_docs:
    print("Aucun document PDF charge. Le script s'arrete.")
    exit()

# 3. Decouper les documents en chunks (avec recouvrement pour contexte)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
docs = text_splitter.split_documents(pdf_docs)
print(f"{len(docs)} chunks crees a partir de {len(pdf_docs)} documents")

# 4. Creer les embeddings avec OpenAI
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

# 5. Creer une base vectorielle FAISS locale
print("Creation de la base vectorielle FAISS...")
db = FAISS.from_documents(docs, embeddings)

# 6. Creer un agent RAG avec GPT-4 + FAISS
llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=openai_api_key)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # tous les chunks sont "stuffes" dans le prompt
    retriever=db.as_retriever(search_type="similarity", search_kwargs={"k": 4}),
    return_source_documents=True
)

# 7. Lancer une requete
def ask_question(question: str):
    print(f"\nQuestion: {question}")
    response = qa_chain(question)
    print("\nReponse :\n", response['result'])
    print("\nExtraits utilises :")
    for doc in response['source_documents']:
        print(f"- {doc.metadata['source']} [page: {doc.metadata.get('page', 'N/A')}]")

# Exemple
if __name__ == "__main__":
    ask_question("Comment avez vous fait pour trouver cette information ?")