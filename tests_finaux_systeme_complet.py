"""
Tests Finaux du Système MAPAQ Complet
Validation end-to-end de tous les modules intégrés

Auteur: Mouhamed Thiaw
Date: 2025-01-17
Heures: 69-72 (Jeudi - Tests Finaux Système Complet)
"""

import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any

# Import de tous les modules développés
try:
    from model_baseline_complet import BaselineModel, RegressionLogistique, NaiveBayes, FeaturePreprocessor
    from probability_engine_complet import ProbabilityEngine
    from rule_adapter import RuleAdapter
    from risk_score import RiskScorer
    from risk_categorizer import RiskCategorizer
    from validation_croisee_modeles import ValidationCroisee
    from optimisation_hyperparametres import OptimisateurHyperparametres
except ImportError as e:
    print(f"Erreur import modules: {e}")
    sys.exit(1)

class TesteurSystemeComplet:
    """
    Testeur complet du système MAPAQ intégré.
    Valide tous les modules et leur intégration.
    """
    
    def __init__(self):
        """Initialise le testeur système."""
        self.resultats_tests = {}
        self.temps_execution = {}
        self.erreurs = []
        
        print("TESTEUR SYSTÈME MAPAQ COMPLET INITIALISÉ")
        print("="*60)
    
    def executer_tests_complets(self) -> Dict[str, Any]:
        """Exécute tous les tests du système."""
        
        tests_a_executer = [
            ("Test 1: Modèles Baseline", self._test_modeles_baseline),
            ("Test 2: Moteur Probabilités", self._test_moteur_probabilites),
            ("Test 3: Adaptateur Règles", self._test_adaptateur_regles),
            ("Test 4: Générateur Scores", self._test_generateur_scores),
            ("Test 5: Catégorisateur Risques", self._test_categorisateur_risques),
            ("Test 6: Pipeline Intégré", self._test_pipeline_integre),
            ("Test 7: Performance Système", self._test_performance_systeme),
            ("Test 8: Robustesse Erreurs", self._test_robustesse_erreurs)
        ]
        
        for nom_test, fonction_test in tests_a_executer:
            print(f"\n{nom_test}")
            print("-" * 50)
            
            debut = time.time()
            try:
                resultat = fonction_test()
                self.resultats_tests[nom_test] = {
                    'statut': 'RÉUSSI' if resultat else 'ÉCHEC',
                    'details': resultat,
                    'erreur': None
                }
            except Exception as e:
                self.resultats_tests[nom_test] = {
                    'statut': 'ERREUR',
                    'details': None,
                    'erreur': str(e)
                }
                self.erreurs.append(f"{nom_test}: {e}")
                print(f"ERREUR: {e}")
            
            fin = time.time()
            self.temps_execution[nom_test] = fin - debut
            print(f"Temps: {self.temps_execution[nom_test]:.2f}s")
        
        return self._generer_rapport_final()
    
    def _test_modeles_baseline(self) -> bool:
        """Test des modèles baseline."""
        
        # Génération de données test
        donnees_test = self._generer_donnees_test(100)
        
        # Test Régression Logistique
        preprocessor = FeaturePreprocessor()
        features, labels = preprocessor.prepare_features(donnees_test)
        
        reg_log = RegressionLogistique(learning_rate=0.01, max_iterations=100)
        reg_log.fit(features, labels)
        predictions_reg = reg_log.predict(features)
        
        # Test Naïve Bayes
        naive_bayes = NaiveBayes()
        naive_bayes.fit(features, labels)
        predictions_nb = naive_bayes.predict(features)
        
        # Validation
        success_reg = len(predictions_reg) == len(labels)
        success_nb = len(predictions_nb) == len(labels)
        
        print(f"Régression Logistique: {success_reg}")
        print(f"Naïve Bayes: {success_nb}")
        
        return success_reg and success_nb
    
    def _test_moteur_probabilites(self) -> bool:
        """Test du moteur de probabilités."""
        
        engine = ProbabilityEngine()
        
        # Test sur différents types de restaurants
        restaurants_test = [
            {'nom': 'Fast Food Test', 'theme': 'fast_food', 'taille': 'grand'},
            {'nom': 'Restaurant Test', 'theme': 'restaurant', 'taille': 'moyen'},
            {'nom': 'Café Test', 'theme': 'cafe', 'taille': 'petit'}
        ]
        
        resultats_valides = 0
        for restaurant in restaurants_test:
            try:
                resultat = engine.calculate_infraction_probability(restaurant)
                if (0 <= resultat['probabilite_infraction'] <= 1 and 
                    'confiance' in resultat):
                    resultats_valides += 1
                    print(f"{restaurant['nom']}: {resultat['probabilite_infraction']:.3f}")
            except Exception as e:
                print(f"Erreur {restaurant['nom']}: {e}")
        
        return resultats_valides == len(restaurants_test)
    
    def _test_adaptateur_regles(self) -> bool:
        """Test de l'adaptateur de règles."""
        
        adapter = RuleAdapter()
        
        # Test pondération temporelle
        weights = adapter.apply_time_based_weights('2024-01-01')
        test_weights = 'facteur_global' in weights and 0 <= weights['facteur_global'] <= 2
        
        # Test ajustement probabilité
        restaurant_test = {'theme': 'fast_food', 'taille': 'grand'}
        prob_ajustee = adapter.get_adjusted_probability(0.5, restaurant_test)
        test_ajustement = 0 <= prob_ajustee <= 1
        
        # Test mise à jour règles
        nouvelles_regles = {
            'version': '2024.test',
            'date_effective': '2024-06-01',
            'facteurs_risque': {'type_etablissement': {'test': 1.0}}
        }
        test_update = adapter.update_rules(nouvelles_regles)
        
        print(f"Pondération temporelle: {test_weights}")
        print(f"Ajustement probabilité: {test_ajustement}")
        print(f"Mise à jour règles: {test_update}")
        
        return test_weights and test_ajustement and test_update
    
    def _test_generateur_scores(self) -> bool:
        """Test du générateur de scores."""
        
        scorer = RiskScorer()
        
        # Test scoring individuel
        restaurant_test = {
            'nom': 'Test Scorer',
            'theme': 'restaurant',
            'taille': 'moyen',
            'historique_infractions': ['2024-01-01']
        }
        
        resultat = scorer.compute_score(restaurant_test)
        test_individuel = (0 <= resultat['score_final'] <= 100 and 
                          'composantes' in resultat)
        
        # Test scoring batch
        restaurants_batch = [restaurant_test] * 3
        resultats_batch = scorer.compute_batch_scores(restaurants_batch)
        test_batch = ('statistiques_globales' in resultats_batch and
                     resultats_batch['statistiques_globales']['nb_restaurants'] == 3)
        
        print(f"Scoring individuel: {test_individuel} (Score: {resultat['score_final']:.1f})")
        print(f"Scoring batch: {test_batch}")
        
        return test_individuel and test_batch
    
    def _test_categorisateur_risques(self) -> bool:
        """Test du catégorisateur de risques."""
        
        categorizer = RiskCategorizer()
        
        # Test catégorisation individuelle
        scores_test = [25.0, 45.0, 65.0, 85.0]
        categories_attendues = ['faible', 'moyen', 'eleve', 'critique']
        
        resultats_corrects = 0
        for score, categorie_attendue in zip(scores_test, categories_attendues):
            resultat = categorizer.categorize(score)
            if resultat['categorie'] == categorie_attendue:
                resultats_corrects += 1
            print(f"Score {score}: {resultat['categorie']} (attendu: {categorie_attendue})")
        
        # Test catégorisation batch
        scores_avec_contexte = [(score, {'nom': f'Test_{i}'}) 
                               for i, score in enumerate(scores_test)]
        resultats_batch = categorizer.categorize_batch(scores_avec_contexte)
        test_batch = 'statistiques' in resultats_batch
        
        print(f"Catégorisation individuelle: {resultats_corrects}/{len(scores_test)}")
        print(f"Catégorisation batch: {test_batch}")
        
        return resultats_corrects >= 3 and test_batch  # Au moins 75% correct
    
    def _test_pipeline_integre(self) -> bool:
        """Test du pipeline intégré complet."""
        
        print("Test pipeline end-to-end...")
        
        # Initialisation de tous les composants
        engine = ProbabilityEngine()
        adapter = RuleAdapter()
        scorer = RiskScorer(engine, adapter)
        categorizer = RiskCategorizer()
        
        # Restaurant test complet
        restaurant = {
            'nom': 'Pipeline Test Restaurant',
            'theme': 'fast_food',
            'taille': 'grand',
            'zone': 'montreal',
            'historique_infractions': ['2024-01-15', '2023-08-20']
        }
        
        try:
            # Étape 1: Calcul probabilité
            prob_result = engine.calculate_infraction_probability(restaurant)
            print(f"Probabilité: {prob_result['probabilite_infraction']:.3f}")
            
            # Étape 2: Ajustement réglementaire
            prob_ajustee = adapter.get_adjusted_probability(
                prob_result['probabilite_infraction'], restaurant
            )
            print(f"Probabilité ajustée: {prob_ajustee:.3f}")
            
            # Étape 3: Génération score
            score_result = scorer.compute_score(restaurant)
            print(f"Score de risque: {score_result['score_final']:.1f}/100")
            
            # Étape 4: Catégorisation
            categorie_result = categorizer.categorize(score_result['score_final'], restaurant)
            print(f"Catégorie: {categorie_result['categorie'].upper()}")
            print(f"Priorité: {categorie_result['priorite_inspection']}/10")
            
            # Validation pipeline
            pipeline_valide = (
                0 <= prob_result['probabilite_infraction'] <= 1 and
                0 <= prob_ajustee <= 1 and
                0 <= score_result['score_final'] <= 100 and
                categorie_result['categorie'] in ['faible', 'moyen', 'eleve', 'critique']
            )
            
            return pipeline_valide
            
        except Exception as e:
            print(f"Erreur pipeline: {e}")
            return False
    
    def _test_performance_systeme(self) -> bool:
        """Test de performance du système."""
        
        print("Test performance avec 50 restaurants...")
        
        # Génération de données de test
        restaurants = self._generer_donnees_test(50)
        
        # Test performance pipeline complet
        debut = time.time()
        
        scorer = RiskScorer()
        categorizer = RiskCategorizer()
        
        scores_calcules = 0
        categories_assignees = 0
        
        for restaurant in restaurants:
            try:
                # Calcul score
                score_result = scorer.compute_score(restaurant)
                if 0 <= score_result['score_final'] <= 100:
                    scores_calcules += 1
                
                # Catégorisation
                categorie_result = categorizer.categorize(score_result['score_final'], restaurant)
                if categorie_result['categorie'] in ['faible', 'moyen', 'eleve', 'critique']:
                    categories_assignees += 1
                    
            except Exception as e:
                print(f"Erreur performance restaurant: {e}")
        
        fin = time.time()
        temps_total = fin - debut
        temps_par_restaurant = temps_total / len(restaurants)
        
        print(f"Scores calculés: {scores_calcules}/{len(restaurants)}")
        print(f"Catégories assignées: {categories_assignees}/{len(restaurants)}")
        print(f"Temps total: {temps_total:.2f}s")
        print(f"Temps par restaurant: {temps_par_restaurant:.3f}s")
        
        # Critères de performance
        taux_succes = (scores_calcules + categories_assignees) / (2 * len(restaurants))
        performance_acceptable = temps_par_restaurant < 0.1  # < 100ms par restaurant
        
        return taux_succes >= 0.9 and performance_acceptable
    
    def _test_robustesse_erreurs(self) -> bool:
        """Test de robustesse face aux erreurs."""
        
        print("Test robustesse avec données problématiques...")
        
        # Données problématiques
        donnees_problematiques = [
            {},  # Vide
            {'nom': None},  # Valeurs nulles
            {'theme': 'inexistant', 'taille': 'invalide'},  # Valeurs invalides
            {'historique_infractions': ['date-invalide', None, 123]},  # Historique corrompu
        ]
        
        scorer = RiskScorer()
        categorizer = RiskCategorizer()
        
        erreurs_gerees = 0
        total_tests = len(donnees_problematiques)
        
        for i, donnees in enumerate(donnees_problematiques):
            try:
                # Test avec données problématiques
                score_result = scorer.compute_score(donnees)
                
                # Le système doit retourner un résultat même avec des données problématiques
                if 'score_final' in score_result:
                    erreurs_gerees += 1
                    print(f"Test {i+1}: Géré (Score: {score_result['score_final']:.1f})")
                else:
                    print(f"Test {i+1}: Échec - Pas de score retourné")
                    
            except Exception as e:
                print(f"Test {i+1}: Exception non gérée - {e}")
        
        taux_robustesse = erreurs_gerees / total_tests
        print(f"Robustesse: {erreurs_gerees}/{total_tests} ({taux_robustesse:.1%})")
        
        return taux_robustesse >= 0.75  # Au moins 75% des cas problématiques gérés
    
    def _generer_donnees_test(self, nb_restaurants: int) -> List[Dict[str, Any]]:
        """Génère des données de test pour les restaurants."""
        
        import random
        
        themes = ['restaurant', 'fast_food', 'cafe', 'bar', 'hotel']
        tailles = ['petit', 'moyen', 'grand']
        zones = ['montreal', 'quebec', 'laval', 'gatineau', 'sherbrooke']
        
        restaurants = []
        for i in range(nb_restaurants):
            restaurant = {
                'nom': f'Restaurant_Test_{i}',
                'theme': random.choice(themes),
                'taille': random.choice(tailles),
                'zone': random.choice(zones),
                'historique_infractions': []
            }
            
            # Ajout d'historique aléatoire
            if random.random() < 0.3:  # 30% ont des infractions
                nb_infractions = random.randint(1, 3)
                for j in range(nb_infractions):
                    date_infraction = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                    restaurant['historique_infractions'].append(date_infraction)
            
            # Label réel pour validation
            restaurant['label_reel'] = 1 if len(restaurant['historique_infractions']) > 0 else 0
            
            restaurants.append(restaurant)
        
        return restaurants
    
    def _generer_rapport_final(self) -> Dict[str, Any]:
        """Génère le rapport final des tests."""
        
        total_tests = len(self.resultats_tests)
        tests_reussis = sum(1 for r in self.resultats_tests.values() if r['statut'] == 'RÉUSSI')
        tests_echecs = sum(1 for r in self.resultats_tests.values() if r['statut'] == 'ÉCHEC')
        tests_erreurs = sum(1 for r in self.resultats_tests.values() if r['statut'] == 'ERREUR')
        
        temps_total = sum(self.temps_execution.values())
        
        rapport = {
            'resume': {
                'total_tests': total_tests,
                'tests_reussis': tests_reussis,
                'tests_echecs': tests_echecs,
                'tests_erreurs': tests_erreurs,
                'taux_succes': (tests_reussis / total_tests) * 100 if total_tests > 0 else 0,
                'temps_total': temps_total
            },
            'details_tests': self.resultats_tests,
            'temps_execution': self.temps_execution,
            'erreurs': self.erreurs,
            'statut_global': 'SUCCÈS' if tests_reussis == total_tests else 'ÉCHEC PARTIEL'
        }
        
        return rapport
    
    def afficher_rapport_final(self, rapport: Dict[str, Any]):
        """Affiche le rapport final formaté."""
        
        print("\n" + "="*60)
        print("RAPPORT FINAL - TESTS SYSTÈME MAPAQ COMPLET")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        resume = rapport['resume']
        print(f"\nRÉSUMÉ EXÉCUTION:")
        print(f"Total tests: {resume['total_tests']}")
        print(f"Tests réussis: {resume['tests_reussis']}")
        print(f"Tests échecs: {resume['tests_echecs']}")
        print(f"Tests erreurs: {resume['tests_erreurs']}")
        print(f"Taux de succès: {resume['taux_succes']:.1f}%")
        print(f"Temps total: {resume['temps_total']:.2f}s")
        print(f"STATUT GLOBAL: {rapport['statut_global']}")
        
        print(f"\nDÉTAILS PAR TEST:")
        for nom_test, details in rapport['details_tests'].items():
            statut = details['statut']
            temps = rapport['temps_execution'][nom_test]
            print(f"  {nom_test}: {statut} ({temps:.2f}s)")
            if details['erreur']:
                print(f"    Erreur: {details['erreur']}")
        
        if rapport['erreurs']:
            print(f"\nERREURS DÉTECTÉES:")
            for erreur in rapport['erreurs']:
                print(f"  • {erreur}")
        
        print("\n" + "="*60)
        
        # Recommandations finales
        if resume['taux_succes'] >= 90:
            print("🎉 SYSTÈME MAPAQ VALIDÉ - Prêt pour production!")
        elif resume['taux_succes'] >= 75:
            print("⚠️  SYSTÈME PARTIELLEMENT VALIDÉ - Corrections mineures nécessaires")
        else:
            print("❌ SYSTÈME NON VALIDÉ - Corrections majeures requises")

def main():
    """Fonction principale d'exécution des tests."""
    
    testeur = TesteurSystemeComplet()
    
    print("Démarrage des tests finaux du système MAPAQ...")
    print(f"Heure de début: {datetime.now().strftime('%H:%M:%S')}")
    
    # Exécution des tests
    rapport = testeur.executer_tests_complets()
    
    # Affichage du rapport
    testeur.afficher_rapport_final(rapport)
    
    return rapport

if __name__ == "__main__":
    rapport_final = main()
