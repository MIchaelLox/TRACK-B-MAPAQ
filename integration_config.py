"""
Configuration d'Intégration Track-C
Configuration spécialisée pour l'intégration avec Track-C

Ce module centralise toute la configuration nécessaire pour l'intégration
entre Track-B (MAPAQ) et Track-C (Integration Utils).

Author: Mouhamed Thiaw
Date: 2025-01-14
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

# ========== CONFIGURATION SÉCURITÉ ==========

@dataclass
class SecurityConfig:
    """Configuration de sécurité pour l'intégration Track-C."""
    
    # Clés API valides (à configurer via variables d'environnement)
    VALID_API_KEYS: List[str] = None
    
    # Configuration CORS
    CORS_ORIGINS: List[str] = None
    
    # Configuration JWT (si utilisé)
    JWT_SECRET_KEY: str = ""
    JWT_EXPIRATION_HOURS: int = 24
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: str = "100/hour"
    
    # HTTPS
    FORCE_HTTPS: bool = False
    SSL_CERT_PATH: str = ""
    SSL_KEY_PATH: str = ""
    
    def __post_init__(self):
        """Initialisation post-création avec variables d'environnement."""
        if self.VALID_API_KEYS is None:
            # Lecture des clés API depuis l'environnement
            api_keys_str = os.getenv('TRACK_C_API_KEYS', 'test-key,dev-key')
            self.VALID_API_KEYS = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        
        if self.CORS_ORIGINS is None:
            # Origines CORS autorisées
            cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:9000')
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]
        
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')

# ========== CONFIGURATION ENDPOINTS ==========

@dataclass
class EndpointConfiguration:
    """Configuration des endpoints d'intégration."""
    
    # URLs des services
    TRACK_A_BASE_URL: str = "http://localhost:8000"
    TRACK_B_BASE_URL: str = "http://localhost:8080"  
    TRACK_C_BASE_URL: str = "http://localhost:9000"
    
    # Endpoints Track-A (FACE Engine)
    TRACK_A_ENDPOINTS: Dict[str, str] = None
    
    # Endpoints Track-C (Integration Utils)
    TRACK_C_ENDPOINTS: Dict[str, str] = None
    
    # Timeouts (en secondes)
    REQUEST_TIMEOUT: int = 30
    CONNECTION_TIMEOUT: int = 10
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5
    
    def __post_init__(self):
        """Initialisation des endpoints."""
        # Lecture des URLs depuis l'environnement
        self.TRACK_A_BASE_URL = os.getenv('TRACK_A_API_URL', self.TRACK_A_BASE_URL)
        self.TRACK_B_BASE_URL = os.getenv('TRACK_B_API_URL', self.TRACK_B_BASE_URL)
        self.TRACK_C_BASE_URL = os.getenv('TRACK_C_API_URL', self.TRACK_C_BASE_URL)
        
        if self.TRACK_A_ENDPOINTS is None:
            self.TRACK_A_ENDPOINTS = {
                'health': f"{self.TRACK_A_BASE_URL}/api/v1/health",
                'financial_analysis': f"{self.TRACK_A_BASE_URL}/api/v1/financial-analysis",
                'cost_prediction': f"{self.TRACK_A_BASE_URL}/api/v1/cost-prediction",
                'compliance_check': f"{self.TRACK_A_BASE_URL}/api/v1/compliance-check"
            }
        
        if self.TRACK_C_ENDPOINTS is None:
            self.TRACK_C_ENDPOINTS = {
                'health': f"{self.TRACK_C_BASE_URL}/api/v1/health",
                'shared_components': f"{self.TRACK_C_BASE_URL}/api/v1/components",
                'integration_status': f"{self.TRACK_C_BASE_URL}/api/v1/integration-status",
                'composite_analysis': f"{self.TRACK_C_BASE_URL}/api/v1/composite-analysis"
            }

# ========== CONFIGURATION CACHE ==========

@dataclass
class CacheConfiguration:
    """Configuration du système de cache."""
    
    # Redis configuration
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # Cache TTL (Time To Live) en secondes
    CACHE_TTL: Dict[str, int] = None
    
    # Tailles maximales de cache
    MAX_CACHE_SIZE: Dict[str, int] = None
    
    # Préfixes de clés
    CACHE_KEY_PREFIXES: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialisation de la configuration cache."""
        # Lecture de la configuration Redis depuis l'environnement
        self.REDIS_URL = os.getenv('REDIS_URL', self.REDIS_URL)
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', self.REDIS_PASSWORD)
        self.REDIS_DB = int(os.getenv('REDIS_DB', str(self.REDIS_DB)))
        
        if self.CACHE_TTL is None:
            self.CACHE_TTL = {
                'geocoding': 3600 * 24,  # 24 heures
                'theme_classification': 3600 * 12,  # 12 heures
                'risk_prediction': 3600 * 2,  # 2 heures
                'api_responses': 300,  # 5 minutes
                'health_checks': 60  # 1 minute
            }
        
        if self.MAX_CACHE_SIZE is None:
            self.MAX_CACHE_SIZE = {
                'geocoding': 10000, 
                'theme_classification': 5000, 
                'risk_prediction': 1000, 
                'api_responses': 500  
            }
        
        if self.CACHE_KEY_PREFIXES is None:
            self.CACHE_KEY_PREFIXES = {
                'geocoding': 'mapaq:geo:',
                'theme_classification': 'mapaq:theme:',
                'risk_prediction': 'mapaq:risk:',
                'api_responses': 'mapaq:api:',
                'integration': 'mapaq:integration:'
            }

# ========== CONFIGURATION MONITORING ==========

@dataclass
class MonitoringConfiguration:
    """Configuration du monitoring et logging."""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PATH: str = "logs/track_c_integration.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024 
    LOG_BACKUP_COUNT: int = 5
    
    # Métriques
    METRICS_ENABLED: bool = True
    METRICS_ENDPOINT: str = "/metrics"
    METRICS_PORT: int = 9090
    
    # Health checks
    HEALTH_CHECK_INTERVAL: int = 60  
    HEALTH_CHECK_TIMEOUT: int = 10  
    
    # Alerting
    ALERTING_ENABLED: bool = False
    ALERT_EMAIL: str = ""
    ALERT_WEBHOOK_URL: str = ""
    
    # Thresholds pour alertes
    ERROR_RATE_THRESHOLD: float = 0.05  # 5%
    RESPONSE_TIME_THRESHOLD: float = 2.0  # 2 secondes
    
    def __post_init__(self):
        """Initialisation de la configuration monitoring."""
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', self.LOG_LEVEL)
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', self.LOG_FILE_PATH)
        
        # Création du répertoire de logs si nécessaire
        log_dir = os.path.dirname(self.LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        self.ALERT_EMAIL = os.getenv('ALERT_EMAIL', self.ALERT_EMAIL)
        self.ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', self.ALERT_WEBHOOK_URL)

# ========== CONFIGURATION PERFORMANCE ==========

@dataclass
class PerformanceConfiguration:
    """Configuration de performance."""
    
    # Limites de requêtes
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_BATCH_SIZE: int = 50  # restaurants par lot
    MAX_CONCURRENT_REQUESTS: int = 100
    
    # Timeouts
    API_TIMEOUT: int = 30  # secondes
    DATABASE_TIMEOUT: int = 10  # secondes
    CACHE_TIMEOUT: int = 5  # secondes
    
    # Pool de connexions
    CONNECTION_POOL_SIZE: int = 20
    CONNECTION_POOL_MAX_OVERFLOW: int = 10
    
    # Optimisations
    ENABLE_COMPRESSION: bool = True
    ENABLE_CACHING: bool = True
    ENABLE_ASYNC_PROCESSING: bool = True
    
    # Seuils de performance
    RESPONSE_TIME_WARNING: float = 1.0  # secondes
    RESPONSE_TIME_CRITICAL: float = 3.0  # secondes
    MEMORY_WARNING_THRESHOLD: int = 512 * 1024 * 1024  # 512MB
    
    def __post_init__(self):
        """Initialisation de la configuration performance."""
        self.MAX_REQUEST_SIZE = int(os.getenv('MAX_REQUEST_SIZE', str(self.MAX_REQUEST_SIZE)))
        self.MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', str(self.MAX_BATCH_SIZE)))
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', str(self.API_TIMEOUT)))

# ========== CONFIGURATION PRINCIPALE ==========

class TrackCIntegrationConfig:
    """Configuration principale pour l'intégration Track-C."""
    
    def __init__(self):
        """Initialise toutes les configurations."""
        self.security = SecurityConfig()
        self.endpoints = EndpointConfiguration()
        self.cache = CacheConfiguration()
        self.monitoring = MonitoringConfiguration()
        self.performance = PerformanceConfiguration()
        
        # Environnement
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Version
        self.version = "1.0.0"
        self.api_version = "v1"
    
    def is_production(self) -> bool:
        """Vérifie si on est en environnement de production."""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Vérifie si on est en environnement de développement."""
        return self.environment.lower() == 'development'
    
    def get_database_url(self) -> str:
        """Récupère l'URL de base de données."""
        return os.getenv('DATABASE_URL', 'sqlite:///mapaq_integration.db')
    
    def validate_configuration(self) -> List[str]:
        """
        Valide la configuration et retourne les erreurs.
        
        Returns:
            List[str]: Liste des erreurs de configuration
        """
        errors = []
        
        # Validation sécurité
        if not self.security.VALID_API_KEYS:
            errors.append("Aucune clé API configurée")
        
        if self.is_production() and 'test-key' in self.security.VALID_API_KEYS:
            errors.append("Clé de test détectée en production")
        
        if self.is_production() and not self.security.FORCE_HTTPS:
            errors.append("HTTPS non forcé en production")
        
        # Validation endpoints
        if not self.endpoints.TRACK_A_BASE_URL:
            errors.append("URL Track-A non configurée")
        
        if not self.endpoints.TRACK_C_BASE_URL:
            errors.append("URL Track-C non configurée")
        
        # Validation cache
        if self.cache.REDIS_ENABLED and not self.cache.REDIS_URL:
            errors.append("Redis activé mais URL non configurée")
        
        # Validation monitoring
        if self.monitoring.ALERTING_ENABLED and not self.monitoring.ALERT_EMAIL:
            errors.append("Alerting activé mais email non configuré")
        
        return errors
    
    def to_dict(self) -> Dict:
        """
        Convertit la configuration en dictionnaire.
        
        Returns:
            Dict: Configuration sérialisée
        """
        return {
            'environment': self.environment,
            'debug': self.debug,
            'version': self.version,
            'api_version': self.api_version,
            'security': {
                'cors_origins': self.security.CORS_ORIGINS,
                'rate_limit_enabled': self.security.RATE_LIMIT_ENABLED,
                'force_https': self.security.FORCE_HTTPS
            },
            'endpoints': {
                'track_a_base_url': self.endpoints.TRACK_A_BASE_URL,
                'track_b_base_url': self.endpoints.TRACK_B_BASE_URL,
                'track_c_base_url': self.endpoints.TRACK_C_BASE_URL,
                'request_timeout': self.endpoints.REQUEST_TIMEOUT
            },
            'cache': {
                'redis_enabled': self.cache.REDIS_ENABLED,
                'redis_url': self.cache.REDIS_URL if not self.cache.REDIS_PASSWORD else "[HIDDEN]"
            },
            'monitoring': {
                'log_level': self.monitoring.LOG_LEVEL,
                'metrics_enabled': self.monitoring.METRICS_ENABLED,
                'alerting_enabled': self.monitoring.ALERTING_ENABLED
            },
            'performance': {
                'max_batch_size': self.performance.MAX_BATCH_SIZE,
                'max_concurrent_requests': self.performance.MAX_CONCURRENT_REQUESTS,
                'enable_caching': self.performance.ENABLE_CACHING
            }
        }

# ========== INSTANCE GLOBALE ==========

config = TrackCIntegrationConfig()

def get_config() -> TrackCIntegrationConfig:
    """
    Récupère l'instance globale de configuration.
    
    Returns:
        TrackCIntegrationConfig: Configuration globale
    """
    return config

def validate_config() -> bool:
    """
    Valide la configuration globale.
    
    Returns:
        bool: True si la configuration est valide
    """
    errors = config.validate_configuration()
    if errors:
        print("Erreurs de configuration détectées:")
        for error in errors:
            print(f"  - {error}")
        return False
    return True

# ========== UTILITAIRES DE CONFIGURATION ==========

def load_config_from_file(config_file: str) -> bool:
    """
    Charge la configuration depuis un fichier.
    
    Args:
        config_file: Chemin vers le fichier de configuration
        
    Returns:
        bool: True si le chargement a réussi
    """
    try:
        if os.path.exists(config_file):
            # Implémentation du chargement de fichier
            # (JSON, YAML, etc.)
            pass
        return True
    except Exception as e:
        print(f"Erreur chargement configuration: {e}")
        return False

def export_config_template(output_file: str = "integration_config_template.json") -> bool:
    """
    Exporte un template de configuration.
    
    Args:
        output_file: Fichier de sortie
        
    Returns:
        bool: True si l'export a réussi
    """
    try:
        import json
        template = config.to_dict()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"Template de configuration exporté vers: {output_file}")
        return True
    except Exception as e:
        print(f"Erreur export template: {e}")
        return False

if __name__ == "__main__":
    # Test de la configuration
    print("=== Configuration Track-C Integration ===")
    print(f"Environnement: {config.environment}")
    print(f"Debug: {config.debug}")
    print(f"Version: {config.version}")
    
    # Validation
    if validate_config():
        print("✅ Configuration valide")
    else:
        print("❌ Configuration invalide")
    
    # Export du template
    export_config_template()
