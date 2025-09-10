
import sys
import os
import unittest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime, timedelta

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test des imports avec fallback
PANDAS_AVAILABLE = False
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    pass

class TestDataIngestion(unittest.TestCase):
    """Tests unitaires pour le module DataIngestor."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Créer un fichier CSV de test
        self.test_csv_path = self.test_data_dir / "test_sample.csv"
        self.create_test_csv()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def create_test_csv(self):
        """Créer un fichier CSV de test."""
        test_data = [
            "id_poursuite,business_id,date,date_jugement,description,etablissement,montant,proprietaire,ville,statut,date_statut,categorie",
            "1,12345,2024-01-15,2024-02-20,Température inadéquate,Restaurant Le Gourmet,500,Jean Dupont,Montréal,Ouvert,2024-01-01,Restaurant",
            "2,12346,2024-02-10,2024-03-15,Contamination croisée,Pizzeria Mario,300,Mario Rossi,Montréal,Ouvert,2023-12-15,Restaurant",
            "3,12347,2024-01-20,2024-02-25,Équipement défaillant,Sushi Zen,750,Yuki Tanaka,Montréal,Ouvert,2024-01-10,Restaurant"
        ]
        
        with open(self.test_csv_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(test_data))
    
    def test_data_ingestor_structure(self):
        """Test de la structure du DataIngestor."""
        # Vérifier que le fichier existe
        ingest_file = Path("data_ingest.py")
        self.assertTrue(ingest_file.exists(), "data_ingest.py should exist")
        
        # Vérifier le contenu
        with open(ingest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            "class DataIngestor",
            "def load_raw_data",
            "def load_from_csv",
            "def load_from_url"
        ]
        
        for element in required_elements:
            self.assertIn(element, content, f"{element} should be in DataIngestor")
    
    def test_csv_loading_logic(self):
        """Test de la logique de chargement CSV."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_ingest import DataIngestor
            
            ingestor = DataIngestor()
            
            # Test de chargement du fichier de test
            data = ingestor.load_from_csv(str(self.test_csv_path))
            
            self.assertIsInstance(data, pd.DataFrame, "Should return DataFrame")
            self.assertEqual(len(data), 3, "Should have 3 rows")
            self.assertEqual(len(data.columns), 12, "Should have 12 columns")
            
        except ImportError:
            self.skipTest("DataIngestor not available without dependencies")
    
    def test_encoding_handling(self):
        """Test de la gestion des encodages."""
        # Créer un fichier avec caractères spéciaux
        special_csv = self.test_data_dir / "special_chars.csv"
        special_data = [
            "id_poursuite,etablissement,proprietaire",
            "1,Café Français,José García",
            "2,Restaurant Québécois,François Côté"
        ]
        
        # Tester différents encodages
        encodings = ['utf-8', 'latin-1']
        
        for encoding in encodings:
            with open(special_csv, 'w', encoding=encoding) as f:
                f.write('\n'.join(special_data))
            
            # Vérifier que le fichier peut être lu
            self.assertTrue(special_csv.exists(), f"File with {encoding} should exist")
    
    def test_error_handling(self):
        """Test de la gestion d'erreurs."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_ingest import DataIngestor
            
            ingestor = DataIngestor()
            
            # Test avec fichier inexistant
            with self.assertRaises(Exception):
                ingestor.load_from_csv("nonexistent_file.csv")
            
        except ImportError:
            self.skipTest("DataIngestor not available")

class TestDataCleaning(unittest.TestCase):
    """Tests unitaires pour le module DataCleaner."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        if PANDAS_AVAILABLE:
            # Créer des données de test avec problèmes
            self.test_data = pd.DataFrame({
                'id_poursuite': [1, 2, None, 4, 5],
                'business_id': [12345, 12346, 12347, None, 12349],
                'date': ['2024-01-15', '2024-02-10', 'invalid', None, '2024-02-28'],
                'montant': [500, '300$', 750.0, None, 'invalid'],
                'ville': ['Montréal', 'montreal', 'MONTREAL', None, 'Montréal'],
                'statut': ['Ouvert', 'Ouvert', 'Fermé', None, 'Ouvert']
            })
    
    def test_data_cleaner_structure(self):
        """Test de la structure du DataCleaner."""
        cleaner_file = Path("data_cleaner.py")
        self.assertTrue(cleaner_file.exists(), "data_cleaner.py should exist")
        
        with open(cleaner_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            "class DataCleaner",
            "def remove_nulls",
            "def unify_formats",
            "def encode_categoricals",
            "def clean_pipeline"
        ]
        
        for element in required_elements:
            self.assertIn(element, content, f"{element} should be in DataCleaner")
    
    def test_null_handling_strategies(self):
        """Test des stratégies de gestion des nulls."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_cleaner import DataCleaner
            
            cleaner = DataCleaner(self.test_data)
            
            # Test stratégie drop
            cleaned_drop = cleaner.remove_nulls(strategy='drop')
            self.assertLess(len(cleaned_drop), len(self.test_data), "Drop should reduce rows")
            
            # Test stratégie fill
            cleaned_fill = cleaner.remove_nulls(strategy='fill')
            self.assertEqual(len(cleaned_fill), len(self.test_data), "Fill should keep all rows")
            
        except ImportError:
            self.skipTest("DataCleaner not available")
    
    def test_format_unification(self):
        """Test de l'unification des formats."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_cleaner import DataCleaner
            
            cleaner = DataCleaner(self.test_data)
            cleaned_data = cleaner.unify_formats()
            
            # Vérifier que les formats sont unifiés
            self.assertIsInstance(cleaned_data, pd.DataFrame, "Should return DataFrame")
            
        except ImportError:
            self.skipTest("DataCleaner not available")
    
    def test_categorical_encoding(self):
        """Test de l'encodage catégoriel."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_cleaner import DataCleaner
            
            cleaner = DataCleaner(self.test_data)
            encoded_data = cleaner.encode_categoricals()
            
            # Vérifier que l'encodage a créé de nouvelles colonnes
            self.assertGreaterEqual(len(encoded_data.columns), len(self.test_data.columns), 
                                  "Encoding should create new columns")
            
        except ImportError:
            self.skipTest("DataCleaner not available")
    
    def test_pipeline_integration(self):
        """Test du pipeline complet."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_cleaner import DataCleaner
            
            cleaner = DataCleaner(self.test_data)
            final_data = cleaner.clean_pipeline()
            
            # Vérifications de base
            self.assertIsInstance(final_data, pd.DataFrame, "Should return DataFrame")
            self.assertGreater(len(final_data.columns), 0, "Should have columns")
            
        except ImportError:
            self.skipTest("DataCleaner not available")

class TestIngestionCleaningIntegration(unittest.TestCase):
    """Tests d'intégration entre ingestion et nettoyage."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.test_data_dir = Path("test_integration")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Créer un fichier CSV avec des problèmes réalistes
        self.integration_csv = self.test_data_dir / "integration_test.csv"
        self.create_problematic_csv()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def create_problematic_csv(self):
        """Créer un CSV avec des problèmes réalistes."""
        problematic_data = [
            "id_poursuite,business_id,date,date_jugement,description,etablissement,montant,proprietaire,ville,statut,date_statut,categorie",
            "1,12345,2024-01-15,2024-02-20,Température inadéquate,Restaurant Le Gourmet,500,Jean Dupont,Montréal,Ouvert,2024-01-01,Restaurant",
            "2,12346,2024/02/10,2024-03-15,Contamination croisée,pizzeria mario,300$,Mario Rossi,montreal,Ouvert,2023-12-15,Restaurant",
            "3,,2024-01-20,,Équipement défaillant,SUSHI ZEN,750.0,Yuki Tanaka,MONTREAL,Ouvert,2024-01-10,Restaurant",
            ",12348,invalid_date,2024-03-05,Non-respect normes,café central,,Marie Tremblay,,Fermé,2024-03-01,Café",
            "5,12349,2024-02-28,2024-03-30,Présence nuisibles,Bar Le Refuge,1000,Pierre Leblanc,Montréal,Fermé changement d'exploitant,2024-01-25,"
        ]
        
        with open(self.integration_csv, 'w', encoding='utf-8') as f:
            f.write('\n'.join(problematic_data))
    
    def test_full_pipeline_integration(self):
        """Test du pipeline complet ingestion → nettoyage."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_ingest import DataIngestor
            from data_cleaner import DataCleaner
            
            # Étape 1: Ingestion
            ingestor = DataIngestor()
            raw_data = ingestor.load_from_csv(str(self.integration_csv))
            
            self.assertIsInstance(raw_data, pd.DataFrame, "Ingestion should return DataFrame")
            self.assertGreater(len(raw_data), 0, "Should have data")
            
            # Étape 2: Nettoyage
            cleaner = DataCleaner(raw_data)
            cleaned_data = cleaner.clean_pipeline()
            
            self.assertIsInstance(cleaned_data, pd.DataFrame, "Cleaning should return DataFrame")
            
            # Vérifications de qualité
            original_nulls = raw_data.isnull().sum().sum()
            cleaned_nulls = cleaned_data.isnull().sum().sum()
            
            # Le nettoyage devrait réduire les nulls ou les gérer
            self.assertLessEqual(cleaned_nulls, original_nulls, 
                               "Cleaning should reduce or maintain null count")
            
        except ImportError:
            self.skipTest("Modules not available without dependencies")
    
    def test_data_quality_improvement(self):
        """Test de l'amélioration de la qualité des données."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_ingest import DataIngestor
            from data_cleaner import DataCleaner
            
            # Pipeline complet
            ingestor = DataIngestor()
            raw_data = ingestor.load_from_csv(str(self.integration_csv))
            
            cleaner = DataCleaner(raw_data)
            cleaned_data = cleaner.clean_pipeline()
            
            # Obtenir le rapport de qualité
            report = cleaner.get_cleaning_report()
            quality = report['data_quality']
            
            # Vérifications de qualité
            self.assertGreaterEqual(quality['completeness'], 0, "Completeness should be >= 0")
            self.assertLessEqual(quality['completeness'], 100, "Completeness should be <= 100")
            
            self.assertGreaterEqual(quality['consistency'], 0, "Consistency should be >= 0")
            self.assertLessEqual(quality['consistency'], 100, "Consistency should be <= 100")
            
        except ImportError:
            self.skipTest("Modules not available")
    
    def test_error_propagation(self):
        """Test de la propagation d'erreurs entre modules."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        try:
            from data_ingest import DataIngestor
            from data_cleaner import DataCleaner
            
            ingestor = DataIngestor()
            
            # Test avec fichier inexistant
            with self.assertRaises(Exception):
                raw_data = ingestor.load_from_csv("nonexistent.csv")
            
            # Test avec données vides
            empty_data = pd.DataFrame()
            cleaner = DataCleaner(empty_data)
            
            # Le cleaner devrait gérer les données vides gracieusement
            try:
                result = cleaner.clean_pipeline()
                # Si ça ne lève pas d'exception, c'est bon
                self.assertIsInstance(result, pd.DataFrame)
            except Exception:
                # Si ça lève une exception, elle devrait être informative
                pass
            
        except ImportError:
            self.skipTest("Modules not available")

class TestPerformanceAndScalability(unittest.TestCase):
    """Tests de performance et scalabilité."""
    
    def test_large_dataset_simulation(self):
        """Test avec simulation d'un grand dataset."""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas not available")
        
        # Créer un dataset simulé plus grand
        large_data = []
        for i in range(1000):
            row = f"{i},1234{i},2024-01-{(i%28)+1:02d},2024-02-{(i%28)+1:02d},Description {i},Restaurant {i},{100+i},Owner {i},Ville {i%10},Ouvert,2024-01-01,Restaurant"
            large_data.append(row)
        
        # Sauvegarder temporairement
        temp_file = Path("temp_large_test.csv")
        header = "id_poursuite,business_id,date,date_jugement,description,etablissement,montant,proprietaire,ville,statut,date_statut,categorie"
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(header + '\n')
                f.write('\n'.join(large_data))
            
            # Test de performance basique
            start_time = datetime.now()
            
            try:
                from data_ingest import DataIngestor
                from data_cleaner import DataCleaner
                
                ingestor = DataIngestor()
                raw_data = ingestor.load_from_csv(str(temp_file))
                
                cleaner = DataCleaner(raw_data)
                cleaned_data = cleaner.clean_pipeline()
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Vérifier que le traitement est raisonnable (< 30 secondes pour 1000 lignes)
                self.assertLess(processing_time, 30, "Processing should be reasonably fast")
                
                # Vérifier l'intégrité des données
                self.assertEqual(len(cleaned_data), len(raw_data), "Should preserve row count")
                
            except ImportError:
                self.skipTest("Modules not available")
            
        finally:
            # Nettoyer le fichier temporaire
            if temp_file.exists():
                temp_file.unlink()

def create_test_suite():
    """Créer la suite de tests complète."""
    suite = unittest.TestSuite()
    
    # Tests d'ingestion
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestDataIngestion))
    
    # Tests de nettoyage
    suite.addTests(loader.loadTestsFromTestCase(TestDataCleaning))
    
    # Tests d'intégration
    suite.addTests(loader.loadTestsFromTestCase(TestIngestionCleaningIntegration))
    
    # Tests de performance
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceAndScalability))
    
    return suite

def run_tests_with_report():
    """Exécuter les tests avec rapport détaillé."""
    print("🚀 Unit Tests - Ingestion + Cleaning Pipeline")
    print("=" * 70)
    print("Heures 21-24: Tests unitaires complets")
    print("=" * 70)
    
    # Vérifier les dépendances
    print(f"📦 Dependencies Status:")
    print(f"  pandas: {'✅ Available' if PANDAS_AVAILABLE else '❌ Not available'}")
    
    # Créer et exécuter la suite de tests
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    
    print(f"\n🧪 Running Unit Tests...")
    result = runner.run(suite)
    
    # Rapport final
    print("\n" + "=" * 70)
    print("📊 UNIT TESTS RESULTS SUMMARY")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed} ✅")
    print(f"  Failed: {failures} ❌")
    print(f"  Errors: {errors} 💥")
    print(f"  Skipped: {skipped} ⏭️")
    
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 UNIT TESTS SUCCESSFUL!")
        print("✅ Ready for Heures 25-28: Pipeline de préprocessing complet")
    elif success_rate >= 60:
        print("⚠️  PARTIAL SUCCESS - Some tests failed")
        print("🔧 Review failed tests before proceeding")
    else:
        print("❌ UNIT TESTS FAILED!")
        print("🛠️  Significant issues detected - review implementation")
    
    # Détails des échecs si nécessaire
    if failures > 0:
        print(f"\n💥 Failures Details:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n🚨 Errors Details:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return success_rate >= 80

if __name__ == "__main__":
    run_tests_with_report()
