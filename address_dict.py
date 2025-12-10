
import pandas as pd
import numpy as np
import re
import json
import requests
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AddressDictionary:
    """
    Dictionnaire d'adresses pour normalisation et géocodage.
    
    Fonctionnalités:
    - Normalisation des adresses (noms de rues, codes postaux)
    - Géocodage avec APIs (Google Maps, OpenStreetMap)
    - Cache local pour éviter les appels répétés
    - Correction automatique des erreurs courantes
    """
    
    def __init__(self, data: pd.DataFrame, cache_dir: str = "cache"):
        """
        Initialiser le dictionnaire d'adresses.
        
        Args:
            data: DataFrame contenant les adresses à traiter
            cache_dir: Répertoire pour le cache local
        """
        self.data = data.copy()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache des adresses normalisées et géocodées
        self.address_cache_file = self.cache_dir / "address_cache.json"
        self.geocode_cache_file = self.cache_dir / "geocode_cache.json"
        
        # Charger les caches existants
        self.address_cache = self._load_cache(self.address_cache_file)
        self.geocode_cache = self._load_cache(self.geocode_cache_file)
        
        # Statistiques de traitement
        self.processing_stats = {
            'addresses_normalized': 0,
            'addresses_geocoded': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': []
        }
        
        # Dictionnaires de normalisation
        self._init_normalization_dictionaries()
        
        logger.info(f"AddressDictionary initialized with {len(data)} records")
    
    def _init_normalization_dictionaries(self):
        """Initialiser les dictionnaires de normalisation."""
        
        # Normalisation des types de rues
        self.street_types = {
            'rue': ['rue', 'r.', 'r', 'street', 'st.', 'st'],
            'avenue': ['avenue', 'ave.', 'ave', 'av.', 'av'],
            'boulevard': ['boulevard', 'boul.', 'boul', 'blvd.', 'blvd', 'bd.', 'bd'],
            'chemin': ['chemin', 'ch.', 'ch', 'chem.', 'chem'],
            'place': ['place', 'pl.', 'pl'],
            'square': ['square', 'sq.', 'sq'],
            'côte': ['côte', 'cote', 'c.'],
            'rang': ['rang', 'rg.', 'rg']
        }
        
        # Directions cardinales
        self.directions = {
            'nord': ['nord', 'n.', 'n', 'north'],
            'sud': ['sud', 's.', 's', 'south'],
            'est': ['est', 'e.', 'e', 'east'],
            'ouest': ['ouest', 'o.', 'o', 'west', 'w.', 'w']
        }
        
        # Corrections d'erreurs courantes
        self.common_corrections = {
            'montréal': ['montreal', 'mtl', 'monteal', 'montrel'],
            'québec': ['quebec', 'qc', 'quebéc', 'quebeck'],
            'saint': ['st', 'st.', 'saint-', 'ste', 'ste.', 'sainte'],
            'sainte': ['ste', 'ste.', 'sainte-']
        }
    
    def _load_cache(self, cache_file: Path) -> Dict:
        """Charger un fichier de cache."""
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache {cache_file}: {e}")
        return {}
    
    def _save_cache(self, cache_data: Dict, cache_file: Path):
        """Sauvegarder un fichier de cache."""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save cache {cache_file}: {e}")
    
    def normalize_addresses(self, address_column: str = 'etablissement') -> pd.DataFrame:
        """
        Normaliser les adresses dans le DataFrame.
        
        Args:
            address_column: Nom de la colonne contenant les adresses
            
        Returns:
            DataFrame avec adresses normalisées
        """
        logger.info(f"Starting address normalization for column: {address_column}")
        
        if address_column not in self.data.columns:
            logger.error(f"Column {address_column} not found in data")
            return self.data
        
        normalized_data = self.data.copy()
        normalized_addresses = []
        
        for idx, address in enumerate(self.data[address_column]):
            if pd.isna(address):
                normalized_addresses.append(address)
                continue
            
            # Vérifier le cache
            address_str = str(address).strip()
            if address_str in self.address_cache:
                normalized_addresses.append(self.address_cache[address_str])
                self.processing_stats['cache_hits'] += 1
                continue
            
            # Normaliser l'adresse
            normalized = self._normalize_single_address(address_str)
            normalized_addresses.append(normalized)
            
            # Ajouter au cache
            self.address_cache[address_str] = normalized
            self.processing_stats['addresses_normalized'] += 1
        
        # Ajouter la colonne normalisée
        normalized_data[f"{address_column}_normalized"] = normalized_addresses

        # Actualiser les données internes pour la suite du pipeline
        self.data = normalized_data

        # Sauvegarder le cache
        self._save_cache(self.address_cache, self.address_cache_file)

        logger.info(
            f"Address normalization completed: "
            f"{self.processing_stats['addresses_normalized']} normalized"
        )
        return self.data
    
    def _normalize_single_address(self, address: str) -> str:
        """
        Normaliser une seule adresse.
        
        Args:
            address: Adresse à normaliser
            
        Returns:
            Adresse normalisée
        """
        if not address or pd.isna(address):
            return address
        
        # Convertir en minuscules et nettoyer
        normalized = str(address).lower().strip()
        
        # Supprimer les caractères spéciaux excessifs
        normalized = re.sub(r'[^\w\s\-\.\,]', ' ', normalized)
        
        # Normaliser les espaces multiples
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Corriger les erreurs courantes
        for correct, variants in self.common_corrections.items():
            for variant in variants:
                normalized = re.sub(r'\b' + re.escape(variant) + r'\b', correct, normalized)
        
        # Normaliser les types de rues
        for standard, variants in self.street_types.items():
            for variant in variants:
                pattern = r'\b' + re.escape(variant) + r'\b'
                normalized = re.sub(pattern, standard, normalized)
        
        # Normaliser les directions
        for standard, variants in self.directions.items():
            for variant in variants:
                pattern = r'\b' + re.escape(variant) + r'\b'
                normalized = re.sub(pattern, standard, normalized)
        
        # Nettoyer les espaces finaux
        normalized = normalized.strip()
        
        return normalized
    
    def geocode_addresses(self, address_column: str = 'etablissement_normalized', 
                         api_key: Optional[str] = None, provider: str = 'osm') -> pd.DataFrame:
        """
        Géocoder les adresses (convertir en latitude/longitude).
        
        Args:
            address_column: Colonne contenant les adresses à géocoder
            api_key: Clé API pour Google Maps (optionnel)
            provider: Fournisseur de géocodage ('osm' ou 'google')
            
        Returns:
            DataFrame avec coordonnées géographiques
        """
        logger.info(f"Starting geocoding with provider: {provider}")
        
        if address_column not in self.data.columns:
            logger.error(f"Column {address_column} not found")
            return self.data
        
        geocoded_data = self.data.copy()
        latitudes = []
        longitudes = []
        geocode_status = []
        
        for idx, address in enumerate(self.data[address_column]):
            if pd.isna(address):
                latitudes.append(None)
                longitudes.append(None)
                geocode_status.append('no_address')
                continue
            
            address_str = str(address).strip()
            
            # Vérifier le cache
            if address_str in self.geocode_cache:
                cached = self.geocode_cache[address_str]
                latitudes.append(cached.get('lat'))
                longitudes.append(cached.get('lng'))
                geocode_status.append(cached.get('status', 'cached'))
                self.processing_stats['cache_hits'] += 1
                continue
            
            # Géocoder l'adresse
            lat, lng, status = self._geocode_single_address(address_str, provider, api_key)
            
            latitudes.append(lat)
            longitudes.append(lng)
            geocode_status.append(status)
            
            # Ajouter au cache
            self.geocode_cache[address_str] = {
                'lat': lat,
                'lng': lng,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            self.processing_stats['addresses_geocoded'] += 1
            
            # Pause pour éviter de surcharger l'API
            if provider == 'osm':
                time.sleep(1)  # Nominatim rate limit
            elif provider == 'google':
                time.sleep(0.1)  # Google Maps rate limit
        
        # Ajouter les colonnes géocodées
        geocoded_data['latitude'] = latitudes
        geocoded_data['longitude'] = longitudes
        geocoded_data['geocode_status'] = geocode_status
        
        # Sauvegarder le cache
        self._save_cache(self.geocode_cache, self.geocode_cache_file)
        
        logger.info(f"Geocoding completed: {self.processing_stats['addresses_geocoded']} geocoded")
        return geocoded_data
    
    def _geocode_single_address(self, address: str, provider: str, api_key: Optional[str]) -> Tuple[Optional[float], Optional[float], str]:
        """
        Géocoder une seule adresse.
        
        Args:
            address: Adresse à géocoder
            provider: Fournisseur ('osm' ou 'google')
            api_key: Clé API
            
        Returns:
            Tuple (latitude, longitude, status)
        """
        try:
            if provider == 'osm':
                return self._geocode_with_osm(address)
            elif provider == 'google' and api_key:
                return self._geocode_with_google(address, api_key)
            else:
                return None, None, 'no_provider'
        except Exception as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            self.processing_stats['errors'].append(str(e))
            return None, None, 'error'
    
    def _geocode_with_osm(self, address: str) -> Tuple[Optional[float], Optional[float], str]:
        """Géocoder avec OpenStreetMap/Nominatim."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{address}, Québec, Canada",
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'MAPAQ-Address-Geocoder/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        self.processing_stats['api_calls'] += 1
        
        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                lat = float(result['lat'])
                lng = float(result['lon'])
                return lat, lng, 'success'
        
        return None, None, 'not_found'
    
    def _geocode_with_google(self, address: str, api_key: str) -> Tuple[Optional[float], Optional[float], str]:
        """Géocoder avec Google Maps API."""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': f"{address}, Québec, Canada",
            'key': api_key,
            'region': 'ca'
        }
        
        response = requests.get(url, params=params, timeout=10)
        self.processing_stats['api_calls'] += 1
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                lat = location['lat']
                lng = location['lng']
                return lat, lng, 'success'
        
        return None, None, 'not_found'
    
    def get_processing_report(self) -> Dict[str, Any]:
        """
        Obtenir un rapport de traitement des adresses.
        
        Returns:
            Dictionnaire avec statistiques de traitement
        """
        return {
            'processing_stats': self.processing_stats,
            'cache_stats': {
                'address_cache_size': len(self.address_cache),
                'geocode_cache_size': len(self.geocode_cache)
            },
            'normalization_rules': {
                'street_types': len(self.street_types),
                'directions': len(self.directions),
                'common_corrections': len(self.common_corrections)
            }
        }
    
    def export_normalized_addresses(self, output_file: str):
        """Exporter les adresses normalisées."""
        try:
            export_data = {
                'normalized_addresses': self.address_cache,
                'geocoded_addresses': self.geocode_cache,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Address data exported to {output_file}")
        except Exception as e:
            logger.error(f"Export failed: {e}")

def test_address_dictionary():
    """Test basique du dictionnaire d'adresses."""
    print("🧪 Testing AddressDictionary...")
    
    # Créer des données de test
    test_data = pd.DataFrame({
        'etablissement': [
            'Restaurant Le Gourmet, 123 rue Saint-Denis, Montréal',
            'Pizzeria Mario, 456 boul. René-Lévesque, Quebec',
            'Sushi Zen, 789 av. du Parc, MTL',
            'Café Central, 321 ch. de la Côte-des-Neiges, Montreal'
        ]
    })
    
    # Initialiser le dictionnaire
    addr_dict = AddressDictionary(test_data)
    
    # Test de normalisation
    normalized_data = addr_dict.normalize_addresses('etablissement')
    print("✅ Address normalization completed")
    
    # Afficher quelques résultats
    for i, (original, normalized) in enumerate(zip(
        test_data['etablissement'], 
        normalized_data['etablissement_normalized']
    )):
        print(f"  {i+1}. {original}")
        print(f"     → {normalized}")
    
    # Obtenir le rapport
    report = addr_dict.get_processing_report()
    print(f"\n📊 Processing Report:")
    print(f"  Addresses normalized: {report['processing_stats']['addresses_normalized']}")
    print(f"  Cache hits: {report['processing_stats']['cache_hits']}")
    
    print("🎉 AddressDictionary test completed!")

if __name__ == "__main__":
    test_address_dictionary()
