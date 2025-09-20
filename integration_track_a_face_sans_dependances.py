"""
Intégration Track-A (FACE) avec Track-B (MAPAQ) - Version Sans Dépendances
Connexion bi-directionnelle simulée entre moteur financier et système prédictif

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceSimulatedClient:
    """
    Client simulé d'intégration avec le moteur financier FACE.
    Simule les appels API pour les tests sans dépendances.
    """
    
    def __init__(self, face_base_url: str = "http://localhost:8000"):
        """Initialise le client simulé FACE."""
        self.face_base_url = face_base_url
        self.connection_status = True  # Simulation connexion OK
        
        logger.info(f"Client FACE simulé initialisé: {self.face_base_url}")
    
    def test_connection(self) -> bool:
        """Simule le test de connexion FACE."""
        logger.info("Test connexion FACE simulé: OK")
        return self.connection_status
    
    def calculate_financial_impact(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simule le calcul d'impact financier via FACE."""
        
        # Simulation des calculs FACE basés sur les données restaurant
        taille = restaurant_data.get('taille', 'moyen')
        theme = restaurant_data.get('theme', 'restaurant')
        infractions = len(restaurant_data.get('historique_infractions', []))
        
        # Coûts de base simulés
        base_costs = {
            'petit': {'staff': 45000, 'equipment': 25000, 'location': 20000, 'operational': 35000},
            'moyen': {'staff': 75000, 'equipment': 50000, 'location': 40000, 'operational': 60000},
            'grand': {'staff': 110000, 'equipment': 85000, 'location': 70000, 'operational': 95000}
        }
        
        # Facteurs thématiques
        theme_factors = {
            'fast_food': 0.9,
            'restaurant': 1.0,
            'cafe': 0.8,
            'bar': 1.1,
            'hotel': 1.3
        }
        
        costs = base_costs.get(taille, base_costs['moyen'])
        theme_factor = theme_factors.get(theme, 1.0)
        
        # Ajustement selon infractions
        violation_factor = 1 + (infractions * 0.08)
        
        # Calcul final
        adjusted_costs = {k: int(v * theme_factor * violation_factor) for k, v in costs.items()}
        total_cost = sum(adjusted_costs.values())
        
        result = {
            'total_cost': total_cost,
            'cost_breakdown': adjusted_costs,
            'theme_factor': theme_factor,
            'violation_factor': violation_factor,
            'simulation_data': True,
            'confidence': 0.85
        }
        
        logger.info(f"Calcul financier simulé: {total_cost:,}$ pour {restaurant_data.get('nom', 'Restaurant')}")
        return result
    
    def send_risk_assessment(self, restaurant_id: str, risk_data: Dict[str, Any]) -> bool:
        """Simule l'envoi d'évaluation de risque vers FACE."""
        logger.info(f"Évaluation risque envoyée (simulé): {restaurant_id}")
        return True
    
    def get_financial_context(self, restaurant_id: str) -> Dict[str, Any]:
        """Simule la récupération de contexte financier."""
        context = {
            'budget_annuel': 250000,
            'marge_beneficiaire': 0.12,
            'seuil_risque_financier': 15000,
            'simulation_data': True
        }
        logger.info(f"Contexte financier simulé récupéré: {restaurant_id}")
        return context

class MapaqFaceIntegratorSimulated:
    """
    Intégrateur MAPAQ-FACE simulé pour tests sans dépendances.
    """
    
    def __init__(self, face_url: str = "http://localhost:8000"):
        """Initialise l'intégrateur simulé."""
        self.face_client = FaceSimulatedClient(face_url)
        
        # Import des modules MAPAQ
        try:
            from risk_score import RiskScorer
            from risk_categorizer import RiskCategorizer
            from probability_engine_complet import ProbabilityEngine
            
            self.risk_scorer = RiskScorer()
            self.risk_categorizer = RiskCategorizer()
            self.probability_engine = ProbabilityEngine()
            
            logger.info("Intégrateur MAPAQ-FACE simulé initialisé")
        except ImportError as e:
            logger.error(f"Erreur import modules MAPAQ: {e}")
            raise
    
    def process_restaurant_complete(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traitement complet simulé d'un restaurant."""
        
        restaurant_id = restaurant_data.get('id', restaurant_data.get('nom', 'unknown'))
        logger.info(f"Traitement complet simulé: {restaurant_id}")
        
        # 1. Évaluation risque MAPAQ
        mapaq_results = self._process_mapaq_assessment(restaurant_data)
        
        # 2. Calcul impact financier FACE (simulé)
        financial_results = self.face_client.calculate_financial_impact(restaurant_data)
        
        # 3. Intégration des résultats
        integrated_results = self._integrate_results(mapaq_results, financial_results, restaurant_data)
        
        # 4. Envoi feedback vers FACE (simulé)
        self.face_client.send_risk_assessment(restaurant_id, mapaq_results)
        
        return integrated_results
    
    def _process_mapaq_assessment(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Effectue l'évaluation complète MAPAQ."""
        
        # Calcul probabilité
        prob_result = self.probability_engine.calculate_infraction_probability(restaurant_data)
        
        # Génération score
        score_result = self.risk_scorer.compute_score(restaurant_data)
        
        # Catégorisation
        category_result = self.risk_categorizer.categorize(score_result['score_final'], restaurant_data)
        
        return {
            'probabilite_infraction': prob_result['probabilite_infraction'],
            'confiance_probabilite': prob_result.get('confiance', prob_result.get('niveau_confiance', 0.75)),
            'score_risque': score_result['score_final'],
            'composantes_score': score_result['composantes'],
            'categorie_risque': category_result['categorie'],
            'priorite_inspection': category_result['priorite_inspection'],
            'recommandations': category_result.get('recommandations', []),
            'delai_inspection': category_result.get('delai_inspection_recommande', 30)
        }
    
    def _integrate_results(self, mapaq_results: Dict[str, Any], 
                          financial_results: Dict[str, Any], 
                          restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intègre les résultats MAPAQ et FACE."""
        
        # Calcul impact financier du risque
        financial_risk_impact = self._calculate_financial_risk_impact(mapaq_results, financial_results)
        
        # Score composite MAPAQ-FACE
        composite_score = self._calculate_composite_score(mapaq_results, financial_results)
        
        # Recommandations intégrées
        integrated_recommendations = self._generate_integrated_recommendations(
            mapaq_results, financial_results, financial_risk_impact
        )
        
        return {
            'restaurant': {
                'nom': restaurant_data.get('nom', 'Restaurant'),
                'theme': restaurant_data.get('theme', 'restaurant'),
                'taille': restaurant_data.get('taille', 'moyen')
            },
            'evaluation_mapaq': mapaq_results,
            'calculs_financiers': financial_results,
            'impact_financier_risque': financial_risk_impact,
            'score_composite': composite_score,
            'recommandations_integrees': integrated_recommendations,
            'timestamp': datetime.now().isoformat(),
            'integration_version': '1.0-simulated'
        }
    
    def _calculate_financial_risk_impact(self, mapaq_results: Dict[str, Any], 
                                       financial_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule l'impact financier du risque sanitaire."""
        
        base_cost = financial_results.get('total_cost', 100000)
        risk_score = mapaq_results.get('score_risque', 50)
        risk_category = mapaq_results.get('categorie_risque', 'moyen')
        
        # Facteurs d'impact par catégorie
        impact_factors = {
            'faible': 0.02,
            'moyen': 0.05,
            'eleve': 0.12,
            'critique': 0.25
        }
        
        impact_factor = impact_factors.get(risk_category, 0.05)
        
        # Coûts additionnels estimés
        additional_costs = {
            'inspections_supplementaires': int(base_cost * impact_factor * 0.3),
            'mesures_correctives': int(base_cost * impact_factor * 0.4),
            'formation_personnel': int(base_cost * impact_factor * 0.2),
            'amendes_potentielles': int(base_cost * impact_factor * 0.1)
        }
        
        total_additional_cost = sum(additional_costs.values())
        
        return {
            'facteur_impact': impact_factor,
            'cout_base': base_cost,
            'couts_additionnels': additional_costs,
            'cout_additionnel_total': total_additional_cost,
            'cout_total_estime': base_cost + total_additional_cost,
            'pourcentage_augmentation': (total_additional_cost / base_cost) * 100
        }
    
    def _calculate_composite_score(self, mapaq_results: Dict[str, Any], 
                                 financial_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule un score composite MAPAQ-FACE."""
        
        mapaq_score = mapaq_results.get('score_risque', 50)
        total_cost = financial_results.get('total_cost', 100000)
        financial_score = min(100, (total_cost / 200000) * 100)
        
        # Pondération: 70% MAPAQ, 30% financier
        composite_score = (mapaq_score * 0.7) + (financial_score * 0.3)
        
        if composite_score >= 80:
            composite_category = 'critique'
        elif composite_score >= 60:
            composite_category = 'eleve'
        elif composite_score >= 40:
            composite_category = 'moyen'
        else:
            composite_category = 'faible'
        
        return {
            'score_composite': composite_score,
            'categorie_composite': composite_category,
            'composantes': {
                'score_mapaq': mapaq_score,
                'score_financier': financial_score,
                'poids_mapaq': 0.7,
                'poids_financier': 0.3
            }
        }
    
    def _generate_integrated_recommendations(self, mapaq_results: Dict[str, Any], 
                                           financial_results: Dict[str, Any],
                                           financial_impact: Dict[str, Any]) -> List[str]:
        """Génère des recommandations intégrées MAPAQ-FACE."""
        
        recommendations = []
        risk_category = mapaq_results.get('categorie_risque', 'moyen')
        financial_impact_pct = financial_impact.get('pourcentage_augmentation', 5)
        
        if risk_category == 'critique':
            recommendations.extend([
                "URGENT: Inspection immédiate requise",
                f"Budget supplémentaire de {financial_impact['cout_additionnel_total']:,}$ nécessaire",
                "Mise en place d'un plan de conformité accéléré"
            ])
        elif risk_category == 'eleve':
            recommendations.extend([
                "Inspection prioritaire dans les 7 jours",
                f"Prévoir {financial_impact_pct:.1f}% de budget supplémentaire",
                "Audit des procédures sanitaires recommandé"
            ])
        elif risk_category == 'moyen':
            recommendations.extend([
                "Inspection de routine dans les 30 jours",
                "Révision des protocoles de nettoyage"
            ])
        else:
            recommendations.extend([
                "Maintenir les bonnes pratiques actuelles",
                "Inspection de routine selon calendrier normal"
            ])
        
        if financial_impact_pct > 15:
            recommendations.append("Considérer un financement pour les mesures correctives")
        
        return recommendations

def demo_integration_face_simulated():
    """Démonstration de l'intégration MAPAQ-FACE simulée."""
    
    print("DÉMONSTRATION INTÉGRATION MAPAQ-FACE (SIMULÉE)")
    print("="*55)
    
    # Initialisation
    integrator = MapaqFaceIntegratorSimulated()
    
    # Test de connexion FACE
    print("\n--- TEST CONNEXION FACE ---")
    connection_ok = integrator.face_client.test_connection()
    print(f"Connexion FACE: {'OK (simule)' if connection_ok else 'ECHEC'}")
    
    # Restaurants de test
    restaurants_test = [
        {
            'id': 'REST_001',
            'nom': 'Fast Food Critique',
            'theme': 'fast_food',
            'taille': 'grand',
            'zone': 'montreal',
            'historique_infractions': ['2024-01-15', '2023-11-20', '2023-08-10']
        },
        {
            'id': 'REST_002',
            'nom': 'Restaurant Moyen',
            'theme': 'restaurant',
            'taille': 'moyen',
            'zone': 'quebec',
            'historique_infractions': ['2023-12-01']
        },
        {
            'id': 'REST_003',
            'nom': 'Café Faible',
            'theme': 'cafe',
            'taille': 'petit',
            'zone': 'laval',
            'historique_infractions': []
        }
    ]
    
    print(f"\n--- TRAITEMENT BATCH INTÉGRÉ ---")
    
    resultats_batch = []
    for restaurant in restaurants_test:
        print(f"\nTraitement: {restaurant['nom']}")
        
        # Traitement intégré
        results = integrator.process_restaurant_complete(restaurant)
        resultats_batch.append(results)
        
        # Affichage résumé
        eval_mapaq = results['evaluation_mapaq']
        composite = results['score_composite']
        impact = results['impact_financier_risque']
        
        print(f"  Score MAPAQ: {eval_mapaq['score_risque']:.1f}/100")
        print(f"  Catégorie: {eval_mapaq['categorie_risque'].upper()}")
        print(f"  Score composite: {composite['score_composite']:.1f}/100")
        print(f"  Impact financier: +{impact['pourcentage_augmentation']:.1f}%")
        print(f"  Coût total estimé: {impact['cout_total_estime']:,}$")
    
    # Statistiques globales
    print(f"\n--- STATISTIQUES GLOBALES ---")
    scores_mapaq = [r['evaluation_mapaq']['score_risque'] for r in resultats_batch]
    scores_composite = [r['score_composite']['score_composite'] for r in resultats_batch]
    impacts_financiers = [r['impact_financier_risque']['pourcentage_augmentation'] for r in resultats_batch]
    
    print(f"Score MAPAQ moyen: {sum(scores_mapaq)/len(scores_mapaq):.1f}")
    print(f"Score composite moyen: {sum(scores_composite)/len(scores_composite):.1f}")
    print(f"Impact financier moyen: {sum(impacts_financiers)/len(impacts_financiers):.1f}%")
    
    # Distribution des catégories
    categories = [r['evaluation_mapaq']['categorie_risque'] for r in resultats_batch]
    distribution = {}
    for cat in categories:
        distribution[cat] = distribution.get(cat, 0) + 1
    
    print(f"\nDistribution des risques:")
    for cat, count in distribution.items():
        print(f"  {cat.capitalize()}: {count} ({count/len(categories)*100:.1f}%)")
    
    return resultats_batch

if __name__ == "__main__":
    demo_integration_face_simulated()
