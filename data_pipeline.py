"""
Pipeline de Données Complet - MAPAQ Track-B
============================================
Pipeline ETL automatisé pour le traitement des données d'inspection MAPAQ

Auteur: Grace MANDIANGU
Date: 2025-11-17
"""

import logging
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import traceback

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Étapes du pipeline"""
    INGESTION = "ingestion"
    CLEANING = "cleaning"
    ENRICHMENT = "enrichment"
    MODELING = "modeling"
    VALIDATION = "validation"
    STORAGE = "storage"


@dataclass
class PipelineConfig:
    """Configuration du pipeline"""
    source_data_path: str = "data/raw/mapaq_inspections.csv"
    output_db_path: str = "mapaq_dashboard.db"
    backup_enabled: bool = True
    max_retries: int = 3
    batch_size: int = 100


class DataPipelineManager:
    """Gestionnaire principal du pipeline de données MAPAQ"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._setup_directories()
        logger.info(f"Pipeline initialisé - ID: {self.execution_id}")
    
    def _setup_directories(self):
        """Crée les dossiers nécessaires"""
        for directory in ["data/raw", "data/processed", "data/backups", "logs"]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Exécute le pipeline complet"""
        logger.info("="*70)
        logger.info("🚀 DÉMARRAGE DU PIPELINE COMPLET MAPAQ")
        logger.info("="*70)
        
        try:
            # 1. Ingestion
            raw_data = self._stage_ingestion()
            logger.info(f"✅ Ingestion: {len(raw_data)} enregistrements")
            
            # 2. Nettoyage
            cleaned_data = self._stage_cleaning(raw_data)
            logger.info(f"✅ Nettoyage: {len(cleaned_data)} enregistrements")
            
            # 3. Enrichissement
            enriched_data = self._stage_enrichment(cleaned_data)
            logger.info(f"✅ Enrichissement: {len(enriched_data)} enregistrements")
            
            # 4. Modélisation
            modeled_data = self._stage_modeling(enriched_data)
            logger.info(f"✅ Modélisation: {len(modeled_data)} prédictions")
            
            # 5. Validation
            validated_data = self._stage_validation(modeled_data)
            logger.info(f"✅ Validation: {len(validated_data)} enregistrements")
            
            # 6. Sauvegarde
            storage_result = self._stage_storage(validated_data)
            logger.info(f"✅ Sauvegarde: {storage_result['inserted']} insérés, {storage_result['updated']} mis à jour")
            
            logger.info("="*70)
            logger.info("✅ PIPELINE COMPLÉTÉ AVEC SUCCÈS")
            logger.info("="*70)
            
            return {'status': 'success', 'records_processed': len(validated_data)}
            
        except Exception as e:
            logger.error(f"❌ ERREUR PIPELINE: {e}")
            logger.error(traceback.format_exc())
            return {'status': 'failed', 'error': str(e)}
    
    def _stage_ingestion(self) -> List[Dict]:
        """Étape 1: Ingestion des données"""
        logger.info("📥 Ingestion des données...")
        
        source_path = Path(self.config.source_data_path)
        if source_path.exists():
            logger.info(f"Chargement depuis: {source_path}")
            # TODO: Charger CSV réel
            return self._generate_demo_data()
        else:
            logger.warning("Fichier source non trouvé, génération de données démo")
            return self._generate_demo_data()
    
    def _generate_demo_data(self) -> List[Dict]:
        """Génère des données de démonstration"""
        return [
            {'etablissement': 'Restaurant Le Gourmet', 'adresse': '1234 Rue Saint-Denis, Montréal',
             'date_inspection': '2024-11-01', 'infractions': 'Température inadéquate', 'statut': 'Non conforme'},
            {'etablissement': 'Sushi Express', 'adresse': '5678 Boulevard Saint-Laurent, Montréal',
             'date_inspection': '2024-10-28', 'infractions': '', 'statut': 'Conforme'},
            {'etablissement': 'Pizzeria Bella', 'adresse': '9012 Avenue du Parc, Montréal',
             'date_inspection': '2024-10-25', 'infractions': 'Formation insuffisante', 'statut': 'Conforme avec remarques'},
        ]
    
    def _stage_cleaning(self, raw_data: List[Dict]) -> List[Dict]:
        """Étape 2: Nettoyage"""
        logger.info("🧹 Nettoyage des données...")
        cleaned = []
        
        for record in raw_data:
            cleaned_record = {
                'nom': record.get('etablissement', '').strip(),
                'adresse': record.get('adresse', '').strip(),
                'date_inspection': record.get('date_inspection', datetime.now().strftime('%Y-%m-%d')),
                'infractions': record.get('infractions', '').strip(),
                'statut': record.get('statut', '').strip(),
                'nb_infractions': len([i for i in record.get('infractions', '').split(',') if i.strip()])
            }
            
            if cleaned_record['nom'] and cleaned_record['adresse']:
                cleaned.append(cleaned_record)
        
        return cleaned
    
    def _stage_enrichment(self, cleaned_data: List[Dict]) -> List[Dict]:
        """Étape 3: Enrichissement"""
        logger.info("🔍 Enrichissement des données...")
        enriched = []
        
        for record in cleaned_data:
            enriched_record = record.copy()
            enriched_record['theme'] = self._detect_theme(record['nom'])
            enriched_record['zone'] = self._extract_zone(record['adresse'])
            enriched_record['taille'] = self._estimate_size(record['nom'])
            enriched.append(enriched_record)
        
        return enriched
    
    def _stage_modeling(self, enriched_data: List[Dict]) -> List[Dict]:
        """Étape 4: Modélisation"""
        logger.info("🤖 Modélisation et prédiction...")
        modeled = []
        
        for record in enriched_data:
            modeled_record = record.copy()
            score = self._calculate_risk_score(record)
            modeled_record['score_risque'] = round(score, 1)
            modeled_record['categorie_risque'] = self._categorize_risk(score)
            modeled_record['probabilite_infraction'] = min(score / 100, 1.0)
            modeled_record['prochaine_inspection'] = self._calculate_next_inspection(
                record['date_inspection'], score
            )
            modeled_record['id'] = f"REST_{hash(record['nom'] + record['adresse']) % 100000:05d}"
            modeled.append(modeled_record)
        
        return modeled
    
    def _stage_validation(self, modeled_data: List[Dict]) -> List[Dict]:
        """Étape 5: Validation"""
        logger.info("✔️  Validation des résultats...")
        validated = []
        
        for record in modeled_data:
            if (0 <= record.get('score_risque', -1) <= 100 and
                record.get('categorie_risque') in ['critique', 'eleve', 'moyen', 'faible']):
                validated.append(record)
        
        return validated
    
    def _stage_storage(self, validated_data: List[Dict]) -> Dict:
        """Étape 6: Sauvegarde"""
        logger.info("💾 Sauvegarde dans la base de données...")
        
        conn = sqlite3.connect(self.config.output_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                adresse TEXT,
                zone TEXT,
                theme TEXT,
                taille TEXT,
                score_risque REAL,
                categorie_risque TEXT,
                probabilite_infraction REAL,
                date_inspection TEXT,
                prochaine_inspection TEXT,
                nb_infractions INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        inserted, updated = 0, 0
        
        for record in validated_data:
            cursor.execute('SELECT id FROM restaurants WHERE id = ?', (record['id'],))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE restaurants SET nom=?, adresse=?, zone=?, theme=?, taille=?,
                    score_risque=?, categorie_risque=?, probabilite_infraction=?,
                    date_inspection=?, prochaine_inspection=?, nb_infractions=?, updated_at=?
                    WHERE id=?
                ''', (record['nom'], record['adresse'], record['zone'], record['theme'], record['taille'],
                      record['score_risque'], record['categorie_risque'], record['probabilite_infraction'],
                      record['date_inspection'], record['prochaine_inspection'], record['nb_infractions'],
                      datetime.now().isoformat(), record['id']))
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO restaurants VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (record['id'], record['nom'], record['adresse'], record['zone'], record['theme'], record['taille'],
                      record['score_risque'], record['categorie_risque'], record['probabilite_infraction'],
                      record['date_inspection'], record['prochaine_inspection'], record['nb_infractions'],
                      datetime.now().isoformat(), datetime.now().isoformat()))
                inserted += 1
        
        conn.commit()
        conn.close()
        
        return {'inserted': inserted, 'updated': updated, 'total': len(validated_data)}
    
    def _detect_theme(self, nom: str) -> str:
        """Détecte le thème/cuisine"""
        nom_lower = nom.lower()
        themes = {
            'italien': ['trattoria', 'pizzeria', 'pasta', 'italien'],
            'asiatique': ['sushi', 'ramen', 'asian', 'chinois'],
            'français': ['bistro', 'brasserie', 'français', 'gourmet'],
            'fast-food': ['burger', 'fast', 'quick', 'express']
        }
        
        for theme, keywords in themes.items():
            if any(k in nom_lower for k in keywords):
                return theme
        return 'autre'
    
    def _extract_zone(self, adresse: str) -> str:
        """Extrait la zone géographique"""
        zones = ['Plateau Mont-Royal', 'Ville-Marie', 'Rosemont', 'Côte-des-Neiges']
        for zone in zones:
            if zone.lower() in adresse.lower():
                return zone
        return 'Montréal'
    
    def _estimate_size(self, nom: str) -> str:
        """Estime la taille"""
        nom_lower = nom.lower()
        if any(w in nom_lower for w in ['express', 'quick', 'snack']):
            return 'petit'
        elif any(w in nom_lower for w in ['palace', 'grand', 'royal']):
            return 'grand'
        return 'moyen'
    
    def _calculate_risk_score(self, record: Dict) -> float:
        """Calcule le score de risque"""
        score = 50.0
        score += record.get('nb_infractions', 0) * 15
        
        statut = record.get('statut', '').lower()
        if 'non conforme' in statut:
            score += 30
        elif 'remarques' in statut:
            score += 10
        
        return min(score, 100.0)
    
    def _categorize_risk(self, score: float) -> str:
        """Catégorise le risque"""
        if score >= 80:
            return 'critique'
        elif score >= 60:
            return 'eleve'
        elif score >= 40:
            return 'moyen'
        return 'faible'
    
    def _calculate_next_inspection(self, last_inspection: str, score: float) -> str:
        """Calcule la date de prochaine inspection"""
        try:
            last_date = datetime.strptime(last_inspection, '%Y-%m-%d')
        except:
            last_date = datetime.now()
        
        if score >= 80:
            days = 30
        elif score >= 60:
            days = 90
        else:
            days = 180
        
        next_date = last_date + timedelta(days=days)
        return next_date.strftime('%Y-%m-%d')


if __name__ == '__main__':
    pipeline = DataPipelineManager()
    result = pipeline.run_full_pipeline()
    print(f"\n{'='*70}")
    print(f"Résultat: {result['status']}")
    print(f"{'='*70}")
