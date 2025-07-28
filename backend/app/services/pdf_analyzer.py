import os
import PyPDF2
import openai
from typing import Dict, Optional
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFAnalyzer:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un fichier PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du texte du PDF: {e}")
            return ""
    
    def analyze_pdf_with_gpt4(self, pdf_path: str, filename: str) -> Dict:
        """Analyse un PDF avec GPT-4 et retourne les métadonnées"""
        try:
            # Extraire le texte du PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                logger.warning(f"Aucun texte extrait du PDF: {pdf_path}")
                return self._get_default_metadata(filename)
            
            # Préparer le prompt pour GPT-4
            prompt = f"""
            Analyse ce document constitutionnel et fournis les informations suivantes au format JSON:
            
            Document: {text[:4000]}  # Limiter à 4000 caractères pour éviter les tokens excessifs
            
            Réponds uniquement avec un JSON valide contenant:
            {{
                "title": "Titre officiel du document",
                "description": "Description détaillée du contenu (2-3 phrases)",
                "year": année du document (nombre),
                "status": "active" ou "draft" ou "archived",
                "summary": "Résumé en 1-2 phrases",
                "key_topics": ["liste", "des", "sujets", "principaux"],
                "country": "Guinée"
            }}
            
            Si tu ne peux pas déterminer certaines informations, utilise null pour les champs manquants.
            """
            
            # Appel à GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse de documents constitutionnels. Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parser la réponse JSON
            import json
            try:
                result = json.loads(response.choices[0].message.content.strip())
                logger.info(f"Analyse GPT-4 réussie pour: {filename}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Erreur de parsing JSON pour: {filename}")
                return self._get_default_metadata(filename)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse GPT-4: {e}")
            return self._get_default_metadata(filename)
    
    def _get_default_metadata(self, filename: str) -> Dict:
        """Retourne des métadonnées par défaut si l'analyse échoue"""
        return {
            "title": filename.replace(".pdf", "").replace("_", " ").title(),
            "description": "Document constitutionnel de la Guinée",
            "year": None,
            "status": "active",
            "summary": "Document constitutionnel",
            "key_topics": ["constitution", "guinée"],
            "country": "Guinée"
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