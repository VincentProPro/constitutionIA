#!/usr/bin/env python3
"""
Service d'automatisation pour la surveillance et le traitement des fichiers PDF
"""

import asyncio
import threading
import time
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from app.services.pdf_import import process_uploaded_pdf, delete_pdf_articles
from app.services.file_watcher import FileWatcher
from app.services.pdf_analyzer import PDFAnalyzer
from app.core.config import settings

logger = logging.getLogger(__name__)

class AutomationService:
    """Service d'automatisation pour la gestion des fichiers PDF"""
    
    def __init__(self):
        self.is_running = False
        self.watcher_thread: Optional[threading.Thread] = None
        self.scan_interval = 30  # secondes
        self.files_dir = Path("Fichier")
        self.known_files = set()
        
    def start(self):
        """Démarrer le service d'automatisation"""
        if self.is_running:
            logger.warning("Service d'automatisation déjà en cours d'exécution")
            return
        
        logger.info("🚀 Démarrage du service d'automatisation")
        self.is_running = True
        
        # Charger les fichiers connus
        self._load_known_files()
        
        # Démarrer le thread de surveillance
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        
        logger.info("✅ Service d'automatisation démarré")
    
    def stop(self):
        """Arrêter le service d'automatisation"""
        if not self.is_running:
            return
        
        logger.info("🛑 Arrêt du service d'automatisation")
        self.is_running = False
        
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.watcher_thread.join(timeout=5)
        
        logger.info("✅ Service d'automatisation arrêté")
    
    def _load_known_files(self):
        """Charger la liste des fichiers connus depuis la base de données"""
        try:
            db = SessionLocal()
            existing_files = db.query(Constitution.filename).filter(Constitution.is_active == True).all()
            self.known_files = {file[0] for file in existing_files}
            logger.info(f"📋 {len(self.known_files)} fichiers connus chargés")
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des fichiers connus: {e}")
        finally:
            db.close()
    
    def _watch_loop(self):
        """Boucle principale de surveillance"""
        logger.info(f"👁️ Surveillance des fichiers (intervalle: {self.scan_interval}s)")
        
        while self.is_running:
            try:
                self._scan_and_process_new_files()
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de surveillance: {e}")
                time.sleep(self.scan_interval)
    
    def _scan_and_process_new_files(self):
        """Scanner et traiter les nouveaux fichiers"""
        if not self.files_dir.exists():
            logger.warning(f"📁 Dossier {self.files_dir} n'existe pas")
            return
        
        new_files = []
        for pdf_file in self.files_dir.glob("*.pdf"):
            if pdf_file.name not in self.known_files:
                new_files.append(pdf_file)
                logger.info(f"🆕 Nouveau fichier détecté: {pdf_file.name}")
        
        if new_files:
            logger.info(f"📦 {len(new_files)} nouveaux fichiers à traiter")
            self._process_new_files(new_files)
        else:
            logger.debug("✅ Aucun nouveau fichier détecté")
    
    def _process_new_files(self, new_files):
        """Traiter les nouveaux fichiers"""
        db = SessionLocal()
        
        try:
            for pdf_file in new_files:
                try:
                    logger.info(f"🔄 Traitement de {pdf_file.name}")
                    
                    # Vérifier si la constitution existe déjà
                    existing = db.query(Constitution).filter(
                        Constitution.filename == pdf_file.name,
                        Constitution.is_active == True
                    ).first()
                    
                    if existing:
                        logger.info(f"⚠️ Constitution existe déjà pour {pdf_file.name}, mise à jour")
                        constitution = existing
                        # Mettre à jour les informations du fichier
                        constitution.file_size = pdf_file.stat().st_size
                        constitution.file_path = str(pdf_file)
                        db.commit()
                    else:
                        # Créer l'entrée en base de données
                        constitution = Constitution(
                            filename=pdf_file.name,
                            title=pdf_file.stem.replace("_", " ").title(),
                            description="Document constitutionnel détecté automatiquement",
                            year=None,
                            country="Guinée",
                            status="active",
                            content="",
                            summary="",
                            key_topics="",
                            file_path=str(pdf_file),
                            file_size=pdf_file.stat().st_size,
                            is_active=True
                        )
                        
                        db.add(constitution)
                        db.commit()
                        db.refresh(constitution)
                        
                        logger.info(f"✅ Constitution créée (ID: {constitution.id})")
                    
                    # Extraire les articles automatiquement
                    result = process_uploaded_pdf(db, constitution.id, str(pdf_file))
                    
                    if result['success']:
                        logger.info(f"✅ {result['articles_count']} articles extraits pour {pdf_file.name}")
                        self.known_files.add(pdf_file.name)
                    else:
                        logger.error(f"❌ Échec de l'extraction pour {pdf_file.name}: {result.get('error')}")
                        # Ne pas supprimer la constitution si elle existait déjà
                        if not existing:
                            db.delete(constitution)
                            db.commit()
                
                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement de {pdf_file.name}: {e}")
                    db.rollback()
        
        finally:
            db.close()
    
    def force_process_file(self, filename: str) -> bool:
        """Forcer le traitement d'un fichier spécifique"""
        try:
            file_path = self.files_dir / filename
            if not file_path.exists():
                logger.error(f"❌ Fichier non trouvé: {filename}")
                return False
            
            db = SessionLocal()
            
            try:
                # Vérifier si la constitution existe déjà
                existing = db.query(Constitution).filter(
                    Constitution.filename == filename,
                    Constitution.is_active == True
                ).first()
                
                if existing:
                    logger.info(f"🔄 Retraitement de {filename}")
                    # Supprimer les anciens articles
                    delete_pdf_articles(db, existing.id)
                    constitution = existing
                else:
                    logger.info(f"🆕 Premier traitement de {filename}")
                    # Créer une nouvelle constitution
                    constitution = Constitution(
                        filename=filename,
                        title=file_path.stem.replace("_", " ").title(),
                        description="Document constitutionnel",
                        year=None,
                        country="Guinée",
                        status="active",
                        content="",
                        summary="",
                        key_topics="",
                        file_path=str(file_path),
                        file_size=file_path.stat().st_size,
                        is_active=True
                    )
                    db.add(constitution)
                    db.commit()
                    db.refresh(constitution)
                
                # Extraire les articles
                result = process_uploaded_pdf(db, constitution.id, str(file_path))
                
                if result['success']:
                    logger.info(f"✅ {result['articles_count']} articles extraits pour {filename}")
                    self.known_files.add(filename)
                    return True
                else:
                    logger.error(f"❌ Échec de l'extraction: {result.get('error')}")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement forcé de {filename}: {e}")
            return False
    
    def get_status(self) -> dict:
        """Obtenir le statut du service"""
        return {
            "is_running": self.is_running,
            "scan_interval": self.scan_interval,
            "known_files_count": len(self.known_files),
            "files_dir": str(self.files_dir),
            "thread_alive": self.watcher_thread.is_alive() if self.watcher_thread else False
        }

# Instance globale du service
automation_service = AutomationService()

def start_automation_service():
    """Démarrer le service d'automatisation"""
    automation_service.start()

def stop_automation_service():
    """Arrêter le service d'automatisation"""
    automation_service.stop()

def get_automation_service() -> AutomationService:
    """Obtenir l'instance du service d'automatisation"""
    return automation_service 