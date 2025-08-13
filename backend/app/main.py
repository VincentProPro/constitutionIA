from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai_copilot, constitutions, chatnow
from app.database import engine
from app.models import constitution, user
from app.services.automation_service import start_automation_service, stop_automation_service
import os
import atexit

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
app.include_router(chatnow.router, tags=["ChatNow"])

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    print("🚀 Démarrage de ConstitutionIA API")
    print("📋 Initialisation du service d'automatisation...")
    
    # Démarrer le service d'automatisation
    start_automation_service()
    
    # Enregistrer la fonction d'arrêt
    atexit.register(stop_automation_service)
    
    print("✅ Service d'automatisation démarré")
    print("✅ ConstitutionIA API prête")

@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application"""
    print("🛑 Arrêt de ConstitutionIA API")
    print("📋 Arrêt du service d'automatisation...")
    
    # Arrêter le service d'automatisation
    stop_automation_service()
    
    print("✅ Service d'automatisation arrêté")
    print("✅ ConstitutionIA API arrêtée")

@app.get("/")
async def root():
    return {"message": "ConstitutionIA API - Système RAG avec FAISS"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "system": "RAG with FAISS"}

@app.get("/automation/status")
async def get_automation_status():
    """Obtenir le statut du service d'automatisation"""
    from app.services.automation_service import get_automation_service
    service = get_automation_service()
    return service.get_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 