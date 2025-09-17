"""
Track-C Integration Module
Module d'intégration avec Track-C (Integration & Utilities)

Ce module gère la communication entre Track-B (MAPAQ) et Track-C,
fournissant les interfaces API standardisées pour l'intégration inter-projets.

Author: Mouhamed Thiaw
Date: 2025-01-14
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError
import time
from functools import wraps

# Configuration
from config import IntegrationConfig, APIConfig, LoggingConfig

# Modules Track-B
from data_ingest import DataIngestor
from data_cleaner import DataCleaner
from address_dict import AddressNormalizer
from theme_dict import ThemeClassifier

# Configuration logging
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LOG_LEVEL),
    format=LoggingConfig.LOG_FORMAT,
    handlers=[
        logging.FileHandler(os.path.join(LoggingConfig.LOG_DIR, 'track_c_integration.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== DATACLASSES POUR RÉPONSES STANDARDISÉES ==========

@dataclass
class APIResponse:
    """Structure standardisée pour toutes les réponses API."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class RiskPrediction:
    """Structure pour les prédictions de risque."""
    restaurant_id: str
    risk_score: float
    risk_category: str
    confidence: float
    factors: List[str]
    geographic_data: Optional[Dict] = None
    theme_data: Optional[Dict] = None

@dataclass
class GeocodeResult:
    """Structure pour les résultats de géocodage."""
    original_address: str
    normalized_address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = 0.0
    source: str = "unknown"

@dataclass
class ThemeClassification:
    """Structure pour la classification thématique."""
    restaurant_name: str
    detected_theme: str
    confidence: float
    keywords_found: List[str]
    category: str

# ========== SCHÉMAS MARSHMALLOW POUR VALIDATION ==========

class RestaurantInputSchema(Schema):
    """Schéma de validation pour les données d'entrée restaurant."""
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    address = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    theme = fields.Str(missing="")
    inspection_history = fields.List(fields.Dict(), missing=[])
    additional_data = fields.Dict(missing={})

class GeocodeInputSchema(Schema):
    """Schéma pour les requêtes de géocodage."""
    address = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    force_refresh = fields.Bool(missing=False)

class ThemeInputSchema(Schema):
    """Schéma pour la classification thématique."""
    restaurant_name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    description = fields.Str(missing="")
    additional_keywords = fields.List(fields.Str(), missing=[])

# ========== DÉCORATEURS UTILITAIRES ==========

def measure_time(f):
    """Décorateur pour mesurer le temps d'exécution."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            if hasattr(result, 'execution_time'):
                result.execution_time = execution_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erreur dans {f.__name__} après {execution_time:.3f}s: {str(e)}")
            raise
    return decorated_function

def validate_api_key(f):
    """Décorateur pour valider les clés API."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in IntegrationConfig.VALID_API_KEYS:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'timestamp': datetime.now().isoformat()
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ========== CLASSE PRINCIPALE D'INTÉGRATION ==========

class TrackCIntegration:
    """
    Classe principale pour l'intégration avec Track-C.
    Gère les communications et la standardisation des données.
    """
    
    def __init__(self):
        """Initialise l'intégration Track-C."""
        self.app = Flask(__name__)
        CORS(self.app, origins=IntegrationConfig.CORS_ORIGINS)
        
        # Initialisation des modules Track-B
        self.data_ingestor = DataIngestor()
        self.data_cleaner = DataCleaner()
        self.address_normalizer = AddressNormalizer()
        self.theme_classifier = ThemeClassifier()
        
        # Configuration des routes
        self._setup_routes()
        
        # Statistiques
        self.stats = {
            'requests_processed': 0,
            'errors_count': 0,
            'average_response_time': 0.0,
            'start_time': datetime.now()
        }
        
        logger.info("TrackCIntegration initialisé avec succès")
    
    def _setup_routes(self):
        """Configure toutes les routes API."""
        
        @self.app.route('/api/v1/health', methods=['GET'])
        def health_check():
            """Endpoint de vérification de santé."""
            return jsonify({
                'success': True,
                'service': 'Track-B MAPAQ Integration',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            })
        
        @self.app.route('/api/v1/predict-risk', methods=['POST'])
        @validate_api_key
        @measure_time
        def predict_risk():
            """Endpoint principal pour la prédiction de risque."""
            try:
                # Validation des données d'entrée
                schema = RestaurantInputSchema()
                data = schema.load(request.json)
                
                # Traitement complet
                result = self._process_risk_prediction(data)
                
                self.stats['requests_processed'] += 1
                
                return jsonify(asdict(APIResponse(
                    success=True,
                    data=asdict(result)
                )))
                
            except ValidationError as e:
                self.stats['errors_count'] += 1
                logger.warning(f"Erreur de validation: {e.messages}")
                return jsonify(asdict(APIResponse(
                    success=False,
                    error=f"Données invalides: {e.messages}"
                ))), 400
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"Erreur prédiction risque: {str(e)}")
                return jsonify(asdict(APIResponse(
                    success=False,
                    error="Erreur interne du serveur"
                ))), 500
        
        @self.app.route('/api/v1/geocode', methods=['POST'])
        @validate_api_key
        @measure_time
        def geocode_address():
            """Endpoint pour le géocodage d'adresses."""
            try:
                schema = GeocodeInputSchema()
                data = schema.load(request.json)
                
                result = self._process_geocoding(data['address'], data['force_refresh'])
                
                self.stats['requests_processed'] += 1
                
                return jsonify(asdict(APIResponse(
                    success=True,
                    data=asdict(result)
                )))
                
            except ValidationError as e:
                self.stats['errors_count'] += 1
                return jsonify(asdict(APIResponse(
                    success=False,
                    error=f"Données invalides: {e.messages}"
                ))), 400
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"Erreur géocodage: {str(e)}")
                return jsonify(asdict(APIResponse(
                    success=False,
                    error="Erreur de géocodage"
                ))), 500
        
        @self.app.route('/api/v1/classify-theme', methods=['POST'])
        @validate_api_key
        @measure_time
        def classify_theme():
            """Endpoint pour la classification thématique."""
            try:
                schema = ThemeInputSchema()
                data = schema.load(request.json)
                
                result = self._process_theme_classification(data)
                
                self.stats['requests_processed'] += 1
                
                return jsonify(asdict(APIResponse(
                    success=True,
                    data=asdict(result)
                )))
                
            except ValidationError as e:
                self.stats['errors_count'] += 1
                return jsonify(asdict(APIResponse(
                    success=False,
                    error=f"Données invalides: {e.messages}"
                ))), 400
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"Erreur classification thème: {str(e)}")
                return jsonify(asdict(APIResponse(
                    success=False,
                    error="Erreur de classification"
                ))), 500
        
        @self.app.route('/api/v1/historical', methods=['GET'])
        @validate_api_key
        def get_historical_data():
            """Endpoint pour récupérer les données historiques."""
            try:
                restaurant_id = request.args.get('restaurant_id')
                date_from = request.args.get('date_from')
                date_to = request.args.get('date_to')
                
                result = self._get_historical_data(restaurant_id, date_from, date_to)
                
                return jsonify(asdict(APIResponse(
                    success=True,
                    data=result
                )))
                
            except Exception as e:
                logger.error(f"Erreur données historiques: {str(e)}")
                return jsonify(asdict(APIResponse(
                    success=False,
                    error="Erreur récupération données historiques"
                ))), 500
    
    @measure_time
    def _process_risk_prediction(self, data: Dict) -> RiskPrediction:
        """
        Traite une prédiction de risque complète.
        
        Args:
            data: Données du restaurant
            
        Returns:
            RiskPrediction: Résultat de la prédiction
        """
        logger.info(f"Traitement prédiction risque pour: {data['name']}")
        
        # 1. Géocodage de l'adresse
        geocode_result = self._process_geocoding(data['address'])
        
        # 2. Classification thématique
        theme_result = self._process_theme_classification({
            'restaurant_name': data['name'],
            'description': data.get('theme', '')
        })
        
        # 3. Nettoyage des données
        cleaned_data = self.data_cleaner.clean_restaurant_data({
            **data,
            'latitude': geocode_result.latitude,
            'longitude': geocode_result.longitude,
            'detected_theme': theme_result.detected_theme
        })
        
        # 4. Calcul du score de risque (simulation pour l'instant)
        risk_score = self._calculate_risk_score(cleaned_data, geocode_result, theme_result)
        
        # 5. Catégorisation du risque
        risk_category = self._categorize_risk(risk_score)
        
        # 6. Identification des facteurs de risque
        risk_factors = self._identify_risk_factors(cleaned_data, theme_result)
        
        return RiskPrediction(
            restaurant_id=str(hash(data['name'] + data['address'])),
            risk_score=risk_score,
            risk_category=risk_category,
            confidence=0.85,  # Simulation
            factors=risk_factors,
            geographic_data=asdict(geocode_result),
            theme_data=asdict(theme_result)
        )
    
    def _process_geocoding(self, address: str, force_refresh: bool = False) -> GeocodeResult:
        """
        Traite le géocodage d'une adresse.
        
        Args:
            address: Adresse à géocoder
            force_refresh: Forcer le rafraîchissement du cache
            
        Returns:
            GeocodeResult: Résultat du géocodage
        """
        try:
            # Normalisation de l'adresse
            normalized = self.address_normalizer.normalize_address(address)
            
            # Géocodage
            geocode_data = self.address_normalizer.geocode_address(
                normalized, 
                force_refresh=force_refresh
            )
            
            return GeocodeResult(
                original_address=address,
                normalized_address=normalized,
                latitude=geocode_data.get('latitude'),
                longitude=geocode_data.get('longitude'),
                confidence=geocode_data.get('confidence', 0.0),
                source=geocode_data.get('source', 'unknown')
            )
            
        except Exception as e:
            logger.error(f"Erreur géocodage pour {address}: {str(e)}")
            return GeocodeResult(
                original_address=address,
                normalized_address=address,
                confidence=0.0,
                source="error"
            )
    
    def _process_theme_classification(self, data: Dict) -> ThemeClassification:
        """
        Traite la classification thématique.
        
        Args:
            data: Données pour la classification
            
        Returns:
            ThemeClassification: Résultat de la classification
        """
        try:
            result = self.theme_classifier.classify_restaurant_theme(
                data['restaurant_name'],
                data.get('description', ''),
                data.get('additional_keywords', [])
            )
            
            return ThemeClassification(
                restaurant_name=data['restaurant_name'],
                detected_theme=result['theme'],
                confidence=result['confidence'],
                keywords_found=result.get('keywords_found', []),
                category=result.get('category', 'unknown')
            )
            
        except Exception as e:
            logger.error(f"Erreur classification thème: {str(e)}")
            return ThemeClassification(
                restaurant_name=data['restaurant_name'],
                detected_theme="unknown",
                confidence=0.0,
                keywords_found=[],
                category="unknown"
            )
    
    def _calculate_risk_score(self, cleaned_data: Dict, geocode_result: GeocodeResult, 
                            theme_result: ThemeClassification) -> float:
        """
        Calcule le score de risque basé sur les données disponibles.
        
        Args:
            cleaned_data: Données nettoyées
            geocode_result: Résultat du géocodage
            theme_result: Résultat de la classification thématique
            
        Returns:
            float: Score de risque (0-100)
        """
        # Simulation d'un calcul de risque basique
        base_score = 50.0
        
        # Facteur thématique
        theme_risk_factors = {
            'fast_food': 1.2,
            'sushi': 1.1,
            'bbq': 1.15,
            'fine_dining': 0.9,
            'cafe': 0.95
        }
        
        theme_factor = theme_risk_factors.get(theme_result.detected_theme, 1.0)
        base_score *= theme_factor
        
        # Facteur géographique (simulation)
        if geocode_result.latitude and geocode_result.longitude:
            # Zone à risque simulée (centre-ville = plus de risque)
            if 45.5 <= geocode_result.latitude <= 45.6 and -73.6 <= geocode_result.longitude <= -73.5:
                base_score *= 1.1
        
        # Facteur historique
        inspection_count = len(cleaned_data.get('inspection_history', []))
        if inspection_count > 3:
            base_score *= 1.05
        
        # Normalisation entre 0 et 100
        return min(max(base_score, 0.0), 100.0)
    
    def _categorize_risk(self, risk_score: float) -> str:
        """
        Catégorise le niveau de risque.
        
        Args:
            risk_score: Score de risque
            
        Returns:
            str: Catégorie de risque
        """
        if risk_score < 30:
            return "LOW"
        elif risk_score < 70:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _identify_risk_factors(self, cleaned_data: Dict, theme_result: ThemeClassification) -> List[str]:
        """
        Identifie les facteurs de risque principaux.
        
        Args:
            cleaned_data: Données nettoyées
            theme_result: Classification thématique
            
        Returns:
            List[str]: Liste des facteurs de risque
        """
        factors = []
        
        # Facteurs thématiques
        high_risk_themes = ['fast_food', 'sushi', 'bbq']
        if theme_result.detected_theme in high_risk_themes:
            factors.append(f"Type de cuisine à risque: {theme_result.detected_theme}")
        
        # Facteurs historiques
        inspection_count = len(cleaned_data.get('inspection_history', []))
        if inspection_count > 5:
            factors.append("Historique d'inspections élevé")
        
        # Facteurs géographiques
        if cleaned_data.get('latitude') and cleaned_data.get('longitude'):
            factors.append("Localisation analysée")
        
        return factors
    
    def _get_historical_data(self, restaurant_id: str, date_from: str, date_to: str) -> Dict:
        """
        Récupère les données historiques pour un restaurant.
        
        Args:
            restaurant_id: ID du restaurant
            date_from: Date de début
            date_to: Date de fin
            
        Returns:
            Dict: Données historiques
        """
        # Simulation de récupération de données historiques
        return {
            'restaurant_id': restaurant_id,
            'period': {
                'from': date_from,
                'to': date_to
            },
            'inspections': [],
            'risk_evolution': [],
            'trends': {}
        }
    
    def run(self, host='localhost', port=8080, debug=False):
        """
        Lance le serveur d'intégration.
        
        Args:
            host: Adresse d'écoute
            port: Port d'écoute
            debug: Mode debug
        """
        logger.info(f"Démarrage serveur Track-C Integration sur {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# ========== POINT D'ENTRÉE ==========

if __name__ == "__main__":
    # Configuration depuis les variables d'environnement
    host = os.getenv('TRACK_B_HOST', 'localhost')
    port = int(os.getenv('TRACK_B_PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Initialisation et lancement
    integration = TrackCIntegration()
    integration.run(host=host, port=port, debug=debug)
