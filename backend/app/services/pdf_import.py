import sqlite3
import PyPDF2
import re
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pathlib import Path
import logging
from app.models.pdf_import import Article, Metadata

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class PDFImporter:
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extraction du texte PDF avec fallbacks"""
        text = ""
        
        # Essai 1: PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            if text.strip():
                logger.info(f"Texte extrait avec PyPDF2: {len(text)} caractères")
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 échoué: {e}")
        
        # Essai 2: LangChain PyPDFLoader
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            text = "\n".join(page.page_content for page in pages if getattr(page, 'page_content', '').strip())
            if text.strip():
                logger.info(f"Texte extrait avec LangChain: {len(text)} caractères")
                return text
        except Exception as e:
            logger.warning(f"LangChain échoué: {e}")
        
        # Essai 3: PyMuPDF
        try:
            import fitz
            with fitz.open(pdf_path) as doc:
                text = "\n".join(page.get_text() for page in doc)
            if text.strip():
                logger.info(f"Texte extrait avec PyMuPDF: {len(text)} caractères")
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF échoué: {e}")
        
        # Essai 4: OCR avec Tesseract
        try:
            import fitz
            import pytesseract
            from PIL import Image
            ocr_text_parts = []
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text_page = pytesseract.image_to_string(img, lang="fra")
                    if text_page.strip():
                        ocr_text_parts.append(text_page)
            text = "\n".join(ocr_text_parts)
            if text.strip():
                logger.info(f"Texte extrait avec OCR: {len(text)} caractères")
                return text
        except Exception as e:
            logger.warning(f"OCR échoué: {e}")
        
        logger.error("Aucune méthode d'extraction n'a fonctionné")
        return ""

    def parse_constitution(self, text: str) -> list:
        """Parsing des articles avec expressions régulières améliorées"""
        articles = []
        
        # Patterns améliorés pour capturer les articles
        patterns = [
            # Pattern 1: Article X - format standard
            r'(Article\s+\d+[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 2: Article X. - avec point
            r'(Article\s+\d+\.?[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 3: ART. X - format abrégé
            r'(ART\.\s*\d+[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 4: Art. X - format court
            r'(Art\.\s*\d+[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 5: ARTICLE X - format majuscule
            r'(ARTICLE\s+\d+[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 6: Article X : - avec deux points
            r'(Article\s+\d+\s*:[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 7: Article X - avec tiret
            r'(Article\s+\d+\s*-[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 8: Article X (avec parenthèses)
            r'(Article\s+\d+\s*\([^)]*\)[^\n]*)\n((?:[^\n]+\n)+)',
            # Pattern 9: Article X - format avec alinéas
            r'(Article\s+\d+[^\n]*)\n((?:[^\n]+\n)+?)(?=Article\s+\d+|$)',
            # Pattern 10: Article X - format avec numérotation
            r'(Article\s+\d+[^\n]*)\n((?:[^\n]+\n)+?)(?=Article\s+\d+|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
            for match in matches:
                article_num = match.group(1).strip()
                content = match.group(2).strip()
                
                # Nettoyer le contenu
                content = re.sub(r'\n+', '\n', content).strip()
                
                # Détection des parties/sections
                part_section = re.search(r'(PREMIÈRE|DEUXIÈME|TROISIÈME|QUATRIÈME|CINQUIÈME)\s+PARTIE|(TITRE\s+[IVXLCDM]+)', article_num, re.IGNORECASE)
                
                # Extraire le numéro d'article
                article_number_match = re.search(r'(\d+)', article_num)
                article_number = article_number_match.group(1) if article_number_match else article_num
                
                # Vérifier que le contenu n'est pas vide et a une longueur minimale
                if content and len(content) > 10:
                    articles.append({
                        'article_number': f"Article {article_number}",
                        'content': content,
                        'part': part_section.group(1) if part_section and part_section.group(1) else None,
                        'section': part_section.group(2) if part_section and part_section.group(2) else None,
                        'page_number': None  # À implémenter si nécessaire
                    })
        
        # Supprimer les doublons basés sur le numéro d'article
        seen = set()
        unique_articles = []
        for article in articles:
            if article['article_number'] not in seen:
                seen.add(article['article_number'])
                unique_articles.append(article)
        
        # Trier par numéro d'article
        unique_articles.sort(key=lambda x: int(re.search(r'\d+', x['article_number']).group()) if re.search(r'\d+', x['article_number']) else 0)
        
        return unique_articles

    def save_articles_to_db(self, constitution_id: int, articles: list) -> bool:
        """Sauvegarder les articles en base de données"""
        try:
            # Supprimer les articles existants pour cette constitution
            self.db.query(Article).filter(Article.constitution_id == constitution_id).delete()
            
            # Insérer les nouveaux articles
            for article in articles:
                db_article = Article(
                    constitution_id=constitution_id,
                    article_number=article['article_number'],
                    title=article.get('title'),
                    content=article['content'],
                    part=article.get('part'),
                    section=article.get('section'),
                    page_number=article.get('page_number')
                )
                self.db.add(db_article)
            
            # Mettre à jour les métadonnées
            metadata = Metadata(
                constitution_id=constitution_id,
                key='last_parsed',
                value=datetime.now().isoformat()
            )
            self.db.add(metadata)
            
            self.db.commit()
            logger.info(f"✅ {len(articles)} articles sauvegardés pour constitution_id {constitution_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erreur lors de la sauvegarde des articles: {e}")
            return False

    def process_pdf_file(self, constitution_id: int, file_path: str) -> dict:
        """Traiter un fichier PDF complet"""
        try:
            logger.info(f"🔄 Traitement du fichier: {file_path}")
            
            # Extraction du texte
            text = self.extract_pdf_text(file_path)
            if not text.strip():
                return {
                    'success': False,
                    'error': 'Impossible d\'extraire le texte du PDF',
                    'articles_count': 0
                }
            
            # Parsing des articles
            articles = self.parse_constitution(text)
            logger.info(f"📄 {len(articles)} articles trouvés")
            
            # Sauvegarde en base
            if self.save_articles_to_db(constitution_id, articles):
                return {
                    'success': True,
                    'articles_count': len(articles),
                    'text_length': len(text)
                }
            else:
                return {
                    'success': False,
                    'error': 'Erreur lors de la sauvegarde en base',
                    'articles_count': 0
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement: {e}")
            return {
                'success': False,
                'error': str(e),
                'articles_count': 0
            }

    def delete_constitution_articles(self, constitution_id: int) -> bool:
        """Supprimer tous les articles d'une constitution"""
        try:
            # Supprimer les articles
            self.db.query(Article).filter(Article.constitution_id == constitution_id).delete()
            
            # Supprimer les métadonnées
            self.db.query(Metadata).filter(Metadata.constitution_id == constitution_id).delete()
            
            self.db.commit()
            logger.info(f"🗑️ Articles supprimés pour constitution_id {constitution_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erreur lors de la suppression: {e}")
            return False

# Fonctions utilitaires pour l'intégration
def process_uploaded_pdf(db_session: Session, constitution_id: int, file_path: str) -> dict:
    """Fonction à appeler lors de l'upload d'un fichier"""
    importer = PDFImporter(db_session)
    return importer.process_pdf_file(constitution_id, file_path)

def delete_pdf_articles(db_session: Session, constitution_id: int) -> bool:
    """Fonction à appeler lors de la suppression d'un fichier"""
    importer = PDFImporter(db_session)
    return importer.delete_constitution_articles(constitution_id)

# Fonction de test
def test_pdf_import(pdf_path: str):
    """Fonction de test pour vérifier le parsing"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Créer une constitution de test
        from app.models.constitution import Constitution
        test_constitution = Constitution(
            filename="test.pdf",
            title="Test Constitution",
            country="Guinée",
            is_active=True
        )
        db.add(test_constitution)
        db.commit()
        db.refresh(test_constitution)
        
        # Traiter le PDF
        result = process_uploaded_pdf(db, test_constitution.id, pdf_path)
        print(f"Résultat: {result}")
        
        # Nettoyer
        db.delete(test_constitution)
        db.commit()
        
    finally:
        db.close()

if __name__ == "__main__":
    # Test avec un fichier spécifique
    pdf_file = "Fichier/DOC-20250708-WA0018_250708_110040_1_compressed_compressed.pdf"
    if Path(pdf_file).exists():
        test_pdf_import(pdf_file)
    else:
        print(f"Fichier {pdf_file} non trouvé")