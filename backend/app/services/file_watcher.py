import os
import time
import logging
from pathlib import Path
from typing import Set, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.constitution import Constitution
from app.services.pdf_analyzer import PDFAnalyzer
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileWatcher:
    def __init__(self, pdf_analyzer: PDFAnalyzer):
        self.pdf_analyzer = pdf_analyzer
        self.files_dir = Path("Fichier")
        self.known_files: Set[str] = set()
        self._load_known_files()
    
    def _load_known_files(self):
        """Charge la liste des fichiers déjà connus depuis la base de données"""
        try:
            db = next(get_db())
            existing_files = db.query(Constitution.filename).all()
            self.known_files = {file[0] for file in existing_files}
            logger.info(f"Chargé {len(self.known_files)} fichiers connus")
            db.close()
        except Exception as e:
            logger.error(f"Erreur lors du chargement des fichiers connus: {e}")
    
    def is_file_already_processed(self, filename: str) -> bool:
        """Vérifie si un fichier a déjà été traité"""
        return filename in self.known_files
    
    def scan_for_new_files(self) -> List[str]:
        """Scanne le dossier pour de nouveaux fichiers PDF"""
        if not self.files_dir.exists():
            logger.warning(f"Dossier {self.files_dir} n'existe pas")
            return []
        
        new_files = []
        for pdf_file in self.files_dir.glob("*.pdf"):
            if not self.is_file_already_processed(pdf_file.name):
                new_files.append(str(pdf_file))
                logger.info(f"Nouveau fichier détecté: {pdf_file.name}")
            else:
                logger.info(f"Fichier déjà traité, ignoré: {pdf_file.name}")
        
        return new_files
    
    def process_new_file(self, pdf_path: str, db: Session):
        """Traite un nouveau fichier PDF"""
        try:
            filename = Path(pdf_path).name
            
            # Obtenir les informations de base du fichier
            file_info = self.pdf_analyzer.get_file_info(pdf_path)
            
            # Analyser le contenu avec GPT-4
            analysis = self.pdf_analyzer.analyze_pdf_with_gpt4(pdf_path, filename)
            
            # Créer l'enregistrement en base de données
            constitution = Constitution(
                filename=filename,
                title=analysis.get("title", filename.replace(".pdf", "").title()),
                description=analysis.get("description", "Document constitutionnel"),
                year=analysis.get("year"),
                country=analysis.get("country", "Guinée"),
                status=analysis.get("status", "active"),
                summary=analysis.get("summary", "Document constitutionnel"),
                content="",  # Le contenu sera stocké séparément si nécessaire
                file_size=file_info["size"],
                file_path=str(pdf_path),
                is_active=True
            )
            
            db.add(constitution)
            db.commit()
            db.refresh(constitution)
            
            # Ajouter à la liste des fichiers connus
            self.known_files.add(filename)
            
            logger.info(f"Fichier traité avec succès: {filename}")
            return constitution
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier {pdf_path}: {e}")
            db.rollback()
            return None
    
    def process_all_new_files(self, db=None):
        """Traite tous les nouveaux fichiers PDF"""
        new_files = self.scan_for_new_files()
        
        if not new_files:
            logger.info("Aucun nouveau fichier détecté")
            return []
        
        processed_files = []
        
        # Utiliser la session passée en paramètre ou en créer une nouvelle
        if db is None:
            from app.database import get_db
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            for pdf_path in new_files:
                constitution = self.process_new_file(pdf_path, db)
                if constitution:
                    processed_files.append(constitution)
            
            # Recharger la liste des fichiers connus après traitement
            self._load_known_files()
        finally:
            if should_close_db:
                db.close()
        
        return processed_files
    
    def force_reprocess_file(self, filename: str, db: Session):
        """Force le retraitement d'un fichier spécifique"""
        try:
            # Supprimer l'ancien enregistrement s'il existe
            existing = db.query(Constitution).filter(Constitution.filename == filename).first()
            if existing:
                db.delete(existing)
                db.commit()
                logger.info(f"Ancien enregistrement supprimé pour: {filename}")
            
            # Retraiter le fichier
            pdf_path = str(self.files_dir / filename)
            if Path(pdf_path).exists():
                constitution = self.process_new_file(pdf_path, db)
                logger.info(f"Fichier retraité avec succès: {filename}")
                return constitution
            else:
                logger.error(f"Fichier non trouvé: {pdf_path}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du retraitement de {filename}: {e}")
            db.rollback()
            return None
    
    def start_watching(self, interval: int = 30):
        """Démarre la surveillance continue des fichiers"""
        logger.info(f"Démarrage de la surveillance des fichiers (intervalle: {interval}s)")
        
        while True:
            try:
                self.process_all_new_files()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Arrêt de la surveillance des fichiers")
                break
            except Exception as e:
                logger.error(f"Erreur dans la surveillance: {e}")
                time.sleep(interval) 