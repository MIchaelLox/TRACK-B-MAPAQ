# ===========================================
# File: config.py
# Purpose: Configuration centrale du projet MAPAQ Track-B
# ===========================================

import os
from pathlib import Path
from typing import Dict, Any

# ========== PATHS & DIRECTORIES ==========
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = PROJECT_ROOT / "cache"

# Créer les répertoires s'ils n'existent pas
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# ========== DATA SOURCES ==========
class DataSources:
    """Configuration des sources de données MAPAQ."""
    
    # URLs des données MAPAQ
    MONTREAL_CSV_URL = "https://donnees.montreal.ca/dataset/inspection-aliments-contrevenants"
    QUEBEC_API_URL = "https://www.donneesquebec.ca/recherche/dataset/vmtl-inspection-aliments-contrevenants"
    
    # Fichiers locaux
    SAMPLE_DATA = PROJECT_ROOT / "sample_data.csv"
    RAW_DATA = DATA_DIR / "raw_mapaq_data.csv"
    CLEAN_DATA = DATA_DIR / "clean_mapaq_data.csv"
    
    # Cache
    GEOCODING_CACHE = CACHE_DIR / "geocoding_cache.json"
    THEME_CACHE = CACHE_DIR / "theme_classification_cache.json"

# ========== API CONFIGURATION ==========
class APIConfig:
    """Configuration des APIs externes."""
    
    # Géocodage
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    OPENSTREETMAP_USER_AGENT = "MAPAQ-Track-B/1.0"
    
    # Limites de taux
    GEOCODING_RATE_LIMIT = 50  # requêtes par minute
    API_TIMEOUT = 30  # secondes

# ========== MODEL CONFIGURATION ==========
class ModelConfig:
    """Configuration des modèles ML."""
    
    # Modèles baseline
    LOGISTIC_REGRESSION_PARAMS = {
        'C': 1.0,
        'max_iter': 1000,
        'random_state': 42
    }
    
    NAIVE_BAYES_PARAMS = {
        'alpha': 1.0
    }
    
    # Validation croisée
    CV_FOLDS = 5
    TEST_SIZE = 0.2
    RANDOM_STATE = 42
    
    # Seuils de risque
    RISK_THRESHOLDS = {
        'LOW': 0.3,
        'MEDIUM': 0.7,
        'HIGH': 1.0
    }

# ========== DATABASE CONFIGURATION ==========
class DatabaseConfig:
    """Configuration base de données."""
    
    SQLITE_DB = PROJECT_ROOT / "mapaq_data.db"
    
    # Tables
    TABLES = {
        'violations': 'violations',
        'establishments': 'establishments',
        'risk_scores': 'risk_scores',
        'geocoding_cache': 'geocoding_cache'
    }

# ========== LOGGING CONFIGURATION ==========
class LoggingConfig:
    """Configuration des logs."""
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "mapaq_track_b.log"
    
    # Rotation des logs
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

# ========== DASHBOARD CONFIGURATION ==========
class DashboardConfig:
    """Configuration du dashboard web."""
    
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = True
    
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# ========== INTEGRATION TRACK-A/C ==========
class IntegrationConfig:
    """Configuration intégration avec Track-A et Track-C."""
    
    # Track-A (FACE Engine)
    TRACK_A_API_URL = os.getenv("TRACK_A_API_URL", "http://localhost:8000")
    TRACK_A_API_KEY = os.getenv("TRACK_A_API_KEY", "")
    
    # Track-C (Integration Utils)
    TRACK_C_API_URL = os.getenv("TRACK_C_API_URL", "http://localhost:9000")
    TRACK_C_SHARED_COMPONENTS = True
    
    # Endpoints partagés
    SHARED_ENDPOINTS = {
        'risk_prediction': '/api/v1/predict-risk',
        'historical_data': '/api/v1/historical',
        'trends': '/api/v1/trends'
    }

# ========== THEME CLASSIFICATION ==========
class ThemeConfig:
    """Configuration classification thématique."""
    
    # Dictionnaires de mots-clés
    CUISINE_KEYWORDS = {
        'italien': ['pizza', 'trattoria', 'pasta', 'italien'],
        'asiatique': ['sushi', 'ramen', 'thai', 'chinois', 'japonais'],
        'francais': ['bistro', 'brasserie', 'français'],
        'americain': ['burger', 'bbq', 'grill', 'steakhouse'],
        'fast_food': ['fast', 'quick', 'express', 'rapide'],
        'cafe': ['café', 'coffee', 'espresso'],
        'boulangerie': ['boulangerie', 'patisserie', 'bakery']
    }
    
    # Seuil de confiance
    CLASSIFICATION_THRESHOLD = 0.6

# ========== EXPORT CONFIGURATION ==========
def get_config() -> Dict[str, Any]:
    """Retourne la configuration complète."""
    return {
        'data_sources': DataSources,
        'api': APIConfig,
        'model': ModelConfig,
        'database': DatabaseConfig,
        'logging': LoggingConfig,
        'dashboard': DashboardConfig,
        'integration': IntegrationConfig,
        'theme': ThemeConfig,
        'paths': {
            'project_root': PROJECT_ROOT,
            'data_dir': DATA_DIR,
            'models_dir': MODELS_DIR,
            'logs_dir': LOGS_DIR,
            'cache_dir': CACHE_DIR
        }
    }

# ========== ENVIRONMENT SETUP ==========
def setup_environment():
    """Configure l'environnement de développement."""
    
    # Créer les répertoires nécessaires
    for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
        directory.mkdir(exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")
    
    # Vérifier les variables d'environnement critiques
    critical_env_vars = [
        'GOOGLE_MAPS_API_KEY',
        'FLASK_SECRET_KEY',
        'TRACK_A_API_KEY'
    ]
    
    missing_vars = []
    for var in critical_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print("💡 Create a .env file with these variables for production")
    
    print("🚀 Environment setup completed!")

if __name__ == "__main__":
    setup_environment()
