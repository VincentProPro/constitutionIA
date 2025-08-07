import os
import PyPDF2
from openai import OpenAI
from typing import Dict, Optional, List
from pathlib import Path
import logging
import re
from app.core.config import settings

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFAnalyzer:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un fichier PDF avec améliorations"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    
                    # Nettoyer le texte extrait
                    page_text = self._clean_text(page_text)
                    
                    # Ajouter le numéro de page si le texte n'est pas vide
                    if page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text + "\n"
                
                # Nettoyer le texte final
                text = self._clean_final_text(text)
                
                logger.info(f"Texte extrait avec succès: {len(text)} caractères")
                return text
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du texte du PDF: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les lignes vides multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Nettoyer les caractères spéciaux
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        return text.strip()
    
    def _clean_final_text(self, text: str) -> str:
        """Nettoie le texte final"""
        # Supprimer les lignes avec seulement des caractères spéciaux
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Garder les lignes qui ont du contenu significatif
            if len(line.strip()) > 2 or re.search(r'[a-zA-Z]', line):
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Supprimer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def _extract_articles(self, text: str) -> List[Dict]:
        """Extrait les articles de la constitution"""
        articles = []
        
        # Pattern pour détecter les articles
        article_pattern = r'Article\s+(\d+)[\.\s]+(.+?)(?=Article\s+\d+|$)'
        matches = re.finditer(article_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            article_num = match.group(1)
            article_content = match.group(2).strip()
            
            if len(article_content) > 10:  # Filtrer les articles trop courts
                articles.append({
                    'number': article_num,
                    'content': article_content,
                    'summary': self._summarize_article(article_content)
                })
        
        return articles
    
    def _summarize_article(self, content: str) -> str:
        """Résume le contenu d'un article"""
        # Prendre les premiers mots significatifs
        words = content.split()
        if len(words) <= 20:
            return content
        
        # Trouver la première phrase complète
        sentences = re.split(r'[.!?]', content)
        if sentences:
            return sentences[0].strip() + "."
        
        return ' '.join(words[:20]) + "..."
    
    def analyze_pdf_with_gpt4(self, pdf_path: str, filename: str) -> Dict:
        """Analyse un PDF avec GPT-4 et retourne les métadonnées améliorées"""
        try:
            # Extraire le texte du PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                logger.warning(f"Aucun texte extrait du PDF: {pdf_path}")
                return self._get_default_metadata(filename)
            
            # Extraire les articles
            articles = self._extract_articles(text)
            
            # Extraire l'année du contenu
            year_from_content = self._extract_year_from_content(text)
            
            # Préparer le prompt pour GPT-4
            prompt = f"""
            Analyse ce document constitutionnel et fournis les informations suivantes au format JSON:
            
            Document: {text[:6000]}  # Augmenter la limite pour une meilleure analyse
            
            Réponds uniquement avec un JSON valide contenant:
            {{
                "title": "Titre officiel du document",
                "description": "Description détaillée du contenu (3-4 phrases)",
                "year": année du document (nombre) - utilise {year_from_content} si détecté,
                "status": "active" ou "draft" ou "archived",
                "summary": "Résumé en 2-3 phrases",
                "key_topics": ["liste", "des", "sujets", "principaux"],
                "country": "Guinée",
                "total_articles": nombre d'articles trouvés,
                "main_sections": ["sections", "principales", "identifiées"],
                "document_type": "constitution" ou "loi" ou "décret" ou "autre"
            }}
            
            Analyse aussi la structure du document et identifie les sections principales.
            Si tu ne peux pas déterminer certaines informations, utilise null pour les champs manquants.
            """
            
            # Appel à GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse de documents constitutionnels. Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2  # Plus déterministe
            )
            
            # Parser la réponse JSON
            import json
            try:
                result = json.loads(response.choices[0].message.content.strip())
                
                # Utiliser l'année extraite du contenu si GPT-4 n'en a pas trouvé
                if not result.get('year') and year_from_content:
                    result['year'] = year_from_content
                    logger.info(f"Année extraite du contenu: {year_from_content}")
                
                # Ajouter les informations sur les articles
                result['total_articles'] = len(articles)
                result['articles_preview'] = [{'number': art['number'], 'summary': art['summary']} for art in articles[:5]]
                
                logger.info(f"Analyse GPT-4 réussie pour: {filename}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Erreur de parsing JSON pour: {filename}")
                # Utiliser l'année extraite même en cas d'erreur GPT-4
                default_metadata = self._get_default_metadata(filename)
                if year_from_content:
                    default_metadata['year'] = year_from_content
                return default_metadata
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse GPT-4: {e}")
            # Utiliser l'année extraite même en cas d'erreur
            default_metadata = self._get_default_metadata(filename)
            if 'text' in locals():
                year_from_content = self._extract_year_from_content(text)
                if year_from_content:
                    default_metadata['year'] = year_from_content
            return default_metadata
    
    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """Extrait l'année du nom du fichier"""
        # Patterns pour détecter les années dans le nom du fichier
        year_patterns = [
            r'(\d{4})',  # 4 chiffres consécutifs
            r'(\d{2})',  # 2 chiffres (année courte)
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, filename)
            if match:
                year = int(match.group(1))
                # Validation de l'année (entre 1900 et 2100)
                if 1900 <= year <= 2100:
                    return year
                # Si c'est une année courte (ex: 24 pour 2024)
                elif 0 <= year <= 99:
                    return 2000 + year
        return None
    
    def _extract_year_from_content(self, text: str) -> Optional[int]:
        """Extrait l'année du contenu du document"""
        # Patterns pour détecter les années dans le contenu
        year_patterns = [
            r'(\d{4})',  # 4 chiffres consécutifs
            r'promulgué[e]?\s+le\s+(\d{1,2})\s+[a-zA-Z]+\s+(\d{4})',  # Date de promulgation
            r'(\d{4})\s*[-–]\s*(\d{4})',  # Période
        ]
        
        for pattern in year_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    year = int(match.group(1))
                    if 1900 <= year <= 2100:
                        return year
                elif len(match.groups()) == 2:
                    # Pour les dates de promulgation
                    if 'promulgué' in text.lower():
                        year = int(match.group(2))
                        if 1900 <= year <= 2100:
                            return year
        return None

    def _get_default_metadata(self, filename: str) -> Dict:
        """Retourne des métadonnées par défaut si l'analyse échoue"""
        # Extraire l'année du nom du fichier
        year = self._extract_year_from_filename(filename)
        
        return {
            "title": filename.replace(".pdf", "").replace("_", " ").title(),
            "description": "Document constitutionnel de la Guinée",
            "year": year,
            "status": "active",
            "summary": "Document constitutionnel",
            "key_topics": ["constitution", "guinée"],
            "country": "Guinée",
            "total_articles": 0,
            "main_sections": ["général"],
            "document_type": "constitution"
        }
    
    def get_file_info(self, pdf_path: str) -> Dict:
        """Obtient les informations de base du fichier"""
        path = Path(pdf_path)
        return {
            "filename": path.name,
            "size": path.stat().st_size,
            "created_at": path.stat().st_ctime,
            "modified_at": path.stat().st_mtime
        }
    
    def extract_structured_content(self, pdf_path: str) -> Dict:
        """Extrait le contenu structuré du PDF"""
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {"error": "Impossible d'extraire le texte"}
        
        # Extraire les articles
        articles = self._extract_articles(text)
        
        # Identifier les sections principales
        sections = self._identify_sections(text)
        
        return {
            "raw_text": text,
            "articles": articles,
            "sections": sections,
            "total_articles": len(articles),
            "text_length": len(text)
        }
    
    def _identify_sections(self, text: str) -> List[Dict]:
        """Identifie les sections principales du document"""
        sections = []
        
        # Patterns pour identifier les sections
        section_patterns = [
            r'TITRE\s+(\d+)[\s\-]+(.+?)(?=TITRE\s+\d+|$)',
            r'CHAPITRE\s+(\d+)[\s\-]+(.+?)(?=CHAPITRE\s+\d+|$)',
            r'Section\s+(\d+)[\s\-]+(.+?)(?=Section\s+\d+|$)'
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section_num = match.group(1)
                section_title = match.group(2).strip()
                section_content = match.group(0)
                
                sections.append({
                    'type': 'section',
                    'number': section_num,
                    'title': section_title,
                    'content': section_content[:500] + "..." if len(section_content) > 500 else section_content
                })
        
        return sections 