
import sys
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime

# Ajout du répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from config import LoggingConfig, ModelConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/categorical_encoder.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CategoricalEncoder:
    """
    Encodeur avancé pour variables catégorielles MAPAQ.
    
    Fonctionnalités:
    - Encodage ordinal pour variables avec ordre naturel
    - One-hot encoding pour variables nominales
    - Label encoding avec gestion des nouvelles catégories
    - Encodage de fréquence pour variables haute cardinalité
    - Target encoding pour améliorer la prédictivité
    - Encodage de texte avec TF-IDF pour descriptions
    - Gestion des catégories rares et regroupement
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, target_column: Optional[str] = None):
        """
        Initialiser l'encodeur catégoriel.
        
        Args:
            data: DataFrame à encoder
            target_column: Colonne cible pour target encoding
        """
        self.data = data.copy() if data is not None else None
        self.target_column = target_column
        self.encoders = {}
        self.encoding_mappings = {}
        self.encoding_stats = {}
        self.rare_categories = {}
        
        logger.info("CategoricalEncoder initialized")
        
        if self.data is not None:
            self._analyze_categorical_variables()
    
    def _analyze_categorical_variables(self):
        """Analyser les variables catégorielles du dataset."""
        if self.data is None:
            return
        
        categorical_analysis = {}
        
        for column in self.data.columns:
            if self.data[column].dtype == 'object' or self.data[column].dtype.name == 'category':
                unique_count = self.data[column].nunique()
                total_count = len(self.data[column])
                null_count = self.data[column].isnull().sum()
                
                # Calculer la cardinalité relative
                cardinality_ratio = unique_count / total_count if total_count > 0 else 0
                
                # Déterminer le type d'encodage recommandé
                if unique_count <= 2:
                    recommended_encoding = 'binary'
                elif unique_count <= 10 and cardinality_ratio < 0.5:
                    recommended_encoding = 'one_hot'
                elif unique_count <= 50:
                    recommended_encoding = 'label_encoding'
                else:
                    recommended_encoding = 'frequency_encoding'
                
                categorical_analysis[column] = {
                    'unique_count': unique_count,
                    'cardinality_ratio': cardinality_ratio,
                    'null_count': null_count,
                    'recommended_encoding': recommended_encoding,
                    'sample_values': list(self.data[column].dropna().unique()[:5])
                }
        
        self.encoding_stats['categorical_analysis'] = categorical_analysis
        logger.info(f"Analyzed {len(categorical_analysis)} categorical variables")
    
    def encode_ordinal_variables(self, ordinal_mappings: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Encoder les variables ordinales avec ordre spécifique.
        
        Args:
            ordinal_mappings: Dict avec nom_colonne -> liste_ordonnée_valeurs
            
        Returns:
            DataFrame avec variables ordinales encodées
        """
        if self.data is None:
            raise ValueError("No data provided for encoding")
        
        encoded_data = self.data.copy()
        
        for column, order in ordinal_mappings.items():
            if column not in encoded_data.columns:
                logger.warning(f"Column {column} not found in data")
                continue
            
            # Créer le mapping ordinal
            ordinal_mapping = {value: idx for idx, value in enumerate(order)}
            
            # Encoder la colonne
            encoded_column = f"{column}_ordinal"
            encoded_data[encoded_column] = encoded_data[column].map(ordinal_mapping)
            
            # Gérer les valeurs non mappées
            unmapped_count = encoded_data[encoded_column].isnull().sum()
            if unmapped_count > 0:
                logger.warning(f"Column {column}: {unmapped_count} unmapped values")
                # Assigner la valeur médiane aux non-mappés
                median_value = len(order) // 2
                encoded_data[encoded_column].fillna(median_value, inplace=True)
            
            # Sauvegarder le mapping
            self.encoding_mappings[column] = {
                'type': 'ordinal',
                'mapping': ordinal_mapping,
                'encoded_column': encoded_column
            }
            
            logger.info(f"Ordinal encoding completed for {column}")
        
        return encoded_data
    
    def encode_nominal_variables(self, columns: List[str], max_categories: int = 20) -> pd.DataFrame:
        """
        Encoder les variables nominales avec one-hot encoding.
        
        Args:
            columns: Liste des colonnes à encoder
            max_categories: Nombre maximum de catégories pour one-hot
            
        Returns:
            DataFrame avec variables nominales encodées
        """
        if self.data is None:
            raise ValueError("No data provided for encoding")
        
        encoded_data = self.data.copy()
        
        for column in columns:
            if column not in encoded_data.columns:
                logger.warning(f"Column {column} not found in data")
                continue
            
            # Vérifier la cardinalité
            unique_count = encoded_data[column].nunique()
            if unique_count > max_categories:
                logger.warning(f"Column {column} has {unique_count} categories (>{max_categories}), using frequency encoding instead")
                encoded_data = self._frequency_encode_column(encoded_data, column)
                continue
            
            # One-hot encoding
            if SKLEARN_AVAILABLE:
                # Utiliser pandas get_dummies pour simplicité
                dummies = pd.get_dummies(encoded_data[column], prefix=f"{column}_cat", dummy_na=True)
                encoded_data = pd.concat([encoded_data, dummies], axis=1)
                
                # Sauvegarder les informations d'encodage
                self.encoding_mappings[column] = {
                    'type': 'one_hot',
                    'categories': list(dummies.columns),
                    'original_categories': list(encoded_data[column].unique())
                }
            else:
                # Fallback manuel
                unique_values = encoded_data[column].dropna().unique()
                for value in unique_values:
                    new_col = f"{column}_cat_{value}"
                    encoded_data[new_col] = (encoded_data[column] == value).astype(int)
                
                self.encoding_mappings[column] = {
                    'type': 'one_hot_manual',
                    'categories': [f"{column}_cat_{v}" for v in unique_values]
                }
            
            logger.info(f"One-hot encoding completed for {column}")
        
        return encoded_data
    
    def _frequency_encode_column(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """Encoder une colonne par fréquence."""
        frequency_map = data[column].value_counts().to_dict()
        encoded_column = f"{column}_freq"
        data[encoded_column] = data[column].map(frequency_map)
        
        self.encoding_mappings[column] = {
            'type': 'frequency',
            'mapping': frequency_map,
            'encoded_column': encoded_column
        }
        
        return data
    
    def encode_high_cardinality_variables(self, columns: List[str], min_frequency: int = 5) -> pd.DataFrame:
        """
        Encoder les variables à haute cardinalité avec regroupement des catégories rares.
        
        Args:
            columns: Colonnes à encoder
            min_frequency: Fréquence minimale pour garder une catégorie
            
        Returns:
            DataFrame avec variables haute cardinalité encodées
        """
        if self.data is None:
            raise ValueError("No data provided for encoding")
        
        encoded_data = self.data.copy()
        
        for column in columns:
            if column not in encoded_data.columns:
                continue
            
            # Calculer les fréquences
            value_counts = encoded_data[column].value_counts()
            
            # Identifier les catégories rares
            rare_categories = value_counts[value_counts < min_frequency].index.tolist()
            common_categories = value_counts[value_counts >= min_frequency].index.tolist()
            
            # Regrouper les catégories rares
            encoded_data[column] = encoded_data[column].apply(
                lambda x: 'RARE_CATEGORY' if x in rare_categories else x
            )
            
            # Encoder par fréquence
            encoded_data = self._frequency_encode_column(encoded_data, column)
            
            # Sauvegarder les catégories rares
            self.rare_categories[column] = {
                'rare_categories': rare_categories,
                'common_categories': common_categories,
                'min_frequency': min_frequency
            }
            
            logger.info(f"High cardinality encoding for {column}: {len(rare_categories)} rare categories grouped")
        
        return encoded_data
    
    def encode_text_variables(self, columns: List[str], max_features: int = 100) -> pd.DataFrame:
        """
        Encoder les variables textuelles avec TF-IDF.
        
        Args:
            columns: Colonnes textuelles à encoder
            max_features: Nombre maximum de features TF-IDF
            
        Returns:
            DataFrame avec features textuelles
        """
        if self.data is None:
            raise ValueError("No data provided for encoding")
        
        encoded_data = self.data.copy()
        
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping text encoding")
            return encoded_data
        
        for column in columns:
            if column not in encoded_data.columns:
                continue
            
            # Préparer le texte
            text_data = encoded_data[column].fillna('').astype(str)
            
            # TF-IDF Vectorization
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            try:
                tfidf_matrix = vectorizer.fit_transform(text_data)
                feature_names = vectorizer.get_feature_names_out()
                
                # Créer les colonnes TF-IDF
                tfidf_df = pd.DataFrame(
                    tfidf_matrix.toarray(),
                    columns=[f"{column}_tfidf_{name}" for name in feature_names],
                    index=encoded_data.index
                )
                
                # Ajouter au dataset
                encoded_data = pd.concat([encoded_data, tfidf_df], axis=1)
                
                # Sauvegarder le vectorizer
                self.encoders[column] = {
                    'type': 'tfidf',
                    'vectorizer': vectorizer,
                    'feature_names': list(feature_names)
                }
                
                logger.info(f"TF-IDF encoding for {column}: {len(feature_names)} features created")
                
            except Exception as e:
                logger.error(f"TF-IDF encoding failed for {column}: {str(e)}")
        
        return encoded_data
    
    def encode_mapaq_specific_variables(self) -> pd.DataFrame:
        """
        Encoder les variables spécifiques au domaine MAPAQ.
        
        Returns:
            DataFrame avec encodage spécialisé MAPAQ
        """
        if self.data is None:
            raise ValueError("No data provided for encoding")
        
        encoded_data = self.data.copy()
        
        # Encodage ordinal pour le statut (ordre de sévérité)
        status_order = [
            'Ouvert',
            'Sous inspection fédérale', 
            'Fermé changement d\'exploitant',
            'Fermé'
        ]
        
        if 'statut' in encoded_data.columns:
            encoded_data = self.encode_ordinal_variables({'statut': status_order})
        
        # Encodage des catégories d'établissement
        if 'categorie' in encoded_data.columns:
            encoded_data = self.encode_nominal_variables(['categorie'])
        
        # Encodage haute cardinalité pour les villes
        if 'ville' in encoded_data.columns:
            encoded_data = self.encode_high_cardinality_variables(['ville'], min_frequency=10)
        
        # Encodage textuel pour les descriptions
        if 'description' in encoded_data.columns:
            encoded_data = self.encode_text_variables(['description'], max_features=50)
        
        # Encodage des propriétaires (haute cardinalité)
        if 'proprietaire' in encoded_data.columns:
            encoded_data = self.encode_high_cardinality_variables(['proprietaire'], min_frequency=3)
        
        logger.info("MAPAQ-specific encoding completed")
        return encoded_data
    
    def get_encoding_report(self) -> Dict[str, Any]:
        """
        Générer un rapport complet de l'encodage.
        
        Returns:
            Dictionnaire avec statistiques d'encodage
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'encoding_summary': {
                'total_variables_encoded': len(self.encoding_mappings),
                'encoding_types_used': list(set(
                    mapping['type'] for mapping in self.encoding_mappings.values()
                )),
                'rare_categories_grouped': len(self.rare_categories)
            },
            'variable_details': {},
            'recommendations': []
        }
        
        # Détails par variable
        for column, mapping in self.encoding_mappings.items():
            details = {
                'encoding_type': mapping['type'],
                'original_column': column
            }
            
            if mapping['type'] == 'one_hot':
                details['new_columns_count'] = len(mapping.get('categories', []))
            elif mapping['type'] in ['ordinal', 'frequency']:
                details['encoded_column'] = mapping.get('encoded_column')
            elif mapping['type'] == 'tfidf':
                details['features_count'] = len(mapping.get('feature_names', []))
            
            report['variable_details'][column] = details
        
        # Recommandations
        if len(self.encoding_mappings) == 0:
            report['recommendations'].append("No categorical variables were encoded")
        
        if self.data is not None:
            total_columns_before = len(self.data.columns)
            if hasattr(self, 'encoded_data'):
                total_columns_after = len(self.encoded_data.columns)
                expansion_ratio = total_columns_after / total_columns_before
                if expansion_ratio > 3:
                    report['recommendations'].append(
                        f"High feature expansion ({expansion_ratio:.1f}x) - consider dimensionality reduction"
                    )
        
        return report
    
    def save_encoders(self, filepath: str):
        """Sauvegarder les encodeurs pour réutilisation."""
        encoder_data = {
            'encoding_mappings': self.encoding_mappings,
            'rare_categories': self.rare_categories,
            'encoding_stats': self.encoding_stats
        }
        
        # Note: Les objets sklearn ne sont pas sérialisables en JSON
        # Pour une implémentation complète, utiliser pickle ou joblib
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(encoder_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Encoders saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save encoders: {str(e)}")
    
    def load_encoders(self, filepath: str):
        """Charger les encodeurs sauvegardés."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                encoder_data = json.load(f)
            
            self.encoding_mappings = encoder_data.get('encoding_mappings', {})
            self.rare_categories = encoder_data.get('rare_categories', {})
            self.encoding_stats = encoder_data.get('encoding_stats', {})
            
            logger.info(f"Encoders loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load encoders: {str(e)}")

def create_mapaq_encoder_pipeline(data: pd.DataFrame) -> Tuple[pd.DataFrame, CategoricalEncoder]:
    """
    Créer un pipeline complet d'encodage pour les données MAPAQ.
    
    Args:
        data: DataFrame MAPAQ à encoder
        
    Returns:
        Tuple (données encodées, encodeur configuré)
    """
    encoder = CategoricalEncoder(data)
    
    # Appliquer l'encodage spécialisé MAPAQ
    encoded_data = encoder.encode_mapaq_specific_variables()
    
    # Générer le rapport
    report = encoder.get_encoding_report()
    
    logger.info("MAPAQ encoding pipeline completed")
    logger.info(f"Encoding summary: {report['encoding_summary']}")
    
    return encoded_data, encoder

# Test et validation
if __name__ == "__main__":
    # Test basique sans dépendances
    print("🧪 Testing CategoricalEncoder...")
    
    if not SKLEARN_AVAILABLE:
        print("⚠️  scikit-learn not available - limited functionality")
    
    # Créer des données de test
    test_data = {
        'statut': ['Ouvert', 'Fermé', 'Ouvert', 'Sous inspection fédérale'],
        'categorie': ['Restaurant', 'Café', 'Restaurant', 'Bar'],
        'ville': ['Montréal', 'Montréal', 'Québec', 'Montréal'],
        'description': ['Température inadéquate', 'Contamination', 'Équipement défaillant', 'Normes non respectées']
    }
    
    if SKLEARN_AVAILABLE:
        import pandas as pd
        df = pd.DataFrame(test_data)
        
        encoder = CategoricalEncoder(df)
        encoded_df = encoder.encode_mapaq_specific_variables()
        
        print(f"✅ Encoding test completed: {df.shape} → {encoded_df.shape}")
        
        report = encoder.get_encoding_report()
        print(f"📊 Variables encoded: {report['encoding_summary']['total_variables_encoded']}")
    else:
        print("✅ Structure test completed - encoder class available")
    
    print("🎉 CategoricalEncoder ready for use!")
