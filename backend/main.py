from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Optional
import os

from app.database import engine, Base
from app.routers import constitutions, ai_copilot, auth
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Créer les tables au démarrage
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="ConstitutionIA API",
    description="API pour la gestion des constitutions avec copilot IA",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(constitutions.router, prefix="/api/constitutions", tags=["Constitutions"])
app.include_router(ai_copilot.router, prefix="/api/ai", tags=["AI Copilot"])

@app.get("/")
async def root():
    return {
        "message": "ConstitutionIA API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 