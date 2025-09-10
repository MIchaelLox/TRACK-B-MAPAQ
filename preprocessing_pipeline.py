
import sys
import os
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import warnings

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test des imports avec fallback
PANDAS_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    warnings.warn("pandas/numpy not available - limited functionality")

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    warnings.warn("scikit-learn not available - limited ML functionality")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/preprocessing_pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MAPAQPreprocessingPipeline:
    """
    Pipeline de préprocessing complet pour les données MAPAQ.
    
    Intègre tous les modules développés :
    - DataIngestor : Chargement des données
    - DataCleaner : Nettoyage et normalisation
    - CategoricalEncoder : Encodage des variables catégorielles
    - Feature Engineering : Création de variables dérivées
    - Data Validation : Contrôle qualité
    - Export : Sauvegarde des données préprocessées
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialiser le pipeline de préprocessing.
        
        Args:
            config: Configuration personnalisée du pipeline
        """
        self.config = config or self._get_default_config()
        self.pipeline_stats = {
            'start_time': None,
            'end_time': None,
            'processing_time': None,
            'stages_completed': [],
            'data_transformations': {},
            'quality_metrics': {},
            'errors': []
        }
        
        # Modules du pipeline
        self.ingestor = None
        self.cleaner = None
        self.encoder = None
        
        # Données à différentes étapes
        self.raw_data = None
        self.cleaned_data = None
        self.encoded_data = None
        self.final_data = None
        
        logger.info("MAPAQ Preprocessing Pipeline initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut du pipeline."""
        return {
            'data_sources': {
                'primary_url': 'https://donnees.montreal.ca/dataset/inspection-aliments-contrevenants/resource/92719d9b-8bf2-4dfd-b8e0-1021ffcaee2f/download/inspection-aliments-contrevenants.csv',
                'fallback_file': 'data/sample_mapaq_data.csv',
                'cache_enabled': True,
                'cache_duration_hours': 24
            },
            'cleaning': {
                'null_strategy': 'smart',
                'date_format': '%Y-%m-%d',
                'text_normalization': True,
                'outlier_detection': True,
                'duplicate_handling': 'remove'
            },
            'encoding': {
                'ordinal_variables': {
                    'statut': ['Ouvert', 'Sous inspection fédérale', 'Fermé changement d\'exploitant', 'Fermé']
                },
                'nominal_variables': ['categorie'],
                'high_cardinality_variables': ['ville', 'proprietaire'],
                'text_variables': ['description'],
                'rare_category_threshold': 5
            },
            'feature_engineering': {
                'create_temporal_features': True,
                'create_text_features': True,
                'create_interaction_features': False,
                'scaling': 'standard'
            },
            'validation': {
                'min_completeness': 80.0,
                'min_consistency': 70.0,
                'max_duplicates_percent': 5.0
            },
            'output': {
                'save_intermediate_steps': True,
                'export_formats': ['csv', 'json'],
                'include_metadata': True
            }
        }
    
    def run_complete_pipeline(self, data_source=None):
        """
        Exécuter le pipeline complet de préprocessing.
        
        Args:
            data_source: Source de données (URL ou fichier)
            
        Returns:
            DataFrame préprocessé prêt pour la modélisation
        """
        self.pipeline_stats['start_time'] = datetime.now()
        logger.info("Starting complete MAPAQ preprocessing pipeline")
        
        try:
            # Étape 1: Ingestion des données
            self.raw_data = self._stage_data_ingestion(data_source)
            self._log_stage_completion('data_ingestion', self.raw_data.shape)
            
            # Étape 2: Nettoyage des données
            self.cleaned_data = self._stage_data_cleaning()
            self._log_stage_completion('data_cleaning', self.cleaned_data.shape)
            
            # Étape 3: Encodage des variables catégorielles
            self.encoded_data = self._stage_categorical_encoding()
            self._log_stage_completion('categorical_encoding', self.encoded_data.shape)
            
            # Étape 4: Feature Engineering
            self.final_data = self._stage_feature_engineering()
            self._log_stage_completion('feature_engineering', self.final_data.shape)
            
            # Étape 5: Validation finale
            self._stage_final_validation()
            self._log_stage_completion('final_validation', None)
            
            # Étape 6: Export des résultats
            self._stage_export_results()
            self._log_stage_completion('export_results', None)
            
            self.pipeline_stats['end_time'] = datetime.now()
            self.pipeline_stats['processing_time'] = (
                self.pipeline_stats['end_time'] - self.pipeline_stats['start_time']
            ).total_seconds()
            
            logger.info(f"Pipeline completed successfully in {self.pipeline_stats['processing_time']:.2f} seconds")
            return self.final_data
            
        except Exception as e:
            self.pipeline_stats['errors'].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def _stage_data_ingestion(self, data_source: Optional[str] = None) -> pd.DataFrame:
        """Étape 1: Ingestion des données."""
        logger.info("Stage 1: Data Ingestion")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for data ingestion")
        
        try:
            from data_ingest import DataIngestor
            self.ingestor = DataIngestor()
            
            if data_source:
                if data_source.startswith('http'):
                    data = self.ingestor.load_from_url(data_source)
                else:
                    data = self.ingestor.load_from_csv(data_source)
            else:
                data = self.ingestor.load_raw_data()
            
            logger.info(f"Data ingested: {data.shape}")
            return data
            
        except ImportError:
            # Fallback: créer des données de test
            logger.warning("DataIngestor not available, using test data")
            return self._create_test_data()
    
    def _stage_data_cleaning(self) -> pd.DataFrame:
        """Étape 2: Nettoyage des données."""
        logger.info("Stage 2: Data Cleaning")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for data cleaning")
        
        try:
            from data_cleaner import DataCleaner
            self.cleaner = DataCleaner(self.raw_data)
            
            # Appliquer le pipeline de nettoyage
            cleaned_data = self.cleaner.clean_pipeline()
            
            # Sauvegarder les statistiques de nettoyage
            cleaning_report = self.cleaner.get_cleaning_report()
            self.pipeline_stats['data_transformations']['cleaning'] = cleaning_report
            
            logger.info(f"Data cleaned: {cleaned_data.shape}")
            return cleaned_data
            
        except ImportError:
            # Fallback: nettoyage basique
            logger.warning("DataCleaner not available, using basic cleaning")
            return self._basic_data_cleaning(self.raw_data)
    
    def _stage_categorical_encoding(self) -> pd.DataFrame:
        """Étape 3: Encodage des variables catégorielles."""
        logger.info("Stage 3: Categorical Encoding")
        
        try:
            from categorical_encoder import CategoricalEncoder
            self.encoder = CategoricalEncoder(self.cleaned_data)
            
            # Appliquer l'encodage spécialisé MAPAQ
            encoded_data = self.encoder.encode_mapaq_specific_variables()
            
            # Sauvegarder les statistiques d'encodage
            encoding_report = self.encoder.get_encoding_report()
            self.pipeline_stats['data_transformations']['encoding'] = encoding_report
            
            logger.info(f"Data encoded: {encoded_data.shape}")
            return encoded_data
            
        except ImportError:
            # Fallback: encodage basique
            logger.warning("CategoricalEncoder not available, using basic encoding")
            return self._basic_categorical_encoding(self.cleaned_data)
    
    def _stage_feature_engineering(self) -> pd.DataFrame:
        """Étape 4: Feature Engineering."""
        logger.info("Stage 4: Feature Engineering")
        
        engineered_data = self.encoded_data.copy()
        
        if self.config['feature_engineering']['create_temporal_features']:
            engineered_data = self._create_temporal_features(engineered_data)
        
        if self.config['feature_engineering']['create_text_features']:
            engineered_data = self._create_text_features(engineered_data)
        
        if self.config['feature_engineering']['scaling'] and SKLEARN_AVAILABLE:
            engineered_data = self._apply_feature_scaling(engineered_data)
        
        logger.info(f"Feature engineering completed: {engineered_data.shape}")
        return engineered_data
    
    def _stage_final_validation(self):
        """Étape 5: Validation finale."""
        logger.info("Stage 5: Final Validation")
        
        validation_results = {
            'completeness': self._calculate_completeness(),
            'consistency': self._calculate_consistency(),
            'duplicates_percent': self._calculate_duplicates_percent(),
            'feature_count': len(self.final_data.columns),
            'record_count': len(self.final_data)
        }
        
        self.pipeline_stats['quality_metrics'] = validation_results
        
        # Vérifier les seuils de qualité
        issues = []
        if validation_results['completeness'] < self.config['validation']['min_completeness']:
            issues.append(f"Completeness {validation_results['completeness']:.1f}% below threshold")
        
        if validation_results['consistency'] < self.config['validation']['min_consistency']:
            issues.append(f"Consistency {validation_results['consistency']:.1f}% below threshold")
        
        if validation_results['duplicates_percent'] > self.config['validation']['max_duplicates_percent']:
            issues.append(f"Duplicates {validation_results['duplicates_percent']:.1f}% above threshold")
        
        if issues:
            logger.warning(f"Validation issues: {issues}")
        else:
            logger.info("Final validation passed")
    
    def _stage_export_results(self):
        """Étape 6: Export des résultats."""
        logger.info("Stage 6: Export Results")
        
        # Créer le dossier de sortie
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export CSV
        if 'csv' in self.config['output']['export_formats']:
            csv_path = output_dir / f"mapaq_preprocessed_{timestamp}.csv"
            self.final_data.to_csv(csv_path, index=False)
            logger.info(f"Data exported to CSV: {csv_path}")
        
        # Export JSON metadata
        if self.config['output']['include_metadata']:
            metadata_path = output_dir / f"preprocessing_metadata_{timestamp}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.pipeline_stats, f, indent=2, default=str, ensure_ascii=False)
            logger.info(f"Metadata exported: {metadata_path}")
    
    def _create_test_data(self) -> pd.DataFrame:
        """Créer des données de test pour le fallback."""
        test_data = {
            'id_poursuite': range(1, 101),
            'business_id': [12345 + i for i in range(100)],
            'date': ['2024-01-15'] * 100,
            'date_jugement': ['2024-02-20'] * 100,
            'description': ['Température inadéquate'] * 50 + ['Contamination croisée'] * 50,
            'etablissement': [f'Restaurant {i}' for i in range(100)],
            'montant': [500 + (i * 10) for i in range(100)],
            'proprietaire': [f'Propriétaire {i}' for i in range(100)],
            'ville': ['Montréal'] * 80 + ['Québec'] * 20,
            'statut': ['Ouvert'] * 90 + ['Fermé'] * 10,
            'date_statut': ['2024-01-01'] * 100,
            'categorie': ['Restaurant'] * 80 + ['Café'] * 20
        }
        
        return pd.DataFrame(test_data)
    
    def _basic_data_cleaning(self, data: pd.DataFrame) -> pd.DataFrame:
        """Nettoyage basique sans DataCleaner."""
        cleaned = data.copy()
        
        # Supprimer les lignes complètement vides
        cleaned = cleaned.dropna(how='all')
        
        # Remplir les nulls numériques avec la médiane
        numeric_columns = cleaned.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            cleaned[col].fillna(cleaned[col].median(), inplace=True)
        
        # Remplir les nulls textuels avec 'Unknown'
        text_columns = cleaned.select_dtypes(include=['object']).columns
        for col in text_columns:
            cleaned[col].fillna('Unknown', inplace=True)
        
        return cleaned
    
    def _basic_categorical_encoding(self, data: pd.DataFrame) -> pd.DataFrame:
        """Encodage catégoriel basique."""
        encoded = data.copy()
        
        # Encodage ordinal pour le statut
        if 'statut' in encoded.columns:
            status_mapping = {'Ouvert': 0, 'Sous inspection fédérale': 1, 'Fermé changement d\'exploitant': 2, 'Fermé': 3}
            encoded['statut_encoded'] = encoded['statut'].map(status_mapping).fillna(0)
        
        # One-hot encoding pour les catégories
        if 'categorie' in encoded.columns:
            dummies = pd.get_dummies(encoded['categorie'], prefix='cat')
            encoded = pd.concat([encoded, dummies], axis=1)
        
        return encoded
    
    def _create_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Créer des features temporelles."""
        temporal_data = data.copy()
        
        # Features basées sur les dates si disponibles
        date_columns = [col for col in data.columns if 'date' in col.lower()]
        
        for col in date_columns:
            if col in temporal_data.columns:
                try:
                    temporal_data[col] = pd.to_datetime(temporal_data[col], errors='coerce')
                    temporal_data[f'{col}_year'] = temporal_data[col].dt.year
                    temporal_data[f'{col}_month'] = temporal_data[col].dt.month
                    temporal_data[f'{col}_dayofweek'] = temporal_data[col].dt.dayofweek
                except:
                    pass
        
        return temporal_data
    
    def _create_text_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Créer des features textuelles basiques."""
        text_data = data.copy()
        
        # Features de longueur de texte
        text_columns = ['description', 'etablissement']
        
        for col in text_columns:
            if col in text_data.columns:
                text_data[f'{col}_length'] = text_data[col].astype(str).str.len()
                text_data[f'{col}_word_count'] = text_data[col].astype(str).str.split().str.len()
        
        return text_data
    
    def _apply_feature_scaling(self, data: pd.DataFrame) -> pd.DataFrame:
        """Appliquer la normalisation des features."""
        scaled_data = data.copy()
        
        # Identifier les colonnes numériques
        numeric_columns = scaled_data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) > 0:
            scaler = StandardScaler()
            scaled_data[numeric_columns] = scaler.fit_transform(scaled_data[numeric_columns])
        
        return scaled_data
    
    def _calculate_completeness(self) -> float:
        """Calculer le taux de complétude."""
        if self.final_data is None:
            return 0.0
        
        total_cells = self.final_data.size
        non_null_cells = total_cells - self.final_data.isnull().sum().sum()
        
        return (non_null_cells / total_cells) * 100 if total_cells > 0 else 0.0
    
    def _calculate_consistency(self) -> float:
        """Calculer le taux de cohérence."""
        # Métrique simplifiée basée sur les types de données
        if self.final_data is None:
            return 0.0
        
        consistent_columns = 0
        total_columns = len(self.final_data.columns)
        
        for col in self.final_data.columns:
            # Vérifier la cohérence des types
            if self.final_data[col].dtype != 'object' or self.final_data[col].isnull().sum() == 0:
                consistent_columns += 1
        
        return (consistent_columns / total_columns) * 100 if total_columns > 0 else 0.0
    
    def _calculate_duplicates_percent(self) -> float:
        """Calculer le pourcentage de doublons."""
        if self.final_data is None:
            return 0.0
        
        total_rows = len(self.final_data)
        duplicate_rows = self.final_data.duplicated().sum()
        
        return (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0.0
    
    def _log_stage_completion(self, stage_name: str, shape: Optional[Tuple] = None):
        """Logger la completion d'une étape."""
        self.pipeline_stats['stages_completed'].append({
            'stage': stage_name,
            'timestamp': datetime.now().isoformat(),
            'data_shape': shape
        })
        
        if shape:
            logger.info(f"Stage {stage_name} completed - Data shape: {shape}")
        else:
            logger.info(f"Stage {stage_name} completed")
    
    def get_pipeline_report(self) -> Dict[str, Any]:
        """Obtenir un rapport complet du pipeline."""
        return {
            'pipeline_config': self.config,
            'pipeline_stats': self.pipeline_stats,
            'data_summary': {
                'raw_data_shape': self.raw_data.shape if self.raw_data is not None else None,
                'final_data_shape': self.final_data.shape if self.final_data is not None else None,
                'feature_expansion_ratio': (
                    len(self.final_data.columns) / len(self.raw_data.columns)
                    if self.raw_data is not None and self.final_data is not None
                    else None
                )
            },
            'quality_assessment': self.pipeline_stats.get('quality_metrics', {}),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Générer des recommandations basées sur les résultats."""
        recommendations = []
        
        quality_metrics = self.pipeline_stats.get('quality_metrics', {})
        
        if quality_metrics.get('completeness', 100) < 90:
            recommendations.append("Consider improving data collection to reduce missing values")
        
        if quality_metrics.get('feature_count', 0) > 100:
            recommendations.append("Consider feature selection to reduce dimensionality")
        
        if self.pipeline_stats.get('processing_time', 0) > 60:
            recommendations.append("Consider optimizing pipeline for better performance")
        
        return recommendations

def run_mapaq_preprocessing_pipeline(data_source: Optional[str] = None) -> Dict[str, Any]:
    """
    Fonction principale pour exécuter le pipeline MAPAQ.
    
    Args:
        data_source: Source de données optionnelle
        
    Returns:
        Rapport complet du pipeline
    """
    print("🚀 MAPAQ Preprocessing Pipeline - Heures 25-28")
    print("=" * 70)
    print("Pipeline de préprocessing complet")
    print("=" * 70)
    
    try:
        # Initialiser et exécuter le pipeline
        pipeline = MAPAQPreprocessingPipeline()
        processed_data = pipeline.run_complete_pipeline(data_source)
        
        # Obtenir le rapport
        report = pipeline.get_pipeline_report()
        
        # Afficher les résultats
        print(f"\n📊 Pipeline Results:")
        print(f"  Processing Time: {report['pipeline_stats']['processing_time']:.2f} seconds")
        print(f"  Stages Completed: {len(report['pipeline_stats']['stages_completed'])}")
        print(f"  Data Transformation: {report['data_summary']['raw_data_shape']} → {report['data_summary']['final_data_shape']}")
        
        quality = report['quality_assessment']
        if quality:
            print(f"\n📈 Data Quality:")
            print(f"  Completeness: {quality.get('completeness', 0):.1f}%")
            print(f"  Consistency: {quality.get('consistency', 0):.1f}%")
            print(f"  Duplicates: {quality.get('duplicates_percent', 0):.1f}%")
        
        recommendations = report['recommendations']
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print(f"\n🎉 PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"✅ Ready for Semaine 2: Dictionnaires et enrichissement")
        
        return report
        
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Exécuter le pipeline avec gestion d'erreurs
    try:
        report = run_mapaq_preprocessing_pipeline()
    except Exception as e:
        print(f"💥 Critical error: {str(e)}")
        sys.exit(1)
