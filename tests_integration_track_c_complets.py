"""
Tests Complets d'Intégration Track-C
Suite de tests pour l'intégration Track-A + Track-B + Track-C

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import unittest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from integration_track_c_complete import (
    GestionnaireIntegrationTrackC, RestaurantComplet, AnalyseComposite,
    creer_app_integration
)

class TestsIntegrationTrackC(unittest.TestCase):
    """Tests d'intégration pour le système Track-C complet."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.gestionnaire = GestionnaireIntegrationTrackC()
        self.donnees_restaurant_test = {
            'nom': 'Restaurant Test Intégration',
            'adresse': '123 Rue Test, Montréal, QC H1A 1A1',
            'theme_cuisine': 'italian',
            'telephone': '514-555-1234',
            'taille_revenus': 'medium',
            'nombre_employes': 8,
            'taille_cuisine': 75.0
        }
    
    def test_validation_donnees_entree(self):
        """Test de validation des données d'entrée."""
        # Test avec données valides
        donnees_valides = self.gestionnaire.schema_entree.load(self.donnees_restaurant_test)
        self.assertEqual(donnees_valides['nom'], 'Restaurant Test Intégration')
        
        # Test avec données invalides
        donnees_invalides = {'nom': '', 'adresse': 'trop court'}
        with self.assertRaises(Exception):
            self.gestionnaire.schema_entree.load(donnees_invalides)
    
    @patch('integration_track_c_complete.aiohttp.ClientSession')
    def test_communication_track_a(self, mock_session):
        """Test de communication avec Track-A (FACE)."""
        # Configuration du mock pour Track-A
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'total_cost': 45000.0,
            'staff_costs': 18000.0,
            'equipment_costs': 11250.0,
            'location_costs': 9000.0,
            'operational_costs': 6750.0
        })
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        # Test de la communication
        restaurant = RestaurantComplet(**self.donnees_restaurant_test)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resultats = loop.run_until_complete(
                self.gestionnaire._traiter_track_a(restaurant)
            )
            
            self.assertEqual(resultats['total_cost'], 45000.0)
            self.assertIn('staff_costs', resultats)
        finally:
            loop.close()
    
    def test_analyse_composite_creation(self):
        """Test de création d'analyse composite."""
        restaurant = RestaurantComplet(**self.donnees_restaurant_test)
        
        # Données simulées Track-B
        track_b = {
            'score_risque': 65.0,
            'categorie_risque': 'MOYEN',
            'facteurs_risque': ['Type de cuisine à risque: italian'],
            'confiance': 0.85
        }
        
        # Données simulées Track-A
        track_a = {
            'total_cost': 45000.0,
            'staff_costs': 18000.0,
            'equipment_costs': 11250.0,
            'location_costs': 9000.0,
            'operational_costs': 6750.0
        }
        
        # Création de l'analyse composite
        analyse = self.gestionnaire._creer_analyse_composite(restaurant, track_b, track_a)
        
        # Vérifications
        self.assertIsInstance(analyse, AnalyseComposite)
        self.assertEqual(analyse.score_risque, 65.0)
        self.assertEqual(analyse.cout_total_estime, 45000.0)
        self.assertGreater(analyse.score_composite, 0)
        self.assertIsInstance(analyse.recommandations, list)
    
    def test_calcul_score_risque_simule(self):
        """Test du calcul de score de risque simulé."""
        restaurant = RestaurantComplet(**self.donnees_restaurant_test)
        
        theme_mock = {'theme': 'italian', 'confidence': 0.9}
        geo_mock = {'latitude': 45.5017, 'longitude': -73.5673}
        
        score = self.gestionnaire._calculer_score_risque_simule(restaurant, theme_mock, geo_mock)
        
        # Le score doit être entre 0 et 100
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
    
    def test_categorisation_risque(self):
        """Test de catégorisation des niveaux de risque."""
        self.assertEqual(self.gestionnaire._categoriser_risque(25.0), "FAIBLE")
        self.assertEqual(self.gestionnaire._categoriser_risque(50.0), "MOYEN")
        self.assertEqual(self.gestionnaire._categoriser_risque(85.0), "ÉLEVÉ")
    
    def test_generation_recommandations(self):
        """Test de génération des recommandations."""
        track_b = {'score_risque': 75.0, 'categorie_risque': 'ÉLEVÉ'}
        track_a = {'total_cost': 90000.0}
        
        recommandations = self.gestionnaire._generer_recommandations(track_b, track_a, 80.0)
        
        self.assertIsInstance(recommandations, list)
        self.assertGreater(len(recommandations), 0)
        # Vérifier qu'il y a des recommandations pour risque élevé
        self.assertTrue(any('Priorité élevée' in rec for rec in recommandations))
    
    def test_calcul_prochaine_inspection(self):
        """Test du calcul de la prochaine inspection."""
        # Test pour risque élevé
        prochaine = self.gestionnaire._calculer_prochaine_inspection(85.0, 'ÉLEVÉ')
        self.assertIsInstance(prochaine, datetime)
        
        # La prochaine inspection doit être dans le futur
        self.assertGreater(prochaine, datetime.now())
    
    def test_mise_a_jour_statistiques(self):
        """Test de mise à jour des statistiques."""
        stats_initiales = self.gestionnaire.stats['requetes_traitees']
        
        self.gestionnaire._mettre_a_jour_stats(1.5, succes=True)
        
        self.assertEqual(
            self.gestionnaire.stats['requetes_traitees'], 
            stats_initiales + 1
        )
        self.assertGreater(self.gestionnaire.stats['temps_reponse_moyen'], 0)
    
    def test_fallback_track_a(self):
        """Test du mécanisme de fallback pour Track-A."""
        restaurant = RestaurantComplet(**self.donnees_restaurant_test)
        
        resultats_fallback = self.gestionnaire._generer_analyse_financiere_fallback(restaurant)
        
        self.assertIn('total_cost', resultats_fallback)
        self.assertIn('fallback', resultats_fallback)
        self.assertTrue(resultats_fallback['fallback'])
        self.assertGreater(resultats_fallback['total_cost'], 0)

class TestsAPIIntegration(unittest.TestCase):
    """Tests de l'API Flask d'intégration."""
    
    def setUp(self):
        """Configuration de l'application de test."""
        self.app = creer_app_integration()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_endpoint_sante(self):
        """Test de l'endpoint de santé."""
        response = self.client.get('/api/v1/sante')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['succes'])
        self.assertEqual(data['service'], 'Intégration Track-C MAPAQ')
        self.assertIn('statistiques', data)
    
    def test_endpoint_statistiques(self):
        """Test de l'endpoint des statistiques."""
        response = self.client.get('/api/v1/statistiques')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['succes'])
        self.assertIn('donnees', data)
        self.assertIn('requetes_traitees', data['donnees'])
    
    @patch('integration_track_c_complete.GestionnaireIntegrationTrackC.analyser_restaurant_complet')
    def test_endpoint_analyser_restaurant_succes(self, mock_analyser):
        """Test de l'endpoint d'analyse avec succès."""
        # Configuration du mock
        mock_analyse = AnalyseComposite(
            restaurant_id='test_123',
            score_risque=65.0,
            categorie_risque='MOYEN',
            facteurs_risque=['Test'],
            confiance_prediction=0.85,
            cout_total_estime=45000.0,
            cout_personnel=18000.0,
            cout_equipement=11250.0,
            cout_immobilier=9000.0,
            cout_operationnel=6750.0,
            score_composite=70.0,
            recommandations=['Test recommandation'],
            prochaine_inspection_suggeree=datetime.now(),
            timestamp_analyse=datetime.now()
        )
        
        # Configuration du mock pour retourner une coroutine
        async def mock_coroutine(*args, **kwargs):
            return mock_analyse
        
        mock_analyser.return_value = mock_coroutine()
        
        # Test de la requête
        donnees_test = {
            'nom': 'Restaurant Test API',
            'adresse': '123 Test Street',
            'theme_cuisine': 'italian'
        }
        
        response = self.client.post(
            '/api/v1/analyser-restaurant',
            data=json.dumps(donnees_test),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['succes'])
        self.assertIn('donnees', data)
    
    def test_endpoint_analyser_restaurant_donnees_invalides(self):
        """Test de l'endpoint d'analyse avec données invalides."""
        donnees_invalides = {'nom': ''}  # Nom vide
        
        response = self.client.post(
            '/api/v1/analyser-restaurant',
            data=json.dumps(donnees_invalides),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['succes'])
        self.assertIn('erreur', data)
    
    def test_endpoint_analyser_restaurant_sans_donnees(self):
        """Test de l'endpoint d'analyse sans données JSON."""
        response = self.client.post('/api/v1/analyser-restaurant')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['succes'])
        self.assertIn('Données JSON requises', data['erreur'])

class TestsPerformanceIntegration(unittest.TestCase):
    """Tests de performance pour l'intégration."""
    
    def setUp(self):
        """Configuration des tests de performance."""
        self.gestionnaire = GestionnaireIntegrationTrackC()
    
    def test_performance_calcul_score_risque(self):
        """Test de performance du calcul de score de risque."""
        restaurant = RestaurantComplet(
            nom='Test Performance',
            adresse='123 Performance St',
            theme_cuisine='italian'
        )
        
        theme_mock = {'theme': 'italian', 'confidence': 0.9}
        geo_mock = {'latitude': 45.5017, 'longitude': -73.5673}
        
        # Mesure du temps d'exécution
        debut = time.time()
        for _ in range(100):  # 100 calculs
            score = self.gestionnaire._calculer_score_risque_simule(
                restaurant, theme_mock, geo_mock
            )
        fin = time.time()
        
        temps_moyen = (fin - debut) / 100
        
        # Le calcul doit être rapide (< 1ms par calcul)
        self.assertLess(temps_moyen, 0.001)
    
    def test_performance_categorisation_risque(self):
        """Test de performance de la catégorisation."""
        scores = [i * 10 for i in range(11)]  # 0, 10, 20, ..., 100
        
        debut = time.time()
        for score in scores * 1000:  # 11000 catégorisations
            categorie = self.gestionnaire._categoriser_risque(score)
        fin = time.time()
        
        temps_total = fin - debut
        
        # Doit être très rapide (< 0.1s pour 11000 opérations)
        self.assertLess(temps_total, 0.1)

def executer_tous_les_tests():
    """Exécute tous les tests d'intégration."""
    print("🧪 === TESTS D'INTÉGRATION TRACK-C ===")
    
    # Création de la suite de tests
    suite = unittest.TestSuite()
    
    # Ajout des tests d'intégration
    suite.addTest(unittest.makeSuite(TestsIntegrationTrackC))
    suite.addTest(unittest.makeSuite(TestsAPIIntegration))
    suite.addTest(unittest.makeSuite(TestsPerformanceIntegration))
    
    # Exécution des tests
    runner = unittest.TextTestRunner(verbosity=2)
    debut = time.time()
    
    resultats = runner.run(suite)
    
    fin = time.time()
    duree = fin - debut
    
    # Rapport final
    print(f"\n📊 === RAPPORT FINAL ===")
    print(f"⏱️  Durée totale: {duree:.2f}s")
    print(f"✅ Tests réussis: {resultats.testsRun - len(resultats.failures) - len(resultats.errors)}")
    print(f"❌ Échecs: {len(resultats.failures)}")
    print(f"🚫 Erreurs: {len(resultats.errors)}")
    
    if resultats.failures:
        print(f"\n🔍 ÉCHECS DÉTAILLÉS:")
        for test, traceback in resultats.failures:
            print(f"  - {test}: {traceback}")
    
    if resultats.errors:
        print(f"\n🚨 ERREURS DÉTAILLÉES:")
        for test, traceback in resultats.errors:
            print(f"  - {test}: {traceback}")
    
    # Taux de succès
    taux_succes = (resultats.testsRun - len(resultats.failures) - len(resultats.errors)) / resultats.testsRun * 100
    print(f"\n🎯 Taux de succès: {taux_succes:.1f}%")
    
    return resultats

if __name__ == "__main__":
    executer_tous_les_tests()
