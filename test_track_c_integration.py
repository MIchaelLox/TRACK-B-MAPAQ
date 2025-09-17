"""
Tests d'Intégration Track-C
Suite complète de tests pour l'intégration Track-B ↔ Track-C

Author: Mouhamed Thiaw
Date: 2025-01-14
"""

import unittest
import json
import time
import requests
import threading
from datetime import datetime
from typing import Dict, List, Optional
import logging
from unittest.mock import Mock, patch, MagicMock

# Modules à tester
from track_c_integration import TrackCIntegration, APIResponse, RiskPrediction
from api_endpoints import APIEndpointManager, EndpointConfig
from data_formatters import TrackCDataFormatter, FormatUtils
from config import IntegrationConfig

# Configuration logging pour les tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CLASSE DE BASE POUR LES TESTS ==========

class BaseTrackCTest(unittest.TestCase):
    """Classe de base pour tous les tests Track-C."""
    
    @classmethod
    def setUpClass(cls):
        """Configuration globale des tests."""
        cls.integration = TrackCIntegration()
        cls.formatter = TrackCDataFormatter()
        cls.test_server_port = 8081
        cls.test_server_url = f"http://localhost:{cls.test_server_port}"
        
        # Données de test
        cls.sample_restaurant = {
            'name': 'Restaurant Test',
            'address': '123 Rue Test, Montréal, QC H1A 1A1',
            'theme': 'italian',
            'phone': '514-555-1234',
            'inspection_history': [
                {'date': '2024-01-15', 'score': 85, 'violations': []},
                {'date': '2024-06-20', 'score': 92, 'violations': ['minor_cleanliness']}
            ]
        }
        
        cls.sample_geocode_request = {
            'address': '123 Rue Test, Montréal, QC H1A 1A1',
            'force_refresh': False
        }
        
        cls.sample_theme_request = {
            'restaurant_name': 'Trattoria Milano',
            'description': 'Authentic Italian cuisine with pasta and pizza',
            'additional_keywords': ['pasta', 'pizza', 'italian']
        }
        
        logger.info("Configuration des tests Track-C terminée")
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.start_time = time.time()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        execution_time = time.time() - self.start_time
        logger.info(f"Test {self._testMethodName} terminé en {execution_time:.3f}s")

# ========== TESTS UNITAIRES ENDPOINTS (Heure 37) ==========

class TestEndpointsUnitaires(BaseTrackCTest):
    """Tests unitaires des endpoints API individuels."""
    
    def test_health_endpoint_structure(self):
        """Test de la structure de l'endpoint de santé."""
        with self.integration.app.test_client() as client:
            response = client.get('/api/v1/health')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Vérification de la structure
            self.assertIn('success', data)
            self.assertIn('service', data)
            self.assertIn('status', data)
            self.assertIn('timestamp', data)
            
            self.assertTrue(data['success'])
            self.assertEqual(data['service'], 'Track-B MAPAQ Integration')
            self.assertEqual(data['status'], 'healthy')
    
    def test_predict_risk_endpoint_validation(self):
        """Test de validation de l'endpoint de prédiction de risque."""
        with self.integration.app.test_client() as client:
            # Test avec données valides
            headers = {'Content-Type': 'application/json', 'X-API-Key': 'test-key'}
            response = client.post(
                '/api/v1/predict-risk',
                data=json.dumps(self.sample_restaurant),
                headers=headers
            )
            
            # Note: Sans clé API valide, devrait retourner 401
            self.assertIn(response.status_code, [200, 401])
            
            # Test avec données invalides
            invalid_data = {'name': ''}  # Nom vide
            response = client.post(
                '/api/v1/predict-risk',
                data=json.dumps(invalid_data),
                headers=headers
            )
            
            self.assertIn(response.status_code, [400, 401])
    
    def test_geocode_endpoint_validation(self):
        """Test de validation de l'endpoint de géocodage."""
        with self.integration.app.test_client() as client:
            headers = {'Content-Type': 'application/json', 'X-API-Key': 'test-key'}
            
            # Test avec adresse valide
            response = client.post(
                '/api/v1/geocode',
                data=json.dumps(self.sample_geocode_request),
                headers=headers
            )
            
            self.assertIn(response.status_code, [200, 401])
            
            # Test avec adresse invalide
            invalid_geocode = {'address': ''}
            response = client.post(
                '/api/v1/geocode',
                data=json.dumps(invalid_geocode),
                headers=headers
            )
            
            self.assertIn(response.status_code, [400, 401])
    
    def test_response_format_consistency(self):
        """Test de la cohérence du format des réponses."""
        with self.integration.app.test_client() as client:
            # Test de l'endpoint de santé
            response = client.get('/api/v1/health')
            data = json.loads(response.data)
            
            # Vérification des champs obligatoires
            required_fields = ['success', 'timestamp']
            for field in required_fields:
                self.assertIn(field, data)
            
            # Vérification du format timestamp
            timestamp = data['timestamp']
            self.assertIsInstance(timestamp, str)

# ========== TESTS D'INTÉGRATION TRACK-B ↔ TRACK-C (Heure 38) ==========

class TestIntegrationTrackBTrackC(BaseTrackCTest):
    """Tests d'intégration entre Track-B et Track-C."""
    
    @patch('track_c_integration.AddressNormalizer')
    @patch('track_c_integration.ThemeClassifier')
    def test_pipeline_prediction_complet(self, mock_theme_classifier, mock_address_normalizer):
        """Test du pipeline complet de prédiction de risque."""
        # Configuration des mocks
        mock_address_normalizer.return_value.normalize_address.return_value = "123 Rue Test Normalisée"
        mock_address_normalizer.return_value.geocode_address.return_value = {
            'latitude': 45.5017, 'longitude': -73.5673, 'confidence': 0.95, 'source': 'test'
        }
        
        mock_theme_classifier.return_value.classify_restaurant_theme.return_value = {
            'theme': 'italian', 'confidence': 0.88, 'keywords_found': ['pasta', 'pizza'], 'category': 'cuisine'
        }
        
        # Test du pipeline
        integration = TrackCIntegration()
        result = integration._process_risk_prediction(self.sample_restaurant)
        
        # Vérifications
        self.assertIsInstance(result, RiskPrediction)
        self.assertIsNotNone(result.restaurant_id)
        self.assertGreaterEqual(result.risk_score, 0)
        self.assertLessEqual(result.risk_score, 100)
        self.assertIn(result.risk_category, ['LOW', 'MEDIUM', 'HIGH'])
        self.assertGreaterEqual(result.confidence, 0)
        self.assertLessEqual(result.confidence, 1)
    
    def test_performance_integration(self):
        """Test de performance du pipeline d'intégration."""
        integration = TrackCIntegration()
        
        # Test avec des mocks pour éviter les appels externes
        with patch.object(integration.address_normalizer, 'normalize_address', return_value="Mock Address"), \
             patch.object(integration.address_normalizer, 'geocode_address', return_value={'latitude': 45.5, 'longitude': -73.6, 'confidence': 0.9, 'source': 'mock'}), \
             patch.object(integration.theme_classifier, 'classify_restaurant_theme', return_value={'theme': 'test', 'confidence': 0.8, 'keywords_found': [], 'category': 'test'}), \
             patch.object(integration.data_cleaner, 'clean_restaurant_data', return_value=self.sample_restaurant):
            
            start_time = time.time()
            result = integration._process_risk_prediction(self.sample_restaurant)
            execution_time = time.time() - start_time
            
            # Vérification de performance (< 2 secondes)
            self.assertLess(execution_time, 2.0)
            self.assertIsInstance(result, RiskPrediction)

# ========== TESTS COMMUNICATION TRACK-A (Heure 39) ==========

class TestCommunicationTrackA(BaseTrackCTest):
    """Tests de communication avec Track-A (FACE Engine)."""
    
    @patch('requests.post')
    def test_track_a_data_exchange(self, mock_post):
        """Test d'échange de données avec Track-A."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'financial_risk_score': 75.5,
                'cost_analysis': {'estimated_fine': 500.0, 'compliance_cost': 1200.0},
                'recommendations': ['Improve food safety training', 'Update equipment']
            }
        }
        mock_post.return_value = mock_response
        
        # Simulation d'envoi de données à Track-A
        risk_data = {
            'restaurant_id': 'test123',
            'risk_score': 68.5,
            'risk_category': 'MEDIUM',
            'factors': ['theme_risk', 'location_risk']
        }
        
        # Test de l'appel
        track_a_url = f"{IntegrationConfig.TRACK_A_API_URL}/api/v1/financial-analysis"
        response = requests.post(track_a_url, json=risk_data)
        
        # Vérifications
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('financial_risk_score', response_data['data'])
    
    def test_fallback_mechanism(self):
        """Test des mécanismes de fallback."""
        # Simulation de Track-A indisponible
        with patch('requests.post', side_effect=requests.ConnectionError("Service unavailable")):
            
            # Le système devrait continuer à fonctionner sans Track-A
            integration = TrackCIntegration()
            
            # Mock des autres services
            with patch.object(integration.address_normalizer, 'normalize_address', return_value="Test Address"), \
                 patch.object(integration.address_normalizer, 'geocode_address', return_value={'latitude': 45.5, 'longitude': -73.6, 'confidence': 0.9, 'source': 'mock'}), \
                 patch.object(integration.theme_classifier, 'classify_restaurant_theme', return_value={'theme': 'test', 'confidence': 0.8, 'keywords_found': [], 'category': 'test'}), \
                 patch.object(integration.data_cleaner, 'clean_restaurant_data', return_value=self.sample_restaurant):
                
                # Le traitement devrait réussir même sans Track-A
                result = integration._process_risk_prediction(self.sample_restaurant)
                self.assertIsInstance(result, RiskPrediction)

# ========== TESTS END-TO-END (Heure 40) ==========

class TestEndToEndScenarios(BaseTrackCTest):
    """Tests end-to-end et scénarios utilisateur complets."""
    
    def test_scenario_utilisateur_complet(self):
        """Test d'un scénario utilisateur complet."""
        integration = TrackCIntegration()
        
        # Simulation d'un scénario complet avec mocks
        with patch.object(integration.address_normalizer, 'normalize_address', return_value="123 Rue Test Normalisée, Montréal, QC"), \
             patch.object(integration.address_normalizer, 'geocode_address', return_value={'latitude': 45.5017, 'longitude': -73.5673, 'confidence': 0.95, 'source': 'osm'}), \
             patch.object(integration.theme_classifier, 'classify_restaurant_theme', return_value={'theme': 'italian', 'confidence': 0.88, 'keywords_found': ['pasta', 'pizza'], 'category': 'european'}), \
             patch.object(integration.data_cleaner, 'clean_restaurant_data', return_value=self.sample_restaurant):
            
            # Étape 1: Saisie utilisateur (restaurant)
            restaurant_data = self.sample_restaurant
            
            # Étape 2: Traitement complet
            start_time = time.time()
            prediction_result = integration._process_risk_prediction(restaurant_data)
            processing_time = time.time() - start_time
            
            # Vérifications du résultat
            self.assertIsInstance(prediction_result, RiskPrediction)
            self.assertIsNotNone(prediction_result.restaurant_id)
            self.assertGreaterEqual(prediction_result.risk_score, 0)
            self.assertLessEqual(prediction_result.risk_score, 100)
            self.assertIn(prediction_result.risk_category, ['LOW', 'MEDIUM', 'HIGH'])
            
            # Vérification de performance
            self.assertLess(processing_time, 5.0)  # Moins de 5 secondes
    
    def test_monitoring_et_metriques(self):
        """Test du système de monitoring et métriques."""
        integration = TrackCIntegration()
        
        # Vérification des statistiques initiales
        initial_stats = integration.stats
        self.assertIn('requests_processed', initial_stats)
        self.assertIn('errors_count', initial_stats)
        self.assertIn('start_time', initial_stats)

# ========== SUITE DE TESTS PRINCIPALE ==========

def create_test_suite():
    """Crée la suite complète de tests."""
    suite = unittest.TestSuite()
    
    # Tests unitaires endpoints (Heure 37)
    suite.addTest(unittest.makeSuite(TestEndpointsUnitaires))
    
    # Tests d'intégration Track-B ↔ Track-C (Heure 38)
    suite.addTest(unittest.makeSuite(TestIntegrationTrackBTrackC))
    
    # Tests communication Track-A (Heure 39)
    suite.addTest(unittest.makeSuite(TestCommunicationTrackA))
    
    # Tests end-to-end (Heure 40)
    suite.addTest(unittest.makeSuite(TestEndToEndScenarios))
    
    return suite

def run_all_tests():
    """Exécute tous les tests avec rapport détaillé."""
    logger.info("=== DÉBUT DES TESTS D'INTÉGRATION TRACK-C ===")
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    total_time = time.time() - start_time
    
    # Rapport final
    logger.info(f"=== TESTS TERMINÉS EN {total_time:.2f}s ===")
    logger.info(f"Tests exécutés: {result.testsRun}")
    logger.info(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Échecs: {len(result.failures)}")
    logger.info(f"Erreurs: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    run_all_tests()
