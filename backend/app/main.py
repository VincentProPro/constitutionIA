from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai_copilot, constitutions
from app.database import engine
from app.models import constitution, user
import os

# Créer les tables
constitution.Base.metadata.create_all(bind=engine)
user.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ConstitutionIA API",
    description="API pour la gestion des constitutions avec copilot IA",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*"  # Pour le développement
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routeurs
app.include_router(ai_copilot.router, prefix="/api/ai", tags=["AI Copilot"])
app.include_router(constitutions.router, prefix="/api/constitutions", tags=["Constitutions"])

@app.get("/")
async def root():
    return {"message": "ConstitutionIA API - Système RAG avec FAISS"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "system": "RAG with FAISS"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 