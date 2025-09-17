"""
API Endpoints Configuration
Configuration des endpoints API pour l'intégration Track-C

Ce module définit tous les endpoints API standardisés pour la communication
entre Track-B (MAPAQ) et Track-C (Integration Utils).

Author: Mouhamed Thiaw
Date: 2025-01-14
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import BadRequest, InternalServerError
import redis
from functools import wraps

# Configuration
from config import IntegrationConfig, APIConfig

# Configuration logging
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ENDPOINTS ==========

class EndpointConfig:
    """Configuration centralisée des endpoints API."""
    
    # Endpoints principaux
    ENDPOINTS = {
        'health': '/api/v1/health',
        'risk_prediction': '/api/v1/predict-risk',
        'geocoding': '/api/v1/geocode',
        'theme_classification': '/api/v1/classify-theme',
        'historical_data': '/api/v1/historical',
        'trends': '/api/v1/trends',
        'batch_processing': '/api/v1/batch',
        'status': '/api/v1/status'
    }
    
    # Méthodes HTTP autorisées par endpoint
    METHODS = {
        'health': ['GET'],
        'risk_prediction': ['POST'],
        'geocoding': ['POST'],
        'theme_classification': ['POST'],
        'historical_data': ['GET'],
        'trends': ['GET'],
        'batch_processing': ['POST'],
        'status': ['GET']
    }
    
    # Limites de taux par endpoint (requêtes/minute)
    RATE_LIMITS = {
        'health': "100/minute",
        'risk_prediction': "30/minute",
        'geocoding': "50/minute",
        'theme_classification': "40/minute",
        'historical_data': "20/minute",
        'trends': "10/minute",
        'batch_processing': "5/minute",
        'status': "60/minute"
    }
    
    # Tailles maximales des requêtes (en bytes)
    MAX_CONTENT_LENGTH = {
        'default': 1024 * 1024,  # 1MB
        'batch_processing': 10 * 1024 * 1024,  # 10MB
        'risk_prediction': 512 * 1024  # 512KB
    }

# ========== DÉCORATEURS POUR ENDPOINTS ==========

def handle_errors(f):
    """Décorateur pour la gestion standardisée des erreurs."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BadRequest as e:
            logger.warning(f"Bad request in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid request format',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'timestamp': datetime.now().isoformat()
            }), 500
    return decorated_function

def validate_content_type(content_type='application/json'):
    """Décorateur pour valider le Content-Type."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.content_type != content_type:
                return jsonify({
                    'success': False,
                    'error': f'Content-Type must be {content_type}',
                    'timestamp': datetime.now().isoformat()
                }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request(f):
    """Décorateur pour logger les requêtes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        logger.info(f"Request {f.__name__} from {client_ip} - {user_agent}")
        
        try:
            result = f(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Request {f.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Request {f.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    return decorated_function

# ========== CLASSE GESTIONNAIRE D'ENDPOINTS ==========

class APIEndpointManager:
    """
    Gestionnaire centralisé des endpoints API.
    Gère la configuration, la validation et le routage des endpoints.
    """
    
    def __init__(self, app: Flask = None):
        """
        Initialise le gestionnaire d'endpoints.
        
        Args:
            app: Instance Flask (optionnelle)
        """
        self.app = app
        self.blueprint = Blueprint('api', __name__)
        self.limiter = None
        self.redis_client = None
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'endpoints_stats': {},
            'start_time': datetime.now()
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialise l'application Flask avec les endpoints.
        
        Args:
            app: Instance Flask
        """
        self.app = app
        
        # Configuration du rate limiting
        self.limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200/hour", "50/minute"]
        )
        
        # Configuration Redis pour le cache (optionnel)
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # Test de connexion
            logger.info("Redis connecté avec succès")
        except Exception as e:
            logger.warning(f"Redis non disponible: {str(e)}")
            self.redis_client = None
        
        # Enregistrement du blueprint
        app.register_blueprint(self.blueprint)
        
        # Configuration des endpoints
        self._setup_endpoints()
        
        logger.info("APIEndpointManager initialisé avec succès")
    
    def _setup_endpoints(self):
        """Configure tous les endpoints API."""
        
        # Endpoint de santé
        @self.blueprint.route(EndpointConfig.ENDPOINTS['health'], methods=['GET'])
        @self.limiter.limit(EndpointConfig.RATE_LIMITS['health'])
        @handle_errors
        @log_request
        def health_check():
            """Endpoint de vérification de santé du service."""
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            
            health_data = {
                'service': 'Track-B MAPAQ API',
                'status': 'healthy',
                'version': '1.0.0',
                'uptime_seconds': uptime,
                'timestamp': datetime.now().isoformat(),
                'endpoints': list(EndpointConfig.ENDPOINTS.keys()),
                'statistics': self.stats,
                'dependencies': {
                    'redis': self.redis_client is not None,
                    'database': True  # Simulation
                }
            }
            
            return jsonify({
                'success': True,
                'data': health_data
            })
        
        # Endpoint de statut détaillé
        @self.blueprint.route(EndpointConfig.ENDPOINTS['status'], methods=['GET'])
        @self.limiter.limit(EndpointConfig.RATE_LIMITS['status'])
        @handle_errors
        @log_request
        def detailed_status():
            """Endpoint de statut détaillé du système."""
            return jsonify({
                'success': True,
                'data': {
                    'system_info': {
                        'python_version': os.sys.version,
                        'platform': os.name,
                        'process_id': os.getpid()
                    },
                    'configuration': {
                        'endpoints_count': len(EndpointConfig.ENDPOINTS),
                        'rate_limits_enabled': True,
                        'redis_enabled': self.redis_client is not None
                    },
                    'performance': self._get_performance_metrics(),
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        # Endpoint de traitement par lot
        @self.blueprint.route(EndpointConfig.ENDPOINTS['batch_processing'], methods=['POST'])
        @self.limiter.limit(EndpointConfig.RATE_LIMITS['batch_processing'])
        @validate_content_type('application/json')
        @handle_errors
        @log_request
        def batch_processing():
            """Endpoint pour le traitement par lot de restaurants."""
            try:
                data = request.get_json()
                
                if not data or 'restaurants' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Field "restaurants" is required',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                restaurants = data['restaurants']
                if not isinstance(restaurants, list) or len(restaurants) == 0:
                    return jsonify({
                        'success': False,
                        'error': 'Field "restaurants" must be a non-empty list',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # Limitation du nombre de restaurants par lot
                max_batch_size = 50
                if len(restaurants) > max_batch_size:
                    return jsonify({
                        'success': False,
                        'error': f'Batch size cannot exceed {max_batch_size} restaurants',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # Traitement du lot (simulation)
                results = []
                for i, restaurant in enumerate(restaurants):
                    try:
                        # Validation basique
                        if not isinstance(restaurant, dict) or 'name' not in restaurant:
                            results.append({
                                'index': i,
                                'success': False,
                                'error': 'Invalid restaurant data'
                            })
                            continue
                        
                        # Simulation de traitement
                        results.append({
                            'index': i,
                            'success': True,
                            'restaurant_id': f"batch_{i}_{hash(restaurant['name'])}",
                            'processed_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        results.append({
                            'index': i,
                            'success': False,
                            'error': str(e)
                        })
                
                # Statistiques du lot
                successful = sum(1 for r in results if r['success'])
                failed = len(results) - successful
                
                return jsonify({
                    'success': True,
                    'data': {
                        'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'total_processed': len(results),
                        'successful': successful,
                        'failed': failed,
                        'results': results,
                        'processing_time': datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur traitement par lot: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Batch processing failed',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Endpoint de tendances
        @self.blueprint.route(EndpointConfig.ENDPOINTS['trends'], methods=['GET'])
        @self.limiter.limit(EndpointConfig.RATE_LIMITS['trends'])
        @handle_errors
        @log_request
        def get_trends():
            """Endpoint pour récupérer les tendances."""
            try:
                # Paramètres de requête
                period = request.args.get('period', 'month')  # day, week, month, year
                category = request.args.get('category', 'all')  # risk, theme, geographic
                
                # Validation des paramètres
                valid_periods = ['day', 'week', 'month', 'year']
                valid_categories = ['all', 'risk', 'theme', 'geographic']
                
                if period not in valid_periods:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid period. Must be one of: {valid_periods}',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                if category not in valid_categories:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid category. Must be one of: {valid_categories}',
                        'timestamp': datetime.now().isoformat()
                    }), 400
                
                # Génération des tendances (simulation)
                trends_data = self._generate_trends_data(period, category)
                
                return jsonify({
                    'success': True,
                    'data': trends_data
                })
                
            except Exception as e:
                logger.error(f"Erreur récupération tendances: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to retrieve trends',
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def _get_performance_metrics(self) -> Dict:
        """
        Récupère les métriques de performance.
        
        Returns:
            Dict: Métriques de performance
        """
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (
                self.stats['successful_requests'] / max(self.stats['total_requests'], 1) * 100
            ),
            'requests_per_minute': (
                self.stats['total_requests'] / max(uptime / 60, 1)
            ),
            'endpoints_stats': self.stats['endpoints_stats']
        }
    
    def _generate_trends_data(self, period: str, category: str) -> Dict:
        """
        Génère des données de tendances simulées.
        
        Args:
            period: Période d'analyse
            category: Catégorie de tendances
            
        Returns:
            Dict: Données de tendances
        """
        # Simulation de données de tendances
        base_data = {
            'period': period,
            'category': category,
            'generated_at': datetime.now().isoformat(),
            'data_points': []
        }
        
        if category in ['all', 'risk']:
            base_data['risk_trends'] = {
                'high_risk_percentage': 25.3,
                'medium_risk_percentage': 45.7,
                'low_risk_percentage': 29.0,
                'trend_direction': 'stable'
            }
        
        if category in ['all', 'theme']:
            base_data['theme_trends'] = {
                'most_common_themes': ['fast_food', 'cafe', 'sushi'],
                'emerging_themes': ['vegan', 'fusion'],
                'theme_risk_correlation': {
                    'fast_food': 'high',
                    'fine_dining': 'low',
                    'cafe': 'medium'
                }
            }
        
        if category in ['all', 'geographic']:
            base_data['geographic_trends'] = {
                'high_risk_areas': ['downtown', 'industrial'],
                'low_risk_areas': ['residential', 'suburban'],
                'geographic_distribution': {
                    'north': 23,
                    'south': 28,
                    'east': 25,
                    'west': 24
                }
            }
        
        return base_data
    
    def update_stats(self, endpoint: str, success: bool):
        """
        Met à jour les statistiques d'utilisation.
        
        Args:
            endpoint: Nom de l'endpoint
            success: Succès de la requête
        """
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # Statistiques par endpoint
        if endpoint not in self.stats['endpoints_stats']:
            self.stats['endpoints_stats'][endpoint] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.stats['endpoints_stats'][endpoint]['total'] += 1
        if success:
            self.stats['endpoints_stats'][endpoint]['successful'] += 1
        else:
            self.stats['endpoints_stats'][endpoint]['failed'] += 1

# ========== UTILITAIRES D'ENDPOINTS ==========

class EndpointUtils:
    """Utilitaires pour les endpoints API."""
    
    @staticmethod
    def validate_pagination(request) -> Dict:
        """
        Valide et extrait les paramètres de pagination.
        
        Args:
            request: Objet request Flask
            
        Returns:
            Dict: Paramètres de pagination validés
        """
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # Validation des limites
            page = max(1, page)
            per_page = max(1, min(per_page, 100))  # Max 100 éléments par page
            
            offset = (page - 1) * per_page
            
            return {
                'page': page,
                'per_page': per_page,
                'offset': offset,
                'valid': True
            }
            
        except (ValueError, TypeError):
            return {
                'page': 1,
                'per_page': 20,
                'offset': 0,
                'valid': False,
                'error': 'Invalid pagination parameters'
            }
    
    @staticmethod
    def format_error_response(error_message: str, error_code: int = 400, 
                            details: Optional[Dict] = None) -> Dict:
        """
        Formate une réponse d'erreur standardisée.
        
        Args:
            error_message: Message d'erreur
            error_code: Code d'erreur HTTP
            details: Détails additionnels
            
        Returns:
            Dict: Réponse d'erreur formatée
        """
        response = {
            'success': False,
            'error': error_message,
            'error_code': error_code,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            response['details'] = details
        
        return response
    
    @staticmethod
    def format_success_response(data: Any, message: Optional[str] = None, 
                              metadata: Optional[Dict] = None) -> Dict:
        """
        Formate une réponse de succès standardisée.
        
        Args:
            data: Données de la réponse
            message: Message de succès optionnel
            metadata: Métadonnées additionnelles
            
        Returns:
            Dict: Réponse de succès formatée
        """
        response = {
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        if message:
            response['message'] = message
        
        if metadata:
            response['metadata'] = metadata
        
        return response

# ========== POINT D'ENTRÉE ==========

def create_api_blueprint() -> Blueprint:
    """
    Crée et configure le blueprint API.
    
    Returns:
        Blueprint: Blueprint API configuré
    """
    manager = APIEndpointManager()
    return manager.blueprint

if __name__ == "__main__":
    # Test des endpoints (développement uniquement)
    from flask import Flask
    
    app = Flask(__name__)
    manager = APIEndpointManager(app)
    
    print("Endpoints configurés:")
    for name, path in EndpointConfig.ENDPOINTS.items():
        methods = EndpointConfig.METHODS.get(name, ['GET'])
        print(f"  {name}: {path} [{', '.join(methods)}]")
    
    app.run(debug=True, port=8080)
