"""
Dashboard API Endpoints - MAPAQ Predictive Health Model
Endpoints API REST pour le dashboard MAPAQ (Heures 85-88)

Ce module implémente les endpoints API REST pour exposer les fonctionnalités
du backend dashboard MAPAQ via une interface HTTP standardisée.

Endpoints principaux:
- POST /api/v1/predict : Prédiction de risque pour un restaurant
- GET /api/v1/historical : Données historiques de prédictions
- GET /api/v1/trends : Analyse des tendances temporelles
- GET /api/v1/dashboard : Résumé complet du dashboard
- GET /api/v1/health : Vérification de santé du service

Author: Mouhamed Thiaw
Date: 2025-01-14
Heures: 85-88 (Semaine 3)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
import traceback

# Framework web (Flask avec fallback)
try:
    from flask import Flask, request, jsonify, Blueprint
    from flask_cors import CORS
    from werkzeug.exceptions import BadRequest, InternalServerError
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask non disponible - Mode simulation activé")
    # Classes de fallback pour éviter les erreurs de référence
    class Flask:
        pass
    class Blueprint:
        pass

# Modules MAPAQ
from dashboard import MapaqDashboardBackend, RestaurantData, PredictionResult

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION API ==========

class DashboardAPIConfig:
    """Configuration des endpoints API du dashboard."""
    
    # Endpoints disponibles
    ENDPOINTS = {
        'health': '/api/v1/health',
        'predict': '/api/v1/predict',
        'historical': '/api/v1/historical',
        'trends': '/api/v1/trends',
        'dashboard': '/api/v1/dashboard',
        'restaurants': '/api/v1/restaurants',
        'metrics': '/api/v1/metrics'
    }
    
    # Limites de taux (requêtes par minute)
    RATE_LIMITS = {
        'health': 100,
        'predict': 30,
        'historical': 50,
        'trends': 20,
        'dashboard': 40,
        'restaurants': 60,
        'metrics': 30
    }
    
    # Tailles maximales de contenu
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB
    
    # Configuration CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:8080']

# ========== CLASSE PRINCIPALE API ==========

class MapaqDashboardAPI:
    """
    API REST pour le dashboard MAPAQ.
    
    Expose les fonctionnalités du backend via des endpoints HTTP standardisés.
    """
    
    def __init__(self, dashboard_backend: Optional[MapaqDashboardBackend] = None):
        """
        Initialise l'API dashboard.
        
        Args:
            dashboard_backend: Instance du backend dashboard
        """
        self.backend = dashboard_backend or MapaqDashboardBackend()
        self.app = None
        self.blueprint = None
        
        # Statistiques API
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'endpoints_usage': {},
            'start_time': datetime.now(),
            'last_request': None
        }
        
        logger.info("API Dashboard MAPAQ initialisée")
    
    def create_flask_app(self) -> Optional[Flask]:
        """
        Crée et configure l'application Flask.
        
        Returns:
            Flask: Application Flask configurée ou None si Flask indisponible
        """
        if not FLASK_AVAILABLE:
            logger.warning("Flask non disponible - Impossible de créer l'application")
            return None
        
        app = Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = DashboardAPIConfig.MAX_CONTENT_LENGTH
        
        # Configuration CORS
        CORS(app, origins=DashboardAPIConfig.CORS_ORIGINS)
        
        # Création du blueprint
        self.blueprint = Blueprint('dashboard_api', __name__)
        self._register_endpoints()
        
        # Enregistrement du blueprint
        app.register_blueprint(self.blueprint)
        
        self.app = app
        logger.info("Application Flask créée et configurée")
        return app
    
    def _register_endpoints(self):
        """Enregistre tous les endpoints API."""
        if not self.blueprint:
            return
        
        # Endpoint de santé
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['health'],
            'health_check',
            self.health_check,
            methods=['GET']
        )
        
        # Endpoint de prédiction
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['predict'],
            'predict_risk',
            self.predict_risk,
            methods=['POST']
        )
        
        # Endpoint données historiques
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['historical'],
            'get_historical_data',
            self.get_historical_data,
            methods=['GET']
        )
        
        # Endpoint tendances
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['trends'],
            'get_trends',
            self.get_trends,
            methods=['GET']
        )
        
        # Endpoint résumé dashboard
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['dashboard'],
            'get_dashboard_summary',
            self.get_dashboard_summary,
            methods=['GET']
        )
        
        # Endpoint liste restaurants
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['restaurants'],
            'get_restaurants',
            self.get_restaurants,
            methods=['GET']
        )
        
        # Endpoint métriques API
        self.blueprint.add_url_rule(
            DashboardAPIConfig.ENDPOINTS['metrics'],
            'get_api_metrics',
            self.get_api_metrics,
            methods=['GET']
        )
        
        logger.info(f"Endpoints enregistrés: {len(DashboardAPIConfig.ENDPOINTS)}")
    
    # ========== ENDPOINTS API ==========
    
    def health_check(self):
        """
        Endpoint de vérification de santé du service.
        
        Returns:
            JSON: Statut de santé du service
        """
        try:
            self._update_stats('health', True)
            
            # Test de connectivité backend
            backend_status = "healthy"
            try:
                summary = self.backend.get_dashboard_summary()
                if not summary:
                    backend_status = "degraded"
            except Exception as e:
                backend_status = "unhealthy"
                logger.error(f"Erreur test backend: {e}")
            
            health_data = {
                'status': 'healthy' if backend_status == 'healthy' else 'degraded',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'backend_status': backend_status,
                'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds(),
                'total_requests': self.stats['total_requests']
            }
            
            return self._format_success_response(health_data, "Service en fonctionnement")
            
        except Exception as e:
            self._update_stats('health', False)
            logger.error(f"Erreur health check: {e}")
            return self._format_error_response("Erreur interne du service", 500)
    
    def predict_risk(self):
        """
        Endpoint de prédiction de risque pour un restaurant.
        
        Body JSON attendu:
        {
            "nom": "Nom du restaurant",
            "adresse": "Adresse complète",
            "ville": "Ville",
            "theme": "Type de cuisine",
            "taille": "Petite/Moyenne/Grande"
        }
        
        Returns:
            JSON: Résultat de prédiction avec score et catégorie
        """
        try:
            # Validation de la requête
            if not request.is_json:
                return self._format_error_response("Content-Type doit être application/json", 400)
            
            data = request.get_json()
            if not data:
                return self._format_error_response("Corps de requête JSON requis", 400)
            
            # Validation des champs requis
            required_fields = ['nom', 'adresse', 'ville']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return self._format_error_response(
                    f"Champs requis manquants: {', '.join(missing_fields)}", 400
                )
            
            # Création de l'objet restaurant
            restaurant_data = RestaurantData(
                id=f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                nom=data['nom'],
                theme=data.get('theme', 'Restaurant'),
                taille=data.get('taille', 'Moyenne'),
                zone=data.get('ville', 'Montréal'),
                adresse=data['adresse'],
                score_risque=0.0,  # Sera calculé
                categorie_risque='',  # Sera calculé
                probabilite_infraction=0.0,  # Sera calculé
                derniere_inspection=datetime.now().strftime('%Y-%m-%d'),
                prochaine_inspection=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                historique_infractions=[]
            )
            
            # Génération de la prédiction
            prediction = self.backend.generate_prediction(restaurant_data)
            
            if prediction:
                self._update_stats('predict', True)
                
                # Formatage de la réponse
                prediction_data = {
                    'restaurant': asdict(restaurant_data),
                    'prediction': asdict(prediction),
                    'timestamp': datetime.now().isoformat(),
                    'model_version': '1.0.0'
                }
                
                return self._format_success_response(
                    prediction_data, 
                    f"Prédiction générée: {prediction.category}"
                )
            else:
                self._update_stats('predict', False)
                return self._format_error_response("Impossible de générer la prédiction", 500)
                
        except Exception as e:
            self._update_stats('predict', False)
            logger.error(f"Erreur prédiction: {e}")
            return self._format_error_response("Erreur lors de la prédiction", 500)
    
    def get_historical_data(self):
        """
        Endpoint pour récupérer les données historiques.
        
        Paramètres query optionnels:
        - days: Nombre de jours (défaut: 30)
        - restaurant_id: ID spécifique du restaurant
        - category: Filtrer par catégorie de risque
        
        Returns:
            JSON: Données historiques de prédictions
        """
        try:
            # Extraction des paramètres
            days = int(request.args.get('days', 30))
            restaurant_id = request.args.get('restaurant_id')
            category = request.args.get('category')
            
            # Validation des paramètres
            if days < 1 or days > 365:
                return self._format_error_response("Paramètre 'days' doit être entre 1 et 365", 400)
            
            # Récupération des données historiques
            historical_data = self.backend.get_historical_data(
                days=days,
                restaurant_id=restaurant_id
            )
            
            # Filtrage par catégorie si spécifié
            if category and historical_data:
                historical_data = [
                    entry for entry in historical_data 
                    if entry.get('category', '').lower() == category.lower()
                ]
            
            self._update_stats('historical', True)
            
            response_data = {
                'historical_data': historical_data or [],
                'filters': {
                    'days': days,
                    'restaurant_id': restaurant_id,
                    'category': category
                },
                'total_records': len(historical_data) if historical_data else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            return self._format_success_response(
                response_data,
                f"Données historiques récupérées: {len(historical_data or [])} enregistrements"
            )
            
        except ValueError as e:
            self._update_stats('historical', False)
            return self._format_error_response(f"Paramètre invalide: {e}", 400)
        except Exception as e:
            self._update_stats('historical', False)
            logger.error(f"Erreur données historiques: {e}")
            return self._format_error_response("Erreur lors de la récupération des données", 500)
    
    def get_trends(self):
        """
        Endpoint pour l'analyse des tendances.
        
        Paramètres query optionnels:
        - period: Période d'analyse (day/week/month/year, défaut: month)
        - metric: Métrique à analyser (score/category/volume, défaut: score)
        
        Returns:
            JSON: Données de tendances et analyses
        """
        try:
            # Extraction des paramètres
            period = request.args.get('period', 'month')
            metric = request.args.get('metric', 'score')
            
            # Validation des paramètres
            valid_periods = ['day', 'week', 'month', 'year']
            valid_metrics = ['score', 'category', 'volume']
            
            if period not in valid_periods:
                return self._format_error_response(
                    f"Période invalide. Valeurs acceptées: {', '.join(valid_periods)}", 400
                )
            
            if metric not in valid_metrics:
                return self._format_error_response(
                    f"Métrique invalide. Valeurs acceptées: {', '.join(valid_metrics)}", 400
                )
            
            # Récupération des tendances
            trends_data = self.backend.get_trends_data(period=period)
            
            # Enrichissement avec analyse de métrique
            if trends_data:
                trends_data['analysis'] = self._analyze_trends(trends_data, metric)
                trends_data['recommendations'] = self._generate_trend_recommendations(trends_data)
            
            self._update_stats('trends', True)
            
            response_data = {
                'trends': trends_data or {},
                'parameters': {
                    'period': period,
                    'metric': metric
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return self._format_success_response(
                response_data,
                f"Tendances analysées pour la période: {period}"
            )
            
        except Exception as e:
            self._update_stats('trends', False)
            logger.error(f"Erreur analyse tendances: {e}")
            return self._format_error_response("Erreur lors de l'analyse des tendances", 500)
    
    def get_dashboard_summary(self):
        """
        Endpoint pour le résumé complet du dashboard.
        
        Returns:
            JSON: Résumé complet avec statistiques et métriques
        """
        try:
            # Récupération du résumé dashboard
            summary = self.backend.get_dashboard_summary()
            
            if summary:
                # Enrichissement avec métriques API
                summary['api_metrics'] = {
                    'total_requests': self.stats['total_requests'],
                    'success_rate': self._calculate_success_rate(),
                    'uptime_hours': round((datetime.now() - self.stats['start_time']).total_seconds() / 3600, 2),
                    'last_request': self.stats['last_request']
                }
                
                # Ajout de recommandations
                summary['recommendations'] = self._generate_dashboard_recommendations(summary)
                
                self._update_stats('dashboard', True)
                
                return self._format_success_response(
                    summary,
                    "Résumé dashboard généré avec succès"
                )
            else:
                self._update_stats('dashboard', False)
                return self._format_error_response("Impossible de générer le résumé", 500)
                
        except Exception as e:
            self._update_stats('dashboard', False)
            logger.error(f"Erreur résumé dashboard: {e}")
            return self._format_error_response("Erreur lors de la génération du résumé", 500)
    
    def get_restaurants(self):
        """
        Endpoint pour lister les restaurants.
        
        Paramètres query optionnels:
        - limit: Nombre maximum de résultats (défaut: 50)
        - offset: Décalage pour pagination (défaut: 0)
        - category: Filtrer par catégorie de risque
        
        Returns:
            JSON: Liste des restaurants avec pagination
        """
        try:
            # Extraction des paramètres de pagination
            limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
            offset = max(int(request.args.get('offset', 0)), 0)
            category = request.args.get('category')
            
            # Récupération des restaurants (simulation)
            restaurants = self._get_restaurants_list(limit, offset, category)
            
            self._update_stats('restaurants', True)
            
            response_data = {
                'restaurants': restaurants,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': len(restaurants),
                    'has_more': len(restaurants) == limit
                },
                'filters': {
                    'category': category
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return self._format_success_response(
                response_data,
                f"Restaurants récupérés: {len(restaurants)}"
            )
            
        except ValueError as e:
            self._update_stats('restaurants', False)
            return self._format_error_response(f"Paramètre invalide: {e}", 400)
        except Exception as e:
            self._update_stats('restaurants', False)
            logger.error(f"Erreur liste restaurants: {e}")
            return self._format_error_response("Erreur lors de la récupération des restaurants", 500)
    
    def get_api_metrics(self):
        """
        Endpoint pour les métriques de l'API.
        
        Returns:
            JSON: Métriques détaillées de l'API
        """
        try:
            metrics = {
                'general': {
                    'total_requests': self.stats['total_requests'],
                    'successful_requests': self.stats['successful_requests'],
                    'failed_requests': self.stats['failed_requests'],
                    'success_rate': self._calculate_success_rate(),
                    'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds()
                },
                'endpoints': self.stats['endpoints_usage'],
                'performance': {
                    'requests_per_hour': self._calculate_requests_per_hour(),
                    'average_response_time': '< 100ms',  # Estimation
                    'peak_hour': self._get_peak_hour()
                },
                'timestamp': datetime.now().isoformat()
            }
            
            self._update_stats('metrics', True)
            
            return self._format_success_response(
                metrics,
                "Métriques API récupérées"
            )
            
        except Exception as e:
            self._update_stats('metrics', False)
            logger.error(f"Erreur métriques API: {e}")
            return self._format_error_response("Erreur lors de la récupération des métriques", 500)
    
    # ========== MÉTHODES UTILITAIRES ==========
    
    def _update_stats(self, endpoint: str, success: bool):
        """Met à jour les statistiques d'utilisation."""
        self.stats['total_requests'] += 1
        self.stats['last_request'] = datetime.now().isoformat()
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # Statistiques par endpoint
        if endpoint not in self.stats['endpoints_usage']:
            self.stats['endpoints_usage'][endpoint] = {'total': 0, 'success': 0, 'failed': 0}
        
        self.stats['endpoints_usage'][endpoint]['total'] += 1
        if success:
            self.stats['endpoints_usage'][endpoint]['success'] += 1
        else:
            self.stats['endpoints_usage'][endpoint]['failed'] += 1
    
    def _calculate_success_rate(self) -> float:
        """Calcule le taux de succès des requêtes."""
        if self.stats['total_requests'] == 0:
            return 100.0
        return round((self.stats['successful_requests'] / self.stats['total_requests']) * 100, 2)
    
    def _calculate_requests_per_hour(self) -> float:
        """Calcule le nombre de requêtes par heure."""
        uptime_hours = (datetime.now() - self.stats['start_time']).total_seconds() / 3600
        if uptime_hours == 0:
            return 0.0
        return round(self.stats['total_requests'] / uptime_hours, 2)
    
    def _get_peak_hour(self) -> str:
        """Retourne l'heure de pointe estimée."""
        current_hour = datetime.now().hour
        return f"{current_hour}:00-{current_hour + 1}:00"
    
    def _analyze_trends(self, trends_data: Dict, metric: str) -> Dict:
        """Analyse les tendances pour une métrique donnée."""
        analysis = {
            'metric': metric,
            'trend_direction': 'stable',
            'change_percentage': 0.0,
            'insights': []
        }
        
        if metric == 'score':
            avg_score = trends_data.get('average_score', 50)
            if avg_score > 70:
                analysis['trend_direction'] = 'increasing'
                analysis['insights'].append("Scores de risque en hausse - surveillance recommandée")
            elif avg_score < 30:
                analysis['trend_direction'] = 'decreasing'
                analysis['insights'].append("Scores de risque en baisse - amélioration notable")
        
        return analysis
    
    def _generate_trend_recommendations(self, trends_data: Dict) -> List[str]:
        """Génère des recommandations basées sur les tendances."""
        recommendations = []
        
        total_predictions = trends_data.get('total_predictions', 0)
        if total_predictions > 100:
            recommendations.append("Volume élevé de prédictions - considérer l'optimisation des performances")
        
        avg_score = trends_data.get('average_score', 50)
        if avg_score > 60:
            recommendations.append("Scores moyens élevés - intensifier les inspections préventives")
        
        return recommendations
    
    def _generate_dashboard_recommendations(self, summary: Dict) -> List[str]:
        """Génère des recommandations pour le dashboard."""
        recommendations = []
        
        high_risk_count = summary.get('high_risk_restaurants', 0)
        if high_risk_count > 5:
            recommendations.append(f"Attention: {high_risk_count} restaurants à risque élevé nécessitent une inspection urgente")
        
        avg_score = summary.get('average_score', 50)
        if avg_score > 70:
            recommendations.append("Score moyen élevé - réviser les critères d'évaluation")
        
        return recommendations
    
    def _get_restaurants_list(self, limit: int, offset: int, category: Optional[str]) -> List[Dict]:
        """Récupère une liste simulée de restaurants."""
        # Simulation de données restaurants
        restaurants = []
        for i in range(offset, offset + limit):
            restaurant = {
                'id': f"rest_{i + 1}",
                'nom': f"Restaurant {i + 1}",
                'adresse': f"{100 + i} Rue Example",
                'ville': 'Montréal',
                'theme': 'Restaurant',
                'score': round(30 + (i % 70), 1),
                'category': ['Faible', 'Moyen', 'Eleve', 'Critique'][i % 4],
                'last_inspection': (datetime.now() - timedelta(days=i % 30)).isoformat()
            }
            
            # Filtrage par catégorie
            if not category or restaurant['category'].lower() == category.lower():
                restaurants.append(restaurant)
        
        return restaurants[:limit]
    
    def _format_success_response(self, data: Any, message: str = "Succès") -> Dict:
        """Formate une réponse de succès standardisée."""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_error_response(self, message: str, status_code: int = 400) -> tuple:
        """Formate une réponse d'erreur standardisée."""
        error_response = {
            'success': False,
            'error': message,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        
        if FLASK_AVAILABLE:
            return jsonify(error_response), status_code
        else:
            return error_response, status_code

# ========== SERVEUR DE DÉVELOPPEMENT ==========

class DevelopmentServer:
    """Serveur de développement pour tester les endpoints."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.api = MapaqDashboardAPI()
        self.app = None
    
    def start(self):
        """Démarre le serveur de développement."""
        if not FLASK_AVAILABLE:
            logger.error("Flask non disponible - Impossible de démarrer le serveur")
            return self._simulate_server()
        
        self.app = self.api.create_flask_app()
        if self.app:
            logger.info(f"Démarrage serveur sur http://localhost:{self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=True)
        else:
            logger.error("Impossible de créer l'application Flask")
    
    def _simulate_server(self):
        """Simule le serveur pour les tests sans Flask."""
        logger.info("=== SIMULATION SERVEUR DASHBOARD API ===")
        logger.info(f"Serveur simulé sur port {self.port}")
        
        # Test des endpoints principaux
        test_endpoints = [
            ('GET', '/api/v1/health', {}),
            ('POST', '/api/v1/predict', {
                'nom': 'Restaurant Test API',
                'adresse': '123 Rue Test',
                'ville': 'Montréal'
            }),
            ('GET', '/api/v1/dashboard', {}),
            ('GET', '/api/v1/historical?days=7', {}),
            ('GET', '/api/v1/trends?period=month', {})
        ]
        
        for method, endpoint, data in test_endpoints:
            logger.info(f"\n--- TEST {method} {endpoint} ---")
            try:
                if method == 'POST' and 'predict' in endpoint:
                    # Simulation de requête POST
                    class MockRequest:
                        def __init__(self, json_data):
                            self.json_data = json_data
                            self.is_json = True
                        def get_json(self):
                            return self.json_data
                    
                    # Temporairement remplacer request
                    import sys
                    original_request = getattr(sys.modules[__name__], 'request', None)
                    sys.modules[__name__].request = MockRequest(data)
                    
                    result = self.api.predict_risk()
                    
                    # Restaurer request
                    if original_request:
                        sys.modules[__name__].request = original_request
                elif method == 'GET':
                    # Simulation de requête GET avec paramètres
                    class MockArgs:
                        def __init__(self, params):
                            self.params = params
                        def get(self, key, default=None):
                            return self.params.get(key, default)
                    
                    class MockRequestGet:
                        def __init__(self, params):
                            self.args = MockArgs(params)
                    
                    # Extraction des paramètres de l'URL
                    params = {}
                    if '?' in endpoint:
                        endpoint_base, query_string = endpoint.split('?', 1)
                        for param in query_string.split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                params[key] = value
                    
                    # Temporairement remplacer request
                    import sys
                    original_request = getattr(sys.modules[__name__], 'request', None)
                    sys.modules[__name__].request = MockRequestGet(params)
                    
                    if 'historical' in endpoint:
                        result = self.api.get_historical_data()
                    elif 'trends' in endpoint:
                        result = self.api.get_trends()
                    elif 'health' in endpoint:
                        result = self.api.health_check()
                    elif 'dashboard' in endpoint:
                        result = self.api.get_dashboard_summary()
                    else:
                        result = {'message': 'Endpoint simulé'}
                    
                    # Restaurer request
                    if original_request:
                        sys.modules[__name__].request = original_request
                
                logger.info(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
            except Exception as e:
                logger.error(f"Erreur test {endpoint}: {e}")
        
        logger.info("\n=== MÉTRIQUES API ===")
        metrics = self.api.get_api_metrics()
        logger.info(json.dumps(metrics, indent=2, ensure_ascii=False))

# ========== POINT D'ENTRÉE ==========

def create_dashboard_api(dashboard_backend: Optional[MapaqDashboardBackend] = None) -> MapaqDashboardAPI:
    """
    Crée une instance de l'API dashboard.
    
    Args:
        dashboard_backend: Instance du backend dashboard
        
    Returns:
        MapaqDashboardAPI: Instance de l'API configurée
    """
    return MapaqDashboardAPI(dashboard_backend)

def main():
    """Point d'entrée principal pour les tests."""
    logger.info("=== DASHBOARD API ENDPOINTS - MAPAQ ===")
    logger.info("Heures 85-88: Implémentation endpoints API REST")
    
    # Création et test du serveur
    server = DevelopmentServer(port=8080)
    server.start()

if __name__ == "__main__":
    main()
