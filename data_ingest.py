import pandas as pd
import requests
import os
import json
import time
from pathlib import Path
from typing import Optional, Union, Dict, List
import logging
from datetime import datetime, timedelta

# Import configuration centralisée
from config import DataSources, APIConfig, LoggingConfig

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LOG_LEVEL),
    format=LoggingConfig.LOG_FORMAT,
    handlers=[
        logging.FileHandler(LoggingConfig.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataIngestor:
    def __init__(self, source_path: Optional[str] = None, auto_download: bool = True):
        """
        Initialize DataIngestor with source path or API endpoint.

        Args:
            source_path (str, optional): Path to CSV file or API endpoint URL
            auto_download (bool): Automatically download from MAPAQ API if no source provided
        """
        self.source_path = source_path or DataSources.RAW_DATA
        self.auto_download = auto_download
        self.raw_data = None

        # Some test environments use a simplified DataSources without CACHE_DIR.
        # Fall back to a local "data/cache" directory in that case.
        cache_dir = getattr(DataSources, "CACHE_DIR", Path("data/cache"))
        if isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)
        self.download_cache = cache_dir / "download_cache.json"

        # Statistiques de téléchargement
        self.download_stats = {
            "last_download": None,
            "records_downloaded": 0,
            "download_duration": 0,
            "source_used": None,
        }
        
    def load_raw_data(self) -> pd.DataFrame:
        """
        Load MAPAQ inspection data from CSV/API.
        Return raw dataset as pandas DataFrame.
        
        Returns:
            pd.DataFrame: Raw dataset loaded from source
        """
        start_time = time.time()
        
        try:
            # Si auto_download est activé et pas de fichier local, télécharger depuis MAPAQ
            if self.auto_download and not self._file_exists_and_recent():
                logger.info("Auto-downloading latest MAPAQ data...")
                self.raw_data = self._download_from_mapaq_api()
                self._save_to_cache()
            elif self._is_url(str(self.source_path)):
                logger.info(f"Loading data from URL: {self.source_path}")
                self.raw_data = self._load_from_url()
            elif self._is_csv_file(str(self.source_path)):
                logger.info(f"Loading data from CSV file: {self.source_path}")
                self.raw_data = self._load_from_csv()
            else:
                logger.warning(f"Unsupported source format: {self.source_path}")
                logger.info("Attempting to download from MAPAQ API as fallback...")
                self.raw_data = self._download_from_mapaq_api()
            
            # Mise à jour des statistiques
            self.download_stats.update({
                'last_download': datetime.now().isoformat(),
                'records_downloaded': len(self.raw_data),
                'download_duration': time.time() - start_time,
                'source_used': str(self.source_path)
            })
                
            logger.info(f"Successfully loaded {len(self.raw_data)} records in {self.download_stats['download_duration']:.2f}s")
            return self.raw_data
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _is_url(self, path: str) -> bool:
        """Check if path is a URL."""
        return path.startswith(('http://', 'https://'))
    
    def _is_csv_file(self, path: str) -> bool:
        """Check if path is a CSV file."""
        return path.endswith('.csv') and os.path.exists(path)

    def load_from_csv(self, csv_path: Optional[str] = None) -> pd.DataFrame:
        """
        Public helper to load data explicitly from a CSV file.

        This is a thin wrapper around the internal `_load_from_csv` method
        and is used by some integration tests.

        Args:
            csv_path (str, optional): Path to a CSV file. If not provided,
                the current `self.source_path` is used.

        Returns:
            pd.DataFrame: Data loaded from the CSV file.
        """
        if csv_path is not None:
            self.source_path = csv_path
        return self._load_from_csv()

    def _load_from_csv(self) -> pd.DataFrame:
        """
        Internal helper to load data from CSV using the current source_path.

        Returns:
            pd.DataFrame: Data loaded from CSV.
        """
        try:
            # Try different encodings
            encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

            for encoding in encodings:
                try:
                    df = pd.read_csv(self.source_path, encoding=encoding)
                    logger.info(f"Successfully loaded CSV with encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue

            # If no encoding works
            raise ValueError("Unable to decode CSV file with any standard encoding")

        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise

    def load_from_url(self, url: Optional[str] = None) -> pd.DataFrame:
        """
        Public helper to load data explicitly from an HTTP/HTTPS URL.

        Args:
            url (str, optional): HTTP/HTTPS URL. If not provided,
                the current `self.source_path` is used.

        Returns:
            pd.DataFrame: Data loaded from the URL.
        """
        if url is not None:
            self.source_path = url
        return self._load_from_url()

    def get_data_info(self) -> dict:
        """
        Get information about the loaded dataset.
        
        Returns:
            dict: Dataset information (shape, columns, dtypes, etc.)
        """
        if self.raw_data is None:
            return {"error": "No data loaded yet"}
        
        return {
            "shape": self.raw_data.shape,
            "columns": list(self.raw_data.columns),
            "dtypes": dict(self.raw_data.dtypes),
            "null_counts": dict(self.raw_data.isnull().sum()),
            "memory_usage": self.raw_data.memory_usage(deep=True).sum(),
            "sample_data": self.raw_data.head().to_dict()
        }
    
    def validate_data_structure(self) -> dict:
        """
        Validate that the loaded data has the expected MAPAQ structure.
        
        Returns:
            dict: Validation results
        """
        if self.raw_data is None:
            return {"valid": False, "error": "No data loaded"}
        
        # Colonnes attendues basées sur notre analyse
        expected_columns = [
            'id_poursuite', 'business_id', 'date', 'date_jugement',
            'description', 'etablissement', 'montant', 'proprietaire',
            'ville', 'statut', 'date_statut', 'categorie'
        ]
        
        actual_columns = list(self.raw_data.columns)
        missing_columns = set(expected_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(expected_columns)
        
        return {
            "valid": len(missing_columns) == 0,
            "expected_columns": expected_columns,
            "actual_columns": actual_columns,
            "missing_columns": list(missing_columns),
            "extra_columns": list(extra_columns),
            "total_records": len(self.raw_data)
        }
    
    def _download_from_mapaq_api(self) -> pd.DataFrame:
        """
        Télécharge les données depuis l'API MAPAQ Montréal.
        
        Returns:
            pd.DataFrame: Données téléchargées depuis l'API
        """
        logger.info("Connecting to MAPAQ Montreal API...")
        
        # URLs des données MAPAQ (basées sur notre recherche précédente)
        api_urls = [
            "https://donnees.montreal.ca/dataset/7f939a08-be8a-45e1-b208-d8744dca8fc6/resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/download/contrevenants.csv",
            DataSources.MONTREAL_CSV_URL,
            "https://www.donneesquebec.ca/recherche/dataset/vmtl-inspection-aliments-contrevenants/resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/download/contrevenants.csv"
        ]
        
        for i, url in enumerate(api_urls):
            try:
                logger.info(f"Attempting download from source {i+1}/{len(api_urls)}: {url}")
                
                response = requests.get(
                    url, 
                    timeout=APIConfig.API_TIMEOUT,
                    headers={
                        'User-Agent': 'MAPAQ-Track-B/1.0 (Educational Project)',
                        'Accept': 'text/csv,application/csv,*/*'
                    }
                )
                response.raise_for_status()
                
                # Vérifier le type de contenu
                content_type = response.headers.get('content-type', '').lower()
                logger.info(f"Response content-type: {content_type}")
                
                # Traiter la réponse selon le type
                if 'csv' in content_type or url.endswith('.csv'):
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    logger.info(f"Successfully downloaded {len(df)} records from CSV")
                    return df
                
                elif 'json' in content_type:
                    data = response.json()
                    if isinstance(data, dict) and 'records' in data:
                        df = pd.DataFrame(data['records'])
                    elif isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                    logger.info(f"Successfully downloaded {len(df)} records from JSON")
                    return df
                
                else:
                    # Essayer de parser comme CSV par défaut
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    logger.info(f"Successfully downloaded {len(df)} records (default CSV parsing)")
                    return df
                    
            except requests.RequestException as e:
                logger.warning(f"Failed to download from {url}: {str(e)}")
                continue
            except pd.errors.EmptyDataError:
                logger.warning(f"Empty data received from {url}")
                continue
            except Exception as e:
                logger.warning(f"Error processing data from {url}: {str(e)}")
                continue
        
        # Si tous les téléchargements échouent, utiliser les données d'exemple
        logger.warning("All API downloads failed, using sample data as fallback")
        return self._load_sample_data()
    
    def _load_sample_data(self) -> pd.DataFrame:
        """
        Charge les données d'exemple si l'API n'est pas disponible.
        
        Returns:
            pd.DataFrame: Données d'exemple
        """
        sample_path = DataSources.SAMPLE_DATA
        if sample_path.exists():
            logger.info(f"Loading sample data from {sample_path}")
            return pd.read_csv(sample_path)
        else:
            logger.error("No sample data available")
            raise FileNotFoundError("No data source available (API failed and no sample data)")
    
    def _file_exists_and_recent(self, max_age_hours: int = 24) -> bool:
        """
        Vérifie si le fichier local existe et est récent.
        
        Args:
            max_age_hours (int): Age maximum en heures
            
        Returns:
            bool: True si le fichier existe et est récent
        """
        if not isinstance(self.source_path, Path):
            file_path = Path(self.source_path)
        else:
            file_path = self.source_path
            
        if not file_path.exists():
            return False
        
        # Vérifier l'âge du fichier
        file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        return file_age < timedelta(hours=max_age_hours)
    
    def _save_to_cache(self):
        """Sauvegarde les données téléchargées dans le cache local."""
        if self.raw_data is not None:
            try:
                cache_file = DataSources.RAW_DATA
                cache_file.parent.mkdir(exist_ok=True)
                self.raw_data.to_csv(cache_file, index=False)
                logger.info(f"Data cached to {cache_file}")
                
                # Sauvegarder les métadonnées
                metadata = {
                    'download_time': datetime.now().isoformat(),
                    'records_count': len(self.raw_data),
                    'columns': list(self.raw_data.columns),
                    'source': str(self.source_path)
                }
                
                metadata_file = self.download_cache
                metadata_file.parent.mkdir(exist_ok=True)
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
            except Exception as e:
                logger.warning(f"Failed to cache data: {str(e)}")
    
    def get_download_stats(self) -> Dict:
        """
        Retourne les statistiques de téléchargement.
        
        Returns:
            dict: Statistiques détaillées
        """
        return {
            **self.download_stats,
            'cache_info': self._get_cache_info(),
            'data_freshness': self._get_data_freshness()
        }
    
    def _get_cache_info(self) -> Dict:
        """Informations sur le cache local."""
        cache_file = DataSources.RAW_DATA
        if cache_file.exists():
            stat = cache_file.stat()
            return {
                'exists': True,
                'size_bytes': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'age_hours': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
            }
        return {'exists': False}
    
    def _get_data_freshness(self) -> str:
        """Évalue la fraîcheur des données."""
        cache_info = self._get_cache_info()
        if not cache_info['exists']:
            return 'no_cache'
        
        age_hours = cache_info['age_hours']
        if age_hours < 1:
            return 'very_fresh'
        elif age_hours < 6:
            return 'fresh'
        elif age_hours < 24:
            return 'acceptable'
        else:
            return 'stale'
