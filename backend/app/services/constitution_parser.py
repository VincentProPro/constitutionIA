"""
Service pour parser et structurer le fichier 02.txt
Extraction automatique des articles, chapitres, sections
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.constitution_data import (
    ConstitutionArticle, 
    ConstitutionStructure, 
    ConstitutionKeyword,
    ConstitutionCache
)

logger = logging.getLogger(__name__)

class ConstitutionParser:
    """Parser pour extraire et structurer les données de la constitution"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def parse_constitution_file(self, file_path: str) -> Dict:
        """
        Parse le fichier 02.txt et extrait la structure
        """
        try:
            # Essayer différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    logger.info(f"Fichier lu avec succès en {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise Exception("Impossible de lire le fichier avec les encodages supportés")
            
            # Extraire la structure
            structure = self._extract_structure(content)
            
            # Extraire les articles
            articles = self._extract_articles(content)
            
            # Extraire les mots-clés
            keywords = self._extract_keywords(articles)
            
            return {
                'structure': structure,
                'articles': articles,
                'keywords': keywords,
                'total_articles': len(articles),
                'total_sections': len(structure)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la constitution: {e}")
            raise
    
    def _extract_structure(self, content: str) -> List[Dict]:
        """
        Extrait la structure hiérarchique (parties, chapitres, sections)
        """
        structure = []
        lines = content.split('\n')
        
        current_part = None
        current_chapter = None
        current_section = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Détecter les parties (TITRE I, TITRE II, etc.)
            if re.match(r'^TITRE\s+[IVX]+', line, re.IGNORECASE):
                current_part = {
                    'title': line,
                    'level': 1,
                    'parent_id': None
                }
                structure.append(current_part)
                
            # Détecter les chapitres (CHAPITRE I, CHAPITRE II, etc.)
            elif re.match(r'^CHAPITRE\s+[IVX]+', line, re.IGNORECASE):
                current_chapter = {
                    'title': line,
                    'level': 2,
                    'parent_id': None  # Sera mis à jour après création
                }
                structure.append(current_chapter)
                
            # Détecter les sections
            elif re.match(r'^Section\s+[IVX]+', line, re.IGNORECASE):
                current_section = {
                    'title': line,
                    'level': 3,
                    'parent_id': None  # Sera mis à jour après création
                }
                structure.append(current_section)
        
        return structure
    
    def _extract_articles(self, content: str) -> List[Dict]:
        """
        Extrait tous les articles de la constitution
        """
        articles = []
        
        # Diviser le contenu en lignes
        lines = content.split('\n')
        current_article = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Détecter le début d'un nouvel article
            article_match = re.match(r'^Article\s+(\d+):\s*(.*)$', line, re.IGNORECASE)
            
            if article_match:
                # Sauvegarder l'article précédent s'il existe
                if current_article:
                    article_content = ' '.join(current_content).strip()
                    if article_content:
                        # Nettoyer le contenu
                        article_content = re.sub(r'\s+', ' ', article_content).strip()
                        
                        # Déterminer la catégorie
                        category = self._categorize_article(article_content)
                        
                        # Extraire les mots-clés
                        keywords = self._extract_article_keywords(article_content)
                        
                        article = {
                            'article_number': current_article,
                            'title': None,
                            'content': article_content,
                            'category': category,
                            'keywords': ', '.join(keywords)
                        }
                        
                        articles.append(article)
                
                # Commencer un nouvel article
                current_article = article_match.group(1)
                current_content = [article_match.group(2)]
                
            elif current_article and line:
                # Ajouter la ligne au contenu de l'article actuel
                current_content.append(line)
        
        # Sauvegarder le dernier article
        if current_article:
            article_content = ' '.join(current_content).strip()
            if article_content:
                # Nettoyer le contenu
                article_content = re.sub(r'\s+', ' ', article_content).strip()
                
                # Déterminer la catégorie
                category = self._categorize_article(article_content)
                
                # Extraire les mots-clés
                keywords = self._extract_article_keywords(article_content)
                
                article = {
                    'article_number': current_article,
                    'title': None,
                    'content': article_content,
                    'category': category,
                    'keywords': ', '.join(keywords)
                }
                
                articles.append(article)
        
        # Trier par numéro d'article
        articles.sort(key=lambda x: int(x['article_number']))
        
        return articles
    
    def _categorize_article(self, content: str) -> str:
        """
        Catégorise un article selon son contenu
        """
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['droit', 'liberté', 'garantie']):
            return 'droits_et_libertes'
        elif any(word in content_lower for word in ['président', 'gouvernement', 'ministre']):
            return 'pouvoir_executif'
        elif any(word in content_lower for word in ['parlement', 'assemblée', 'député']):
            return 'pouvoir_legislatif'
        elif any(word in content_lower for word in ['tribunal', 'cour', 'justice']):
            return 'pouvoir_judiciaire'
        elif any(word in content_lower for word in ['élection', 'vote', 'suffrage']):
            return 'elections'
        elif any(word in content_lower for word in ['révision', 'modification', 'amendement']):
            return 'revision_constitutionnelle'
        else:
            return 'general'
    
    def _extract_article_keywords(self, content: str) -> List[str]:
        """
        Extrait les mots-clés d'un article
        """
        # Mots-clés importants de la constitution
        important_words = [
            'droit', 'liberté', 'garantie', 'président', 'gouvernement', 'parlement',
            'tribunal', 'élection', 'vote', 'citoyen', 'république', 'constitution',
            'pouvoir', 'institution', 'responsabilité', 'mandat', 'session'
        ]
        
        content_lower = content.lower()
        keywords = []
        
        for word in important_words:
            if word in content_lower:
                keywords.append(word)
        
        return keywords[:10]  # Limiter à 10 mots-clés
    
    def _extract_keywords(self, articles: List[Dict]) -> List[Dict]:
        """
        Extrait et analyse les mots-clés de tous les articles
        """
        keywords = []
        
        for article in articles:
            article_keywords = article['keywords'].split(', ')
            for keyword in article_keywords:
                if keyword:
                    keywords.append({
                        'keyword': keyword,
                        'article_id': article['article_number'],
                        'context': article['content'][:200] + '...',
                        'frequency': article['content'].lower().count(keyword.lower()),
                        'importance_score': self._calculate_importance_score(keyword, article['content'])
                    })
        
        return keywords
    
    def _calculate_importance_score(self, keyword: str, content: str) -> int:
        """
        Calcule un score d'importance pour un mot-clé
        """
        frequency = content.lower().count(keyword.lower())
        
        # Mots-clés très importants
        if keyword in ['droit', 'liberté', 'président', 'constitution']:
            return min(10, frequency + 5)
        # Mots-clés importants
        elif keyword in ['gouvernement', 'parlement', 'élection', 'citoyen']:
            return min(10, frequency + 3)
        # Mots-clés moyens
        else:
            return min(10, frequency + 1)
    
    def save_to_database(self, parsed_data: Dict) -> bool:
        """
        Sauvegarde les données parsées dans la base de données
        """
        try:
            # Vider les tables existantes
            self.db.query(ConstitutionArticle).delete()
            self.db.query(ConstitutionStructure).delete()
            self.db.query(ConstitutionKeyword).delete()
            
            # Sauvegarder la structure
            for item in parsed_data['structure']:
                structure = ConstitutionStructure(**item)
                self.db.add(structure)
            
            # Sauvegarder les articles
            for article_data in parsed_data['articles']:
                article = ConstitutionArticle(**article_data)
                self.db.add(article)
            
            # Sauvegarder les mots-clés
            for keyword_data in parsed_data['keywords']:
                keyword = ConstitutionKeyword(**keyword_data)
                self.db.add(keyword)
            
            self.db.commit()
            logger.info(f"Données de constitution sauvegardées: {parsed_data['total_articles']} articles")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
