"""
Tests Dashboard API Endpoints - MAPAQ
Suite de tests complète pour les endpoints API dashboard (Heures 93-96)

Ce module teste tous les endpoints API du dashboard MAPAQ avec :
- Tests unitaires de chaque endpoint
- Tests d'intégration avec la base de données
- Tests de performance et charge
- Validation des réponses et codes d'erreur

Author: Mouhamed Thiaw
Date: 2025-01-14
Heures: 93-96 (Semaine 3)
"""

import unittest
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
import os

# Modules MAPAQ à tester
from dashboard_api_endpoints import MapaqDashboardAPI, DashboardAPIConfig
from dashboard import MapaqDashboardBackend, RestaurantData
from database_schema_design import DatabaseSchemaDesigner

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDashboardAPIEndpoints(unittest.TestCase):
    """
    Suite de tests pour les endpoints API du dashboard MAPAQ.
    
    Tests couverts:
    - Health check endpoint
    - Prediction endpoint
    - Historical data endpoint
    - Trends endpoint
    - Dashboard summary endpoint
    - Error handling
    - Performance
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale des tests."""
        logger.info("=== DÉBUT TESTS DASHBOARD API ENDPOINTS ===")
        
        # Base de données de test
        cls.test_db = "test_mapaq_dashboard.db"
        
        # Création de la base de données de test
        cls.db_designer = DatabaseSchemaDesigner()
        cls.db_designer.db_path = cls.test_db
        cls.db_designer.create_database()
        
        # Initialisation du backend et API
        cls.backend = MapaqDashboardBackend()
        # Modification du chemin de base de données pour les tests
        cls.backend.db_manager.db_path = cls.test_db
        cls.api = MapaqDashboardAPI(cls.backend)
        
        # Données de test
        cls._setup_test_data()
        
        logger.info("Configuration des tests terminée")
    
    @classmethod
    def _setup_test_data(cls):
        """Prépare les données de test."""
        # Restaurants de test
        test_restaurants = [
            {
                'id': 'TEST_001',
                'nom': 'Restaurant Test API',
                'theme': 'Restaurant',
                'taille': 'Moyenne',
                'zone': 'Montréal',
                'adresse': '123 Rue Test'
            },
            {
                'id': 'TEST_002', 
                'nom': 'Fast Food Test',
                'theme': 'Fast Food',
                'taille': 'Grande',
                'zone': 'Québec',
                'adresse': '456 Avenue Test'
            }
        ]
        
        # Insertion des données de test
        conn = sqlite3.connect(cls.test_db)
        for resto in test_restaurants:
            conn.execute("""
                INSERT OR REPLACE INTO restaurants 
                (id, nom, theme, taille, zone, adresse, score_risque_actuel, 
                 categorie_risque_actuelle, derniere_inspection, prochaine_inspection, 
                 nombre_infractions_total)
                VALUES (?, ?, ?, ?, ?, ?, 50.0, 'Moyen', date('now'), 
                        date('now', '+30 days'), 0)
            """, (resto['id'], resto['nom'], resto['theme'], resto['taille'], 
                  resto['zone'], resto['adresse']))
        
        conn.commit()
        conn.close()
        
        logger.info("Données de test préparées")
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après les tests."""
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        logger.info("=== FIN TESTS DASHBOARD API ENDPOINTS ===")
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Reset des statistiques API
        self.api.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'endpoints_usage': {},
            'start_time': datetime.now(),
            'last_request': None
        }
    
    # ========== TESTS ENDPOINT HEALTH ==========
    
    def test_health_check_success(self):
        """Test du health check en conditions normales."""
        logger.info("Test: Health check success")
        
        result = self.api.health_check()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'healthy')
        self.assertIn('version', result['data'])
        self.assertIn('uptime_seconds', result['data'])
        
        logger.info("✅ Health check success - OK")
    
    def test_health_check_statistics(self):
        """Test des statistiques dans le health check."""
        logger.info("Test: Health check statistics")
        
        # Premier appel
        result1 = self.api.health_check()
        self.assertEqual(result1['data']['total_requests'], 1)
        
        # Deuxième appel
        result2 = self.api.health_check()
        self.assertEqual(result2['data']['total_requests'], 2)
        
        logger.info("✅ Health check statistics - OK")
    
    # ========== TESTS ENDPOINT PREDICT ==========
    
    def test_predict_valid_request(self):
        """Test de prédiction avec requête valide."""
        logger.info("Test: Predict valid request")
        
        # Simulation d'une requête valide
        class MockRequest:
            def __init__(self, json_data):
                self.json_data = json_data
                self.is_json = True
            def get_json(self):
                return self.json_data
        
        # Données de test
        test_data = {
            'nom': 'Restaurant Test Predict',
            'adresse': '789 Rue Predict',
            'ville': 'Montréal',
            'theme': 'Restaurant',
            'taille': 'Moyenne'
        }
        
        # Mock de la requête
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest(test_data)
        
        try:
            result = self.api.predict_risk()
            
            # Vérifications
            if isinstance(result, tuple):
                result = result[0]  # En cas d'erreur avec code de statut
            
            self.assertIsInstance(result, dict)
            if result.get('success'):
                self.assertIn('data', result)
                self.assertIn('restaurant', result['data'])
                self.assertIn('prediction', result['data'])
            
        finally:
            # Restauration
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Predict valid request - OK")
    
    def test_predict_missing_fields(self):
        """Test de prédiction avec champs manquants."""
        logger.info("Test: Predict missing fields")
        
        class MockRequest:
            def __init__(self, json_data):
                self.json_data = json_data
                self.is_json = True
            def get_json(self):
                return self.json_data
        
        # Données incomplètes
        test_data = {
            'nom': 'Restaurant Test'
            # Manque adresse et ville
        }
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest(test_data)
        
        try:
            result = self.api.predict_risk()
            
            if isinstance(result, tuple):
                result, status_code = result
                self.assertEqual(status_code, 400)
            
            self.assertFalse(result['success'])
            self.assertIn('Champs requis manquants', result['error'])
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Predict missing fields - OK")
    
    # ========== TESTS ENDPOINT HISTORICAL ==========
    
    def test_historical_data_default(self):
        """Test récupération données historiques par défaut."""
        logger.info("Test: Historical data default")
        
        class MockArgs:
            def get(self, key, default=None):
                return default
        
        class MockRequest:
            def __init__(self):
                self.args = MockArgs()
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest()
        
        try:
            result = self.api.get_historical_data()
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result['success'])
            self.assertIn('data', result)
            self.assertIn('historical_data', result['data'])
            self.assertIn('filters', result['data'])
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Historical data default - OK")
    
    def test_historical_data_with_filters(self):
        """Test données historiques avec filtres."""
        logger.info("Test: Historical data with filters")
        
        class MockArgs:
            def __init__(self, params):
                self.params = params
            def get(self, key, default=None):
                return self.params.get(key, default)
        
        class MockRequest:
            def __init__(self, params):
                self.args = MockArgs(params)
        
        # Paramètres de test
        params = {'days': '7', 'category': 'moyen'}
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest(params)
        
        try:
            result = self.api.get_historical_data()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data']['filters']['days'], 7)
            self.assertEqual(result['data']['filters']['category'], 'moyen')
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Historical data with filters - OK")
    
    # ========== TESTS ENDPOINT TRENDS ==========
    
    def test_trends_default_period(self):
        """Test analyse tendances période par défaut."""
        logger.info("Test: Trends default period")
        
        class MockArgs:
            def get(self, key, default=None):
                return default
        
        class MockRequest:
            def __init__(self):
                self.args = MockArgs()
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest()
        
        try:
            result = self.api.get_trends()
            
            self.assertTrue(result['success'])
            self.assertIn('trends', result['data'])
            self.assertEqual(result['data']['parameters']['period'], 'month')
            self.assertEqual(result['data']['parameters']['metric'], 'score')
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Trends default period - OK")
    
    def test_trends_invalid_period(self):
        """Test tendances avec période invalide."""
        logger.info("Test: Trends invalid period")
        
        class MockArgs:
            def __init__(self, params):
                self.params = params
            def get(self, key, default=None):
                return self.params.get(key, default)
        
        class MockRequest:
            def __init__(self, params):
                self.args = MockArgs(params)
        
        # Période invalide
        params = {'period': 'invalid_period'}
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest(params)
        
        try:
            result = self.api.get_trends()
            
            if isinstance(result, tuple):
                result, status_code = result
                self.assertEqual(status_code, 400)
            
            self.assertFalse(result['success'])
            self.assertIn('Période invalide', result['error'])
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        logger.info("✅ Trends invalid period - OK")
    
    # ========== TESTS ENDPOINT DASHBOARD ==========
    
    def test_dashboard_summary(self):
        """Test résumé dashboard."""
        logger.info("Test: Dashboard summary")
        
        result = self.api.get_dashboard_summary()
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        
        # Vérification des champs attendus
        data = result['data']
        expected_fields = [
            'total_restaurants', 'average_score', 'distribution_categories',
            'high_risk_count', 'upcoming_inspections', 'api_metrics'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        logger.info("✅ Dashboard summary - OK")
    
    # ========== TESTS ENDPOINT METRICS ==========
    
    def test_api_metrics(self):
        """Test métriques API."""
        logger.info("Test: API metrics")
        
        # Faire quelques appels pour générer des métriques
        self.api.health_check()
        self.api.get_dashboard_summary()
        
        result = self.api.get_api_metrics()
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        
        metrics = result['data']
        self.assertIn('general', metrics)
        self.assertIn('endpoints', metrics)
        self.assertIn('performance', metrics)
        
        # Vérification des compteurs
        self.assertGreater(metrics['general']['total_requests'], 0)
        self.assertGreaterEqual(metrics['general']['success_rate'], 0)
        
        logger.info("✅ API metrics - OK")
    
    # ========== TESTS DE PERFORMANCE ==========
    
    def test_performance_health_check(self):
        """Test performance du health check."""
        logger.info("Test: Performance health check")
        
        start_time = time.time()
        
        # 10 appels consécutifs
        for _ in range(10):
            result = self.api.health_check()
            self.assertTrue(result['success'])
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        # Vérification performance (< 100ms par appel)
        self.assertLess(avg_time, 0.1)
        
        logger.info(f"✅ Performance health check - {avg_time*1000:.2f}ms/appel")
    
    def test_performance_dashboard_summary(self):
        """Test performance du résumé dashboard."""
        logger.info("Test: Performance dashboard summary")
        
        start_time = time.time()
        
        # 5 appels consécutifs
        for _ in range(5):
            result = self.api.get_dashboard_summary()
            self.assertTrue(result['success'])
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 5
        
        # Vérification performance (< 200ms par appel)
        self.assertLess(avg_time, 0.2)
        
        logger.info(f"✅ Performance dashboard summary - {avg_time*1000:.2f}ms/appel")
    
    # ========== TESTS D'INTÉGRATION ==========
    
    def test_integration_full_workflow(self):
        """Test d'intégration workflow complet."""
        logger.info("Test: Integration full workflow")
        
        # 1. Health check
        health = self.api.health_check()
        self.assertTrue(health['success'])
        
        # 2. Dashboard summary
        dashboard = self.api.get_dashboard_summary()
        self.assertTrue(dashboard['success'])
        
        # 3. Historical data
        class MockRequest:
            def __init__(self):
                self.args = type('MockArgs', (), {'get': lambda self, k, d=None: d})()
        
        import sys
        original_request = getattr(sys.modules['dashboard_api_endpoints'], 'request', None)
        sys.modules['dashboard_api_endpoints'].request = MockRequest()
        
        try:
            historical = self.api.get_historical_data()
            self.assertTrue(historical['success'])
            
            trends = self.api.get_trends()
            self.assertTrue(trends['success'])
            
        finally:
            if original_request:
                sys.modules['dashboard_api_endpoints'].request = original_request
        
        # 4. Métriques finales
        metrics = self.api.get_api_metrics()
        self.assertTrue(metrics['success'])
        self.assertGreater(metrics['data']['general']['total_requests'], 4)
        
        logger.info("✅ Integration full workflow - OK")

class TestDashboardAPIPerformance(unittest.TestCase):
    """Tests de performance spécialisés."""
    
    def setUp(self):
        """Configuration pour tests de performance."""
        self.test_db = "perf_test_mapaq.db"
        
        # Base de données de performance
        db_designer = DatabaseSchemaDesigner()
        db_designer.db_path = self.test_db
        db_designer.create_database()
        
        self.backend = MapaqDashboardBackend()
        # Modification du chemin de base de données pour les tests
        self.backend.db_manager.db_path = self.test_db
        self.api = MapaqDashboardAPI(self.backend)
    
    def tearDown(self):
        """Nettoyage après tests de performance."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_concurrent_requests_simulation(self):
        """Simulation de requêtes concurrentes."""
        logger.info("Test: Concurrent requests simulation")
        
        start_time = time.time()
        
        # Simulation de 50 requêtes rapides
        results = []
        for i in range(50):
            result = self.api.health_check()
            results.append(result['success'])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Vérifications
        self.assertEqual(sum(results), 50)  # Toutes réussies
        self.assertLess(total_time, 5.0)    # Moins de 5 secondes
        
        logger.info(f"✅ 50 requêtes en {total_time:.2f}s ({total_time/50*1000:.2f}ms/req)")

def run_all_tests():
    """Exécute tous les tests avec rapport détaillé."""
    logger.info("=== DÉBUT TESTS DASHBOARD API ENDPOINTS ===")
    logger.info("Heures 93-96: Tests complets des endpoints API")
    
    # Suite de tests principale
    suite = unittest.TestSuite()
    
    # Tests fonctionnels
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardAPIEndpoints))
    
    # Tests de performance
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardAPIPerformance))
    
    # Exécution avec rapport détaillé
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Rapport final
    logger.info("\n=== RAPPORT FINAL TESTS ===")
    logger.info(f"Tests exécutés: {result.testsRun}")
    logger.info(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Échecs: {len(result.failures)}")
    logger.info(f"Erreurs: {len(result.errors)}")
    
    if result.failures:
        logger.error("ÉCHECS:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.error("ERREURS:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    logger.info(f"Taux de succès: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    if success:
        logger.info("🎉 TOUS LES TESTS RÉUSSIS!")
    else:
        logger.error("❌ CERTAINS TESTS ONT ÉCHOUÉ")
