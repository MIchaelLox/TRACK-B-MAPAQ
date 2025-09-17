"""
Data Formatters for Track-C Integration
Formatage et validation des données pour l'intégration Track-C

Ce module fournit les classes et fonctions pour formater, valider et transformer
les données échangées entre Track-B (MAPAQ) et Track-C (Integration Utils).

Author: Mouhamed Thiaw
Date: 2025-01-14
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from marshmallow.decorators import post_load
import re

# Configuration logging
logger = logging.getLogger(__name__)

# ========== SCHÉMAS DE VALIDATION MARSHMALLOW ==========

class BaseSchema(Schema):
    """Schéma de base avec validation commune."""
    
    def handle_error(self, error, data, **kwargs):
        """Gestion personnalisée des erreurs de validation."""
        logger.warning(f"Erreur de validation: {error.messages}")
        raise ValidationError(error.messages)

class RestaurantInputSchema(BaseSchema):
    """Schéma de validation pour les données d'entrée restaurant."""
    
    name = fields.Str(
        required=True, 
        validate=lambda x: len(x.strip()) > 0,
        error_messages={'required': 'Le nom du restaurant est requis'}
    )
    address = fields.Str(
        required=True,
        validate=lambda x: len(x.strip()) > 0,
        error_messages={'required': 'L\'adresse est requise'}
    )
    theme = fields.Str(missing="", allow_none=True)
    phone = fields.Str(missing="", allow_none=True)
    email = fields.Email(missing="", allow_none=True)
    website = fields.Url(missing="", allow_none=True)
    inspection_history = fields.List(fields.Dict(), missing=[])
    additional_data = fields.Dict(missing={})
    
    @validates('phone')
    def validate_phone(self, value):
        """Valide le format du numéro de téléphone."""
        if value and value.strip():
            # Format canadien/québécois basique
            phone_pattern = r'^(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})$'
            if not re.match(phone_pattern, value.strip()):
                raise ValidationError('Format de téléphone invalide')
    
    @validates('name')
    def validate_name_length(self, value):
        """Valide la longueur du nom."""
        if len(value.strip()) > 200:
            raise ValidationError('Le nom du restaurant ne peut pas dépasser 200 caractères')
    
    @validates('address')
    def validate_address_format(self, value):
        """Valide le format de base de l'adresse."""
        if len(value.strip()) < 10:
            raise ValidationError('L\'adresse semble trop courte')
        if len(value.strip()) > 500:
            raise ValidationError('L\'adresse ne peut pas dépasser 500 caractères')

class GeocodeInputSchema(BaseSchema):
    """Schéma pour les requêtes de géocodage."""
    
    address = fields.Str(
        required=True,
        validate=lambda x: len(x.strip()) > 0,
        error_messages={'required': 'L\'adresse à géocoder est requise'}
    )
    force_refresh = fields.Bool(missing=False)
    provider = fields.Str(
        missing="auto",
        validate=lambda x: x in ['auto', 'google', 'osm', 'nominatim']
    )
    
    @validates('address')
    def validate_address(self, value):
        """Valide l'adresse pour le géocodage."""
        if len(value.strip()) < 5:
            raise ValidationError('Adresse trop courte pour le géocodage')

class ThemeInputSchema(BaseSchema):
    """Schéma pour la classification thématique."""
    
    restaurant_name = fields.Str(
        required=True,
        validate=lambda x: len(x.strip()) > 0,
        error_messages={'required': 'Le nom du restaurant est requis'}
    )
    description = fields.Str(missing="", allow_none=True)
    menu_items = fields.List(fields.Str(), missing=[])
    additional_keywords = fields.List(fields.Str(), missing=[])
    
    @validates('menu_items')
    def validate_menu_items(self, value):
        """Valide les éléments du menu."""
        if len(value) > 50:
            raise ValidationError('Trop d\'éléments de menu (maximum 50)')

class BatchProcessingSchema(BaseSchema):
    """Schéma pour le traitement par lot."""
    
    restaurants = fields.List(
        fields.Nested(RestaurantInputSchema),
        required=True,
        validate=lambda x: 0 < len(x) <= 50,
        error_messages={
            'required': 'Liste de restaurants requise',
            'validator_failed': 'Le lot doit contenir entre 1 et 50 restaurants'
        }
    )
    processing_options = fields.Dict(missing={})
    callback_url = fields.Url(missing="", allow_none=True)
    
    @validates_schema
    def validate_batch_size(self, data, **kwargs):
        """Valide la taille du lot."""
        restaurants = data.get('restaurants', [])
        if not restaurants:
            raise ValidationError('Au moins un restaurant est requis')

# ========== SCHÉMAS DE RÉPONSE ==========

class APIResponseSchema(BaseSchema):
    """Schéma pour les réponses API standardisées."""
    
    success = fields.Bool(required=True)
    data = fields.Raw(allow_none=True)
    error = fields.Str(allow_none=True)
    timestamp = fields.DateTime(missing=datetime.now)
    execution_time = fields.Float(missing=0.0)
    request_id = fields.Str(allow_none=True)

class RiskPredictionResponseSchema(BaseSchema):
    """Schéma pour les réponses de prédiction de risque."""
    
    restaurant_id = fields.Str(required=True)
    risk_score = fields.Float(required=True, validate=lambda x: 0 <= x <= 100)
    risk_category = fields.Str(
        required=True,
        validate=lambda x: x in ['LOW', 'MEDIUM', 'HIGH']
    )
    confidence = fields.Float(required=True, validate=lambda x: 0 <= x <= 1)
    factors = fields.List(fields.Str(), missing=[])
    geographic_data = fields.Dict(allow_none=True)
    theme_data = fields.Dict(allow_none=True)
    prediction_date = fields.DateTime(missing=datetime.now)

class GeocodeResponseSchema(BaseSchema):
    """Schéma pour les réponses de géocodage."""
    
    original_address = fields.Str(required=True)
    normalized_address = fields.Str(required=True)
    latitude = fields.Float(allow_none=True, validate=lambda x: -90 <= x <= 90 if x else True)
    longitude = fields.Float(allow_none=True, validate=lambda x: -180 <= x <= 180 if x else True)
    confidence = fields.Float(required=True, validate=lambda x: 0 <= x <= 1)
    source = fields.Str(required=True)
    geocoded_at = fields.DateTime(missing=datetime.now)

# ========== FORMATTERS PRINCIPAUX ==========

class TrackCDataFormatter:
    """
    Formatage principal des données pour Track-C.
    Centralise toutes les opérations de formatage et validation.
    """
    
    def __init__(self):
        """Initialise le formateur de données."""
        self.schemas = {
            'restaurant_input': RestaurantInputSchema(),
            'geocode_input': GeocodeInputSchema(),
            'theme_input': ThemeInputSchema(),
            'batch_processing': BatchProcessingSchema(),
            'api_response': APIResponseSchema(),
            'risk_prediction': RiskPredictionResponseSchema(),
            'geocode_response': GeocodeResponseSchema()
        }
        logger.info("TrackCDataFormatter initialisé")
    
    def validate_restaurant_input(self, data: Dict) -> Dict:
        """
        Valide et nettoie les données d'entrée restaurant.
        
        Args:
            data: Données brutes du restaurant
            
        Returns:
            Dict: Données validées et nettoyées
            
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            validated_data = self.schemas['restaurant_input'].load(data)
            logger.debug(f"Restaurant validé: {validated_data['name']}")
            return validated_data
        except ValidationError as e:
            logger.error(f"Erreur validation restaurant: {e.messages}")
            raise
    
    def validate_geocode_input(self, data: Dict) -> Dict:
        """
        Valide les données pour le géocodage.
        
        Args:
            data: Données de géocodage
            
        Returns:
            Dict: Données validées
        """
        try:
            return self.schemas['geocode_input'].load(data)
        except ValidationError as e:
            logger.error(f"Erreur validation géocodage: {e.messages}")
            raise
    
    def validate_theme_input(self, data: Dict) -> Dict:
        """
        Valide les données pour la classification thématique.
        
        Args:
            data: Données de classification
            
        Returns:
            Dict: Données validées
        """
        try:
            return self.schemas['theme_input'].load(data)
        except ValidationError as e:
            logger.error(f"Erreur validation thème: {e.messages}")
            raise
    
    def format_api_response(self, success: bool, data: Optional[Any] = None,
                          error: Optional[str] = None, execution_time: float = 0.0,
                          request_id: Optional[str] = None) -> Dict:
        """
        Formate une réponse API standardisée.
        
        Args:
            success: Succès de l'opération
            data: Données de réponse
            error: Message d'erreur
            execution_time: Temps d'exécution
            request_id: ID de la requête
            
        Returns:
            Dict: Réponse formatée
        """
        response_data = {
            'success': success,
            'data': data,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time
        }
        
        if request_id:
            response_data['request_id'] = request_id
        
        try:
            return self.schemas['api_response'].load(response_data)
        except ValidationError as e:
            logger.error(f"Erreur formatage réponse API: {e.messages}")
            # Retour d'une réponse d'erreur basique
            return {
                'success': False,
                'error': 'Erreur de formatage de la réponse',
                'timestamp': datetime.now().isoformat()
            }
    
    def format_risk_prediction(self, prediction_data: Dict) -> Dict:
        """
        Formate une réponse de prédiction de risque.
        
        Args:
            prediction_data: Données de prédiction
            
        Returns:
            Dict: Prédiction formatée
        """
        try:
            return self.schemas['risk_prediction'].load(prediction_data)
        except ValidationError as e:
            logger.error(f"Erreur formatage prédiction: {e.messages}")
            raise
    
    def format_geocode_response(self, geocode_data: Dict) -> Dict:
        """
        Formate une réponse de géocodage.
        
        Args:
            geocode_data: Données de géocodage
            
        Returns:
            Dict: Géocodage formaté
        """
        try:
            return self.schemas['geocode_response'].load(geocode_data)
        except ValidationError as e:
            logger.error(f"Erreur formatage géocodage: {e.messages}")
            raise
    
    def validate_batch_input(self, data: Dict) -> Dict:
        """
        Valide les données pour le traitement par lot.
        
        Args:
            data: Données du lot
            
        Returns:
            Dict: Lot validé
        """
        try:
            return self.schemas['batch_processing'].load(data)
        except ValidationError as e:
            logger.error(f"Erreur validation lot: {e.messages}")
            raise

# ========== UTILITAIRES DE FORMATAGE ==========

class FormatUtils:
    """Utilitaires de formatage et transformation."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Nettoie et normalise un texte.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
        
        # Suppression des espaces multiples
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Suppression des caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalise un numéro de téléphone.
        
        Args:
            phone: Numéro brut
            
        Returns:
            str: Numéro normalisé
        """
        if not phone:
            return ""
        
        # Suppression de tous les caractères non numériques
        digits = re.sub(r'\D', '', phone)
        
        # Format canadien
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone  # Retour du format original si non reconnu
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Normalise une adresse.
        
        Args:
            address: Adresse brute
            
        Returns:
            str: Adresse normalisée
        """
        if not address:
            return ""
        
        # Nettoyage de base
        address = FormatUtils.clean_text(address)
        
        # Normalisation des abréviations courantes
        replacements = {
            r'\bSt\b': 'Street',
            r'\bAve\b': 'Avenue',
            r'\bBlvd\b': 'Boulevard',
            r'\bRd\b': 'Road',
            r'\bDr\b': 'Drive',
            r'\bApt\b': 'Apartment',
            r'\bSte\b': 'Suite'
        }
        
        for pattern, replacement in replacements.items():
            address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
        
        return address
    
    @staticmethod
    def format_currency(amount: Union[int, float], currency: str = 'CAD') -> str:
        """
        Formate un montant en devise.
        
        Args:
            amount: Montant
            currency: Code de devise
            
        Returns:
            str: Montant formaté
        """
        if currency == 'CAD':
            return f"{amount:,.2f} CAD$"
        elif currency == 'USD':
            return f"${amount:,.2f} USD"
        else:
            return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """
        Formate un pourcentage.
        
        Args:
            value: Valeur (0-1 ou 0-100)
            decimals: Nombre de décimales
            
        Returns:
            str: Pourcentage formaté
        """
        # Détection si la valeur est déjà en pourcentage
        if value <= 1.0:
            value *= 100
        
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def serialize_datetime(dt: datetime) -> str:
        """
        Sérialise une datetime en ISO format.
        
        Args:
            dt: Datetime à sérialiser
            
        Returns:
            str: Datetime en format ISO
        """
        if isinstance(dt, datetime):
            return dt.isoformat()
        elif isinstance(dt, date):
            return dt.isoformat()
        else:
            return str(dt)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Tronque un texte à une longueur maximale.
        
        Args:
            text: Texte à tronquer
            max_length: Longueur maximale
            suffix: Suffixe à ajouter
            
        Returns:
            str: Texte tronqué
        """
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

# ========== CONVERTISSEURS SPÉCIALISÉS ==========

class DataConverter:
    """Convertisseurs pour différents types de données."""
    
    @staticmethod
    def restaurant_to_api_format(restaurant_data: Dict) -> Dict:
        """
        Convertit les données restaurant au format API.
        
        Args:
            restaurant_data: Données restaurant internes
            
        Returns:
            Dict: Données au format API
        """
        formatter = TrackCDataFormatter()
        
        # Nettoyage et formatage
        api_data = {
            'name': FormatUtils.clean_text(restaurant_data.get('name', '')),
            'address': FormatUtils.normalize_address(restaurant_data.get('address', '')),
            'phone': FormatUtils.normalize_phone(restaurant_data.get('phone', '')),
            'theme': restaurant_data.get('theme', ''),
            'inspection_history': restaurant_data.get('inspection_history', []),
            'additional_data': restaurant_data.get('additional_data', {})
        }
        
        # Ajout de métadonnées
        api_data['formatted_at'] = datetime.now().isoformat()
        api_data['data_version'] = '1.0'
        
        return formatter.validate_restaurant_input(api_data)
    
    @staticmethod
    def prediction_to_track_c_format(prediction: Dict) -> Dict:
        """
        Convertit une prédiction au format Track-C.
        
        Args:
            prediction: Données de prédiction
            
        Returns:
            Dict: Prédiction au format Track-C
        """
        return {
            'restaurant_id': str(prediction.get('restaurant_id', '')),
            'risk_assessment': {
                'score': float(prediction.get('risk_score', 0.0)),
                'category': prediction.get('risk_category', 'UNKNOWN'),
                'confidence': float(prediction.get('confidence', 0.0))
            },
            'analysis': {
                'factors': prediction.get('factors', []),
                'geographic_data': prediction.get('geographic_data', {}),
                'theme_data': prediction.get('theme_data', {})
            },
            'metadata': {
                'prediction_date': FormatUtils.serialize_datetime(datetime.now()),
                'model_version': '1.0',
                'processing_time': prediction.get('execution_time', 0.0)
            }
        }

# ========== POINT D'ENTRÉE ==========

# Instance globale du formateur
global_formatter = TrackCDataFormatter()

def get_formatter() -> TrackCDataFormatter:
    """
    Récupère l'instance globale du formateur.
    
    Returns:
        TrackCDataFormatter: Instance du formateur
    """
    return global_formatter

if __name__ == "__main__":
    # Tests de base des formatters
    formatter = TrackCDataFormatter()
    
    # Test de validation restaurant
    test_restaurant = {
        'name': 'Test Restaurant',
        'address': '123 Test St, Montreal, QC',
        'phone': '514-555-1234',
        'theme': 'italian'
    }
    
    try:
        validated = formatter.validate_restaurant_input(test_restaurant)
        print("✅ Validation restaurant réussie")
        print(json.dumps(validated, indent=2))
    except ValidationError as e:
        print(f"❌ Erreur validation: {e.messages}")
    
    # Test de formatage de réponse API
    response = formatter.format_api_response(
        success=True,
        data={'test': 'data'},
        execution_time=0.123
    )
    print("\n✅ Formatage réponse API:")
    print(json.dumps(response, indent=2))
