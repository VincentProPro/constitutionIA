from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str = "sqlite:///./constitutionia.db"
    
    # Sécurité
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # IA
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-3.5-turbo"
    
    # Application
    APP_NAME: str = "ConstitutionIA"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings() 