
import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import configuration centralisée
from config import DataSources, ModelConfig, LoggingConfig

# Configuration du logging
logger = logging.getLogger(__name__)


class DataCleaner:
    def __init__(self, raw_data: pd.DataFrame):
        """
        Initialize DataCleaner with raw dataset.
        
        Args:
            raw_data (pd.DataFrame): Raw dataset from DataIngestor
        """
        self.raw_data = raw_data.copy()
        self.clean_data = None
        self.cleaning_stats = {
            'original_shape': raw_data.shape,
            'null_handling': {},
            'format_changes': {},
            'encoding_changes': {},
            'final_shape': None,
            'cleaning_steps': []
        }
        
        logger.info(f"DataCleaner initialized with {raw_data.shape[0]} records, {raw_data.shape[1]} columns")

    def _ensure_clean_data(self) -> None:
        """
        Ensure that `self.clean_data` is initialised.

        Some unit tests call cleaning methods directly on a new instance
        without running `clean_pipeline()` first, so we lazily create
        the working copy of the raw data here.
        """
        if self.clean_data is None:
            self.clean_data = self.raw_data.copy()


    def clean_pipeline(self) -> pd.DataFrame:
        """
        Execute complete cleaning pipeline.
        
        Returns:
            pd.DataFrame: Fully cleaned dataset
        """
        logger.info("Starting complete data cleaning pipeline...")
        
        # Copier les données pour le nettoyage
        self.clean_data = self.raw_data.copy()
        
        # Pipeline de nettoyage
        self._standardize_column_names()
        self.remove_nulls()
        self.unify_formats()
        self.encode_categoricals()
        self._validate_cleaned_data()
        
        # Statistiques finales
        self.cleaning_stats['final_shape'] = self.clean_data.shape
        
        logger.info(f"Cleaning pipeline completed: {self.cleaning_stats['original_shape']} → {self.cleaning_stats['final_shape']}")
        
        return self.clean_data

    def remove_nulls(self, strategy: str = 'smart') -> pd.DataFrame:
        """
        Remove or handle null values intelligently.

        Args:
            strategy (str): 'drop', 'fill', 'smart' (default)

        Returns:
            pd.DataFrame: Dataset with nulls handled
        """
        logger.info(f"Handling null values with strategy: {strategy}")

        # Muy importante para los tests:
        # siempre reiniciar desde los datos originales para que
        # llamadas sucesivas (drop, luego fill) sean comparables.
        self.clean_data = self.raw_data.copy()

        # Analizar nulls antes del limpieza
        null_analysis = self._analyze_nulls()
        self.cleaning_stats['null_handling']['before'] = null_analysis

        if strategy == 'smart':
            self._smart_null_handling()
        elif strategy == 'drop':
            self._drop_null_handling()
        elif strategy == 'fill':
            self._fill_null_handling()
        else:
            raise ValueError(f"Unknown null handling strategy: {strategy}")

        # Analizar después del limpieza
        null_analysis_after = self._analyze_nulls()
        self.cleaning_stats['null_handling']['after'] = null_analysis_after

        self.cleaning_stats['cleaning_steps'].append('null_handling')
        logger.info("Null handling completed")

        return self.clean_data

    def unify_formats(self) -> pd.DataFrame:
        """
        Standardize column formats, dates, numeric types.
        
        Returns:
            pd.DataFrame: Dataset with unified formats
        """
        logger.info("Unifying data formats...")

        # Ensure data is initialised
        self._ensure_clean_data()

        format_changes = {}
        
        # Normaliser les dates
        date_columns = self._identify_date_columns()
        for col in date_columns:
            original_type = str(self.clean_data[col].dtype)
            self.clean_data[col] = self._standardize_dates(self.clean_data[col])
            format_changes[col] = {'from': original_type, 'to': 'datetime64[ns]', 'type': 'date'}
        
        # Normaliser les montants
        if 'montant' in self.clean_data.columns:
            original_type = str(self.clean_data['montant'].dtype)
            self.clean_data['montant'] = self._standardize_amounts(self.clean_data['montant'])
            format_changes['montant'] = {'from': original_type, 'to': 'float64', 'type': 'numeric'}
        
        # Normaliser les textes
        text_columns = self._identify_text_columns()
        for col in text_columns:
            self.clean_data[col] = self._standardize_text(self.clean_data[col])
            format_changes[col] = {'from': 'object', 'to': 'object', 'type': 'text_normalized'}
        
        # Normaliser les IDs
        id_columns = self._identify_id_columns()
        for col in id_columns:
            original_type = str(self.clean_data[col].dtype)
            self.clean_data[col] = self._standardize_ids(self.clean_data[col])
            format_changes[col] = {'from': original_type, 'to': 'int64', 'type': 'id'}
        
        self.cleaning_stats['format_changes'] = format_changes
        self.cleaning_stats['cleaning_steps'].append('format_unification')
        
        logger.info(f"Format unification completed: {len(format_changes)} columns modified")
        return self.clean_data
    
    def encode_categoricals(self) -> pd.DataFrame:
        """
        Encode categorical variables into numeric format.
        
        Returns:
            pd.DataFrame: Dataset with encoded categoricals
        """
        logger.info("Encoding categorical variables...")

        # Ensure data is initialised
        self._ensure_clean_data()

        encoding_changes = {}
        
        # Encoder le statut (ordinal encoding)
        if 'statut' in self.clean_data.columns:
            status_mapping = {
                'Ouvert': 1,
                'Fermé': 0,
                'Fermé changement d\'exploitant': 0,
                'Sous inspection fédérale': 2
            }
            self.clean_data['statut_encoded'] = self.clean_data['statut'].map(status_mapping)
            encoding_changes['statut'] = {'type': 'ordinal', 'mapping': status_mapping}
        
        # Encoder les catégories (one-hot encoding)
        if 'categorie' in self.clean_data.columns:
            category_dummies = pd.get_dummies(self.clean_data['categorie'], prefix='cat')
            self.clean_data = pd.concat([self.clean_data, category_dummies], axis=1)
            encoding_changes['categorie'] = {'type': 'one_hot', 'columns': list(category_dummies.columns)}
        
        # Encoder les villes (label encoding pour les plus fréquentes)
        if 'ville' in self.clean_data.columns:
            ville_encoding = self._encode_ville_column()
            encoding_changes['ville'] = ville_encoding
        
        # Créer des variables dérivées
        self._create_derived_variables()
        encoding_changes['derived_variables'] = self._get_derived_variables_info()
        
        self.cleaning_stats['encoding_changes'] = encoding_changes
        self.cleaning_stats['cleaning_steps'].append('categorical_encoding')
        
        logger.info(f"Categorical encoding completed: {len(encoding_changes)} transformations")
        return self.clean_data
    
    def get_clean_data(self) -> pd.DataFrame:
        """
        Return cleaned dataset.
        
        Returns:
            pd.DataFrame: Cleaned dataset
        """
        if self.clean_data is None:
            logger.warning("No cleaned data available. Running cleaning pipeline...")
            return self.clean_pipeline()
        
        return self.clean_data
    
    def get_cleaning_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive cleaning report.
        
        Returns:
            dict: Detailed cleaning statistics and changes
        """
        return {
            'cleaning_stats': self.cleaning_stats,
            'data_quality': self._assess_data_quality(),
            'column_analysis': self._analyze_columns(),
            'recommendations': self._generate_recommendations()
        }
    
    # ========== PRIVATE METHODS ==========
    
    def _standardize_column_names(self):
        """Standardize column names to lowercase with underscores."""
        original_columns = list(self.clean_data.columns)
        
        # Mapping des colonnes MAPAQ vers noms standardisés
        column_mapping = {
            'id_poursuite': 'pursuit_id',
            'business_id': 'business_id',
            'date': 'infraction_date',
            'date_jugement': 'judgment_date',
            'description': 'description',
            'etablissement': 'establishment_name',
            'montant': 'fine_amount',
            'proprietaire': 'owner_name',
            'ville': 'city',
            'statut': 'status',
            'date_statut': 'status_date',
            'categorie': 'category'
        }
        
        # Appliquer le mapping si les colonnes existent
        columns_to_rename = {}
        for old_name, new_name in column_mapping.items():
            if old_name in self.clean_data.columns:
                columns_to_rename[old_name] = new_name
        
        if columns_to_rename:
            self.clean_data.rename(columns=columns_to_rename, inplace=True)
            logger.info(f"Standardized {len(columns_to_rename)} column names")
    
    def _analyze_nulls(self) -> Dict[str, Any]:
        """Analyze null values in the dataset."""
        self._ensure_clean_data()
        null_counts = self.clean_data.isnull().sum()
        total_rows = len(self.clean_data)
        
        return {
            'total_nulls': null_counts.sum(),
            'null_percentage': (null_counts.sum() / (total_rows * len(self.clean_data.columns))) * 100,
            'columns_with_nulls': null_counts[null_counts > 0].to_dict(),
            'null_percentages_by_column': ((null_counts / total_rows) * 100).to_dict()
        }

    def _smart_null_handling(self):
        """Smart null handling based on column type and null percentage."""
        # Always work on an initialised DataFrame
        self._ensure_clean_data()

        # Use a copy of the column list, as we may drop some
        for column in list(self.clean_data.columns):
            null_count = self.clean_data[column].isnull().sum()
            null_percentage = (null_count / len(self.clean_data)) * 100

            if null_percentage == 0:
                continue

            # Drop columns with >50% nulls
            if null_percentage > 50:
                logger.warning(f"Dropping column {column} (>{null_percentage:.1f}% nulls)")
                self.clean_data.drop(columns=[column], inplace=True)
                continue

            # Monetary / amount-like columns
            if column in ["fine_amount", "montant"]:
                # Be robust to values like "300$" or "invalid"
                numeric_series = pd.to_numeric(self.clean_data[column], errors="coerce")
                median_value = numeric_series.median()
                self.clean_data[column] = numeric_series.fillna(median_value)
                continue

            # Date-like columns
            if "date" in column.lower():
                # Forward fill dates
                self.clean_data[column] = self.clean_data[column].ffill()
                continue

            # Text / categorical columns
            if self.clean_data[column].dtype == "object":
                self.clean_data[column] = self.clean_data[column].fillna("Unknown")
            else:
                # Generic numeric columns – also robust to mixed types
                numeric_series = pd.to_numeric(self.clean_data[column], errors="coerce")
                median_value = numeric_series.median()
                self.clean_data[column] = numeric_series.fillna(median_value)

    def _drop_null_handling(self):
        """Drop all rows with any null values."""
        original_rows = len(self.clean_data)
        self.clean_data.dropna(inplace=True)
        dropped_rows = original_rows - len(self.clean_data)
        logger.info(f"Dropped {dropped_rows} rows with null values")

    def _fill_null_handling(self):
        """Fill all null values with appropriate defaults."""
        for column in self.clean_data.columns:
            if self.clean_data[column].dtype in ['int64', 'float64']:
                self.clean_data[column].fillna(self.clean_data[column].median(), inplace=True)
            else:
                self.clean_data[column].fillna('Unknown', inplace=True)

    def _identify_date_columns(self) -> List[str]:
        """Identify columns that contain dates."""
        date_keywords = ['date', 'time', 'timestamp']
        return [col for col in self.clean_data.columns 
                if any(keyword in col.lower() for keyword in date_keywords)]
    
    def _identify_text_columns(self) -> List[str]:
        """Identify text columns that need normalization."""
        text_columns = []
        for col in self.clean_data.columns:
            if self.clean_data[col].dtype == 'object':
                # Check if it's likely text (not categorical with few unique values)
                unique_ratio = self.clean_data[col].nunique() / len(self.clean_data)
                if unique_ratio > 0.1:  # More than 10% unique values
                    text_columns.append(col)
        return text_columns
    
    def _identify_id_columns(self) -> List[str]:
        """Identify ID columns."""
        id_keywords = ['id', 'pursuit', 'business']
        return [col for col in self.clean_data.columns 
                if any(keyword in col.lower() for keyword in id_keywords)]
    
    def _standardize_dates(self, series: pd.Series) -> pd.Series:
        """Standardize date formats."""
        try:
            return pd.to_datetime(series, errors='coerce')
        except Exception as e:
            logger.warning(f"Error standardizing dates: {e}")
            return series
    
    def _standardize_amounts(self, series: pd.Series) -> pd.Series:
        """Standardize monetary amounts."""
        try:
            # Remove currency symbols and convert to float
            if series.dtype == 'object':
                cleaned = series.astype(str).str.replace(r'[^\d.]', '', regex=True)
                return pd.to_numeric(cleaned, errors='coerce')
            return pd.to_numeric(series, errors='coerce')
        except Exception as e:
            logger.warning(f"Error standardizing amounts: {e}")
            return series
    
    def _standardize_text(self, series: pd.Series) -> pd.Series:
        """Standardize text fields."""
        try:
            return series.astype(str).str.strip().str.title()
        except Exception as e:
            logger.warning(f"Error standardizing text: {e}")
            return series
    
    def _standardize_ids(self, series: pd.Series) -> pd.Series:
        """Standardize ID fields."""
        try:
            return pd.to_numeric(series, errors='coerce').astype('Int64')
        except Exception as e:
            logger.warning(f"Error standardizing IDs: {e}")
            return series
    
    def _encode_ville_column(self) -> Dict[str, Any]:
        """Encode ville column with label encoding."""
        if 'ville' not in self.clean_data.columns and 'city' not in self.clean_data.columns:
            return {}
        
        ville_col = 'city' if 'city' in self.clean_data.columns else 'ville'
        
        # Get top cities and encode others as 'Other'
        top_cities = self.clean_data[ville_col].value_counts().head(10).index.tolist()
        
        def encode_city(city):
            return city if city in top_cities else 'Other'
        
        self.clean_data[f'{ville_col}_encoded'] = self.clean_data[ville_col].apply(encode_city)
        
        # Create dummy variables for top cities
        city_dummies = pd.get_dummies(self.clean_data[f'{ville_col}_encoded'], prefix='city')
        self.clean_data = pd.concat([self.clean_data, city_dummies], axis=1)
        
        return {
            'type': 'label_encoding_with_dummies',
            'top_cities': top_cities,
            'dummy_columns': list(city_dummies.columns)
        }
    
    def _create_derived_variables(self):
        """Create derived variables for ML models."""
        # Age of infraction (days from today)
        if 'infraction_date' in self.clean_data.columns:
            self.clean_data['infraction_age_days'] = (
                datetime.now() - pd.to_datetime(self.clean_data['infraction_date'])
            ).dt.days
        
        # Time between infraction and judgment
        if 'infraction_date' in self.clean_data.columns and 'judgment_date' in self.clean_data.columns:
            self.clean_data['judgment_delay_days'] = (
                pd.to_datetime(self.clean_data['judgment_date']) - 
                pd.to_datetime(self.clean_data['infraction_date'])
            ).dt.days
        
        # Fine amount categories
        if 'fine_amount' in self.clean_data.columns:
            self.clean_data['fine_category'] = pd.cut(
                self.clean_data['fine_amount'], 
                bins=[0, 300, 600, 1000, float('inf')], 
                labels=['Low', 'Medium', 'High', 'Very_High']
            )
        
        # Text length features
        if 'description' in self.clean_data.columns:
            self.clean_data['description_length'] = self.clean_data['description'].astype(str).str.len()
            self.clean_data['description_word_count'] = self.clean_data['description'].astype(str).str.split().str.len()
    
    def _get_derived_variables_info(self) -> Dict[str, str]:
        """Get information about derived variables."""
        derived_vars = {}
        
        if 'infraction_age_days' in self.clean_data.columns:
            derived_vars['infraction_age_days'] = 'Days since infraction occurred'
        if 'judgment_delay_days' in self.clean_data.columns:
            derived_vars['judgment_delay_days'] = 'Days between infraction and judgment'
        if 'fine_category' in self.clean_data.columns:
            derived_vars['fine_category'] = 'Categorical fine amount (Low/Medium/High/Very_High)'
        if 'description_length' in self.clean_data.columns:
            derived_vars['description_length'] = 'Character count of infraction description'
        if 'description_word_count' in self.clean_data.columns:
            derived_vars['description_word_count'] = 'Word count of infraction description'
        
        return derived_vars
    
    def _validate_cleaned_data(self):
        """Validate the cleaned dataset."""
        issues = []
        
        # Check for remaining nulls in critical columns
        critical_columns = ['business_id', 'infraction_date', 'fine_amount']
        for col in critical_columns:
            if col in self.clean_data.columns and self.clean_data[col].isnull().any():
                issues.append(f"Critical column {col} still has null values")
        
        # Check data types
        if 'fine_amount' in self.clean_data.columns and not pd.api.types.is_numeric_dtype(self.clean_data['fine_amount']):
            issues.append("fine_amount is not numeric")
        
        # Check for duplicate records
        duplicates = self.clean_data.duplicated().sum()
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate records found")
        
        if issues:
            logger.warning(f"Data validation issues: {issues}")
        else:
            logger.info("Data validation passed successfully")
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality."""
        return {
            'completeness': (1 - self.clean_data.isnull().sum().sum() / self.clean_data.size) * 100,
            'consistency': self._check_consistency(),
            'validity': self._check_validity(),
            'uniqueness': (1 - self.clean_data.duplicated().sum() / len(self.clean_data)) * 100
        }
    
    def _check_consistency(self) -> float:
        """Check data consistency."""
        consistency_score = 100.0
        
        # Check date consistency
        if 'infraction_date' in self.clean_data.columns and 'judgment_date' in self.clean_data.columns:
            invalid_dates = (
                pd.to_datetime(self.clean_data['judgment_date']) < 
                pd.to_datetime(self.clean_data['infraction_date'])
            ).sum()
            consistency_score -= (invalid_dates / len(self.clean_data)) * 20
        
        return max(0, consistency_score)
    
    def _check_validity(self) -> float:
        """Check data validity."""
        validity_score = 100.0
        
        # Check fine amounts are positive
        if 'fine_amount' in self.clean_data.columns:
            negative_fines = (self.clean_data['fine_amount'] < 0).sum()
            validity_score -= (negative_fines / len(self.clean_data)) * 30
        
        return max(0, validity_score)
    
    def _analyze_columns(self) -> Dict[str, Dict]:
        """Analyze each column in detail."""
        analysis = {}
        
        for col in self.clean_data.columns:
            analysis[col] = {
                'dtype': str(self.clean_data[col].dtype),
                'null_count': self.clean_data[col].isnull().sum(),
                'unique_count': self.clean_data[col].nunique(),
                'memory_usage': self.clean_data[col].memory_usage(deep=True)
            }
            
            if pd.api.types.is_numeric_dtype(self.clean_data[col]):
                analysis[col].update({
                    'min': self.clean_data[col].min(),
                    'max': self.clean_data[col].max(),
                    'mean': self.clean_data[col].mean(),
                    'std': self.clean_data[col].std()
                })
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for further data improvement."""
        recommendations = []
        
        # Check for high cardinality categorical variables
        for col in self.clean_data.columns:
            if self.clean_data[col].dtype == 'object':
                unique_ratio = self.clean_data[col].nunique() / len(self.clean_data)
                if unique_ratio > 0.8:
                    recommendations.append(f"Consider feature engineering for high-cardinality column: {col}")
        
        # Check for skewed numeric variables
        numeric_columns = self.clean_data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if abs(self.clean_data[col].skew()) > 2:
                recommendations.append(f"Consider log transformation for skewed column: {col}")
        
        return recommendations
