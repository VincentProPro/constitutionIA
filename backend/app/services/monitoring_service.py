import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Service de monitoring pour le système IA
    Collecte et analyse les métriques de performance
    """
    
    def __init__(self):
        self.metrics = {
            "response_times": deque(maxlen=1000),  # Temps de réponse
            "query_types": defaultdict(int),       # Types de questions
            "success_rates": deque(maxlen=1000),   # Taux de succès
            "error_counts": defaultdict(int),      # Compteurs d'erreurs
            "rag_usage": deque(maxlen=1000),      # Utilisation RAG vs fallback
            "user_satisfaction": deque(maxlen=1000)  # Satisfaction utilisateur
        }
        
        self.start_time = datetime.now()
        self.total_queries = 0
        self.successful_queries = 0
        
        # Seuils d'alerte
        self.alert_thresholds = {
            "avg_response_time": 5.0,  # secondes
            "error_rate": 0.1,         # 10%
            "rag_fallback_rate": 0.3   # 30%
        }

    def track_query(self, query: str, response_time: float, success: bool, 
                   query_type: str, used_rag: bool, confidence: float):
        """Enregistre une requête avec ses métriques"""
        timestamp = datetime.now()
        
        # Métriques de base
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        
        # Temps de réponse
        self.metrics["response_times"].append({
            "timestamp": timestamp,
            "response_time": response_time,
            "query": query[:100]  # Limiter la taille
        })
        
        # Type de question
        self.metrics["query_types"][query_type] += 1
        
        # Taux de succès
        self.metrics["success_rates"].append({
            "timestamp": timestamp,
            "success": success
        })
        
        # Utilisation RAG
        self.metrics["rag_usage"].append({
            "timestamp": timestamp,
            "used_rag": used_rag,
            "confidence": confidence
        })
        
        # Log pour debugging
        logger.info(f"Query tracked: {query_type}, {response_time:.2f}s, RAG: {used_rag}, Success: {success}")

    def track_error(self, error_type: str, error_message: str):
        """Enregistre une erreur"""
        self.metrics["error_counts"][error_type] += 1
        logger.error(f"Error tracked: {error_type} - {error_message}")

    def track_user_feedback(self, query_id: str, rating: int, feedback: str = ""):
        """Enregistre le feedback utilisateur"""
        self.metrics["user_satisfaction"].append({
            "timestamp": datetime.now(),
            "rating": rating,
            "feedback": feedback
        })

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance actuelles"""
        if not self.metrics["response_times"]:
            return {
                "performance": {
                    "avg_response_time": 0.0,
                    "max_response_time": 0.0,
                    "min_response_time": 0.0,
                    "success_rate": 0.0,
                    "rag_usage_rate": 0.0
                },
                "usage": {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 1),
                    "popular_query_types": [],
                    "frequent_errors": []
                },
                "quality": {
                    "avg_satisfaction": 0.0,
                    "total_feedback": 0
                },
                "alerts": [],
                "message": "Aucune donnée disponible"
            }
        
        # Calculer les métriques
        response_times = [rt["response_time"] for rt in self.metrics["response_times"]]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Taux de succès
        success_rate = self.successful_queries / self.total_queries if self.total_queries > 0 else 0
        
        # Utilisation RAG
        rag_usage = [r["used_rag"] for r in self.metrics["rag_usage"]]
        rag_usage_rate = sum(rag_usage) / len(rag_usage) if rag_usage else 0
        
        # Types de questions populaires
        popular_query_types = sorted(
            self.metrics["query_types"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Erreurs fréquentes
        frequent_errors = sorted(
            self.metrics["error_counts"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Satisfaction utilisateur
        user_ratings = [u["rating"] for u in self.metrics["user_satisfaction"]]
        avg_satisfaction = sum(user_ratings) / len(user_ratings) if user_ratings else 0
        
        return {
            "performance": {
                "avg_response_time": round(avg_response_time, 2),
                "max_response_time": round(max_response_time, 2),
                "min_response_time": round(min_response_time, 2),
                "success_rate": round(success_rate * 100, 1),
                "rag_usage_rate": round(rag_usage_rate * 100, 1)
            },
            "usage": {
                "total_queries": self.total_queries,
                "successful_queries": self.successful_queries,
                "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 1),
                "popular_query_types": popular_query_types,
                "frequent_errors": frequent_errors
            },
            "quality": {
                "avg_satisfaction": round(avg_satisfaction, 1),
                "total_feedback": len(user_ratings)
            },
            "alerts": self._check_alerts(avg_response_time, success_rate, rag_usage_rate)
        }

    def _check_alerts(self, avg_response_time: float, success_rate: float, rag_usage_rate: float) -> List[str]:
        """Vérifie les seuils d'alerte"""
        alerts = []
        
        if avg_response_time > self.alert_thresholds["avg_response_time"]:
            alerts.append(f"Temps de réponse élevé: {avg_response_time:.2f}s")
        
        if success_rate < (1 - self.alert_thresholds["error_rate"]):
            alerts.append(f"Taux d'erreur élevé: {(1-success_rate)*100:.1f}%")
        
        if rag_usage_rate < (1 - self.alert_thresholds["rag_fallback_rate"]):
            alerts.append(f"Utilisation RAG faible: {rag_usage_rate*100:.1f}%")
        
        return alerts

    def get_recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """Retourne l'activité récente"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_queries = [
            rt for rt in self.metrics["response_times"] 
            if rt["timestamp"] > cutoff_time
        ]
        
        recent_errors = [
            error for error in self.metrics["error_counts"].items()
            if error[1] > 0  # Au moins une erreur
        ]
        
        return {
            "recent_queries_count": len(recent_queries),
            "recent_avg_response_time": sum(rt["response_time"] for rt in recent_queries) / len(recent_queries) if recent_queries else 0,
            "recent_errors": recent_errors,
            "time_period_hours": hours
        }

    def export_metrics(self, filepath: str = None) -> str:
        """Exporte les métriques vers un fichier JSON"""
        if not filepath:
            filepath = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        metrics_data = {
            "export_timestamp": datetime.now().isoformat(),
            "performance_metrics": self.get_performance_metrics(),
            "raw_metrics": {
                "response_times": list(self.metrics["response_times"]),
                "query_types": dict(self.metrics["query_types"]),
                "error_counts": dict(self.metrics["error_counts"]),
                "rag_usage": list(self.metrics["rag_usage"]),
                "user_satisfaction": list(self.metrics["user_satisfaction"])
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            logger.info(f"Métriques exportées vers {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            return ""

    def reset_metrics(self):
        """Réinitialise toutes les métriques"""
        self.metrics = {
            "response_times": deque(maxlen=1000),
            "query_types": defaultdict(int),
            "success_rates": deque(maxlen=1000),
            "error_counts": defaultdict(int),
            "rag_usage": deque(maxlen=1000),
            "user_satisfaction": deque(maxlen=1000)
        }
        self.start_time = datetime.now()
        self.total_queries = 0
        self.successful_queries = 0
        logger.info("Métriques réinitialisées")

# Instance globale du service de monitoring
monitoring_service = MonitoringService() 