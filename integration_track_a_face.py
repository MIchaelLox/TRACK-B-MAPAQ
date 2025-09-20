"""
Intégration Track-A (FACE) avec Track-B (MAPAQ)
Connexion bi-directionnelle entre moteur financier et système prédictif

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import sys
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceIntegrationClient:
    """
    Client d'intégration avec le moteur financier FACE (Track-A).
    Permet la communication bi-directionnelle entre MAPAQ et FACE.
    """
    
    def __init__(self, face_base_url: str = "http://localhost:8000"):
        """
        Initialise le client d'intégration FACE.
        
        Args:
            face_base_url: URL de base du moteur FACE
        """
        self.face_base_url = face_base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MAPAQ-Integration/1.0'
        })
        
        logger.info(f"Client d'intégration FACE initialisé: {self.face_base_url}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion avec le moteur FACE.
        
        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            response = self.session.get(f"{self.face_base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Connexion FACE établie avec succès")
                return True
            else:
                logger.warning(f"Connexion FACE échouée: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur connexion FACE: {e}")
            return False
    
    def calculate_financial_impact(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule l'impact financier d'un restaurant via FACE.
        
        Args:
            restaurant_data: Données du restaurant MAPAQ
            
        Returns:
            Résultats des calculs financiers FACE
        """
        try:
            # Transformation des données MAPAQ vers format FACE
            face_input = self._transform_mapaq_to_face(restaurant_data)
            
            # Appel API FACE
            response = self.session.post(
                f"{self.face_base_url}/api/calculate",
                json=face_input,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Calcul financier réussi pour {restaurant_data.get('nom', 'Restaurant')}")
                return result
            else:
                logger.error(f"Erreur calcul FACE: {response.status_code} - {response.text}")
                return self._get_fallback_financial_data(restaurant_data)
                
        except Exception as e:
            logger.error(f"Exception calcul financier: {e}")
            return self._get_fallback_financial_data(restaurant_data)
    
    def send_risk_assessment(self, restaurant_id: str, risk_data: Dict[str, Any]) -> bool:
        """
        Envoie l'évaluation de risque MAPAQ vers FACE.
        
        Args:
            restaurant_id: Identifiant du restaurant
            risk_data: Données d'évaluation de risque MAPAQ
            
        Returns:
            True si l'envoi réussit, False sinon
        """
        try:
            payload = {
                'restaurant_id': restaurant_id,
                'risk_assessment': risk_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'MAPAQ-TrackB'
            }
            
            response = self.session.post(
                f"{self.face_base_url}/api/risk-update",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"Évaluation risque envoyée avec succès: {restaurant_id}")
                return True
            else:
                logger.error(f"Erreur envoi risque: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception envoi risque: {e}")
            return False
    
    def get_financial_context(self, restaurant_id: str) -> Dict[str, Any]:
        """
        Récupère le contexte financier d'un restaurant depuis FACE.
        
        Args:
            restaurant_id: Identifiant du restaurant
            
        Returns:
            Contexte financier du restaurant
        """
        try:
            response = self.session.get(
                f"{self.face_base_url}/api/restaurant/{restaurant_id}/financial-context",
                timeout=10
            )
            
            if response.status_code == 200:
                context = response.json()
                logger.info(f"Contexte financier récupéré: {restaurant_id}")
                return context
            else:
                logger.warning(f"Contexte financier non disponible: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Erreur récupération contexte: {e}")
            return {}
    
    def _transform_mapaq_to_face(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforme les données MAPAQ vers le format FACE.
        
        Args:
            restaurant_data: Données restaurant MAPAQ
            
        Returns:
            Données formatées pour FACE
        """
        # Mapping des tailles MAPAQ vers FACE
        size_mapping = {
            'petit': 'small',
            'moyen': 'medium',
            'grand': 'large'
        }
        
        # Mapping des thèmes MAPAQ vers types FACE
        theme_mapping = {
            'fast_food': 'fast_food',
            'restaurant': 'full_service',
            'cafe': 'cafe',
            'bar': 'bar',
            'hotel': 'hotel'
        }
        
        face_input = {
            'session_name': restaurant_data.get('nom', 'Restaurant MAPAQ'),
            'restaurant_type': theme_mapping.get(restaurant_data.get('theme', 'restaurant'), 'full_service'),
            'size_category': size_mapping.get(restaurant_data.get('taille', 'moyen'), 'medium'),
            'location': restaurant_data.get('zone', 'montreal'),
            'complexity_factors': {
                'has_violations': len(restaurant_data.get('historique_infractions', [])) > 0,
                'violation_count': len(restaurant_data.get('historique_infractions', [])),
                'risk_level': restaurant_data.get('niveau_risque', 'moyen')
            },
            'metadata': {
                'source': 'MAPAQ-Integration',
                'integration_timestamp': datetime.now().isoformat()
            }
        }
        
        return face_input
    
    def _get_fallback_financial_data(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère des données financières de fallback en cas d'échec FACE.
        
        Args:
            restaurant_data: Données restaurant MAPAQ
            
        Returns:
            Données financières estimées
        """
        # Estimations basées sur le type et la taille
        base_costs = {
            'petit': {'staff': 50000, 'equipment': 30000, 'location': 25000, 'operational': 40000},
            'moyen': {'staff': 80000, 'equipment': 60000, 'location': 45000, 'operational': 70000},
            'grand': {'staff': 120000, 'equipment': 100000, 'location': 80000, 'operational': 110000}
        }
        
        taille = restaurant_data.get('taille', 'moyen')
        costs = base_costs.get(taille, base_costs['moyen'])
        
        # Ajustement selon les infractions
        violation_penalty = len(restaurant_data.get('historique_infractions', [])) * 0.05
        total_cost = sum(costs.values()) * (1 + violation_penalty)
        
        return {
            'total_cost': total_cost,
            'cost_breakdown': costs,
            'risk_adjustment': violation_penalty,
            'fallback_data': True,
            'estimation_confidence': 0.6
        }

class MapaqFaceIntegrator:
    """
    Intégrateur principal MAPAQ-FACE.
    Orchestre les échanges bi-directionnels entre les systèmes.
    """
    
    def __init__(self, face_url: str = "http://localhost:8000"):
        """
        Initialise l'intégrateur MAPAQ-FACE.
        
        Args:
            face_url: URL du moteur FACE
        """
        self.face_client = FaceIntegrationClient(face_url)
        
        # Import des modules MAPAQ
        try:
            from risk_score import RiskScorer
            from risk_categorizer import RiskCategorizer
            from probability_engine_complet import ProbabilityEngine
            
            self.risk_scorer = RiskScorer()
            self.risk_categorizer = RiskCategorizer()
            self.probability_engine = ProbabilityEngine()
            
            logger.info("Intégrateur MAPAQ-FACE initialisé avec succès")
        except ImportError as e:
            logger.error(f"Erreur import modules MAPAQ: {e}")
            raise
    
    def process_restaurant_complete(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traitement complet d'un restaurant avec intégration FACE.
        
        Args:
            restaurant_data: Données complètes du restaurant
            
        Returns:
            Résultats intégrés MAPAQ + FACE
        """
        restaurant_id = restaurant_data.get('id', restaurant_data.get('nom', 'unknown'))
        
        logger.info(f"Traitement complet: {restaurant_id}")
        
        # 1. Évaluation risque MAPAQ
        mapaq_results = self._process_mapaq_assessment(restaurant_data)
        
        # 2. Calcul impact financier FACE
        financial_results = self.face_client.calculate_financial_impact(restaurant_data)
        
        # 3. Intégration des résultats
        integrated_results = self._integrate_results(mapaq_results, financial_results, restaurant_data)
        
        # 4. Envoi feedback vers FACE
        self.face_client.send_risk_assessment(restaurant_id, mapaq_results)
        
        logger.info(f"Traitement complet terminé: {restaurant_id}")
        
        return integrated_results
    
    def _process_mapaq_assessment(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue l'évaluation complète MAPAQ.
        
        Args:
            restaurant_data: Données du restaurant
            
        Returns:
            Résultats évaluation MAPAQ
        """
        # Calcul probabilité
        prob_result = self.probability_engine.calculate_infraction_probability(restaurant_data)
        
        # Génération score
        score_result = self.risk_scorer.compute_score(restaurant_data)
        
        # Catégorisation
        category_result = self.risk_categorizer.categorize(score_result['score_final'], restaurant_data)
        
        return {
            'probabilite_infraction': prob_result['probabilite_infraction'],
            'confiance_probabilite': prob_result['confiance'],
            'score_risque': score_result['score_final'],
            'composantes_score': score_result['composantes'],
            'categorie_risque': category_result['categorie'],
            'priorite_inspection': category_result['priorite_inspection'],
            'recommandations': category_result['recommandations'],
            'delai_inspection': category_result['delai_inspection_recommande']
        }
    
    def _integrate_results(self, mapaq_results: Dict[str, Any], 
                          financial_results: Dict[str, Any], 
                          restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intègre les résultats MAPAQ et FACE.
        
        Args:
            mapaq_results: Résultats évaluation MAPAQ
            financial_results: Résultats calculs FACE
            restaurant_data: Données originales restaurant
            
        Returns:
            Résultats intégrés
        """
        # Calcul impact financier du risque
        financial_risk_impact = self._calculate_financial_risk_impact(
            mapaq_results, financial_results
        )
        
        # Score composite MAPAQ-FACE
        composite_score = self._calculate_composite_score(
            mapaq_results, financial_results
        )
        
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
            'integration_version': '1.0'
        }
    
    def _calculate_financial_risk_impact(self, mapaq_results: Dict[str, Any], 
                                       financial_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule l'impact financier du risque sanitaire.
        
        Args:
            mapaq_results: Résultats MAPAQ
            financial_results: Résultats FACE
            
        Returns:
            Impact financier du risque
        """
        base_cost = financial_results.get('total_cost', 100000)
        risk_score = mapaq_results.get('score_risque', 50)
        risk_category = mapaq_results.get('categorie_risque', 'moyen')
        
        # Facteurs d'impact par catégorie
        impact_factors = {
            'faible': 0.02,    # 2% de coût supplémentaire
            'moyen': 0.05,     # 5% de coût supplémentaire
            'eleve': 0.12,     # 12% de coût supplémentaire
            'critique': 0.25   # 25% de coût supplémentaire
        }
        
        impact_factor = impact_factors.get(risk_category, 0.05)
        
        # Coûts additionnels estimés
        additional_costs = {
            'inspections_supplementaires': base_cost * impact_factor * 0.3,
            'mesures_correctives': base_cost * impact_factor * 0.4,
            'formation_personnel': base_cost * impact_factor * 0.2,
            'amendes_potentielles': base_cost * impact_factor * 0.1
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
        """
        Calcule un score composite MAPAQ-FACE.
        
        Args:
            mapaq_results: Résultats MAPAQ
            financial_results: Résultats FACE
            
        Returns:
            Score composite
        """
        # Normalisation des scores (0-100)
        mapaq_score = mapaq_results.get('score_risque', 50)
        
        # Score financier basé sur les coûts (normalisé)
        total_cost = financial_results.get('total_cost', 100000)
        financial_score = min(100, (total_cost / 200000) * 100)  # Normalisation sur 200k
        
        # Pondération: 70% MAPAQ, 30% financier
        composite_score = (mapaq_score * 0.7) + (financial_score * 0.3)
        
        # Catégorisation composite
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
        """
        Génère des recommandations intégrées MAPAQ-FACE.
        
        Args:
            mapaq_results: Résultats MAPAQ
            financial_results: Résultats FACE
            financial_impact: Impact financier
            
        Returns:
            Liste de recommandations intégrées
        """
        recommendations = []
        
        risk_category = mapaq_results.get('categorie_risque', 'moyen')
        financial_impact_pct = financial_impact.get('pourcentage_augmentation', 5)
        
        # Recommandations selon le niveau de risque
        if risk_category == 'critique':
            recommendations.extend([
                "URGENT: Inspection immédiate requise",
                f"Budget supplémentaire de {financial_impact['cout_additionnel_total']:,.0f}$ nécessaire",
                "Mise en place d'un plan de conformité accéléré",
                "Formation intensive du personnel sur les normes sanitaires"
            ])
        elif risk_category == 'eleve':
            recommendations.extend([
                "Inspection prioritaire dans les 7 jours",
                f"Prévoir {financial_impact_pct:.1f}% de budget supplémentaire",
                "Audit des procédures sanitaires recommandé",
                "Renforcement des mesures de contrôle qualité"
            ])
        elif risk_category == 'moyen':
            recommendations.extend([
                "Inspection de routine dans les 30 jours",
                "Révision des protocoles de nettoyage",
                "Formation continue du personnel"
            ])
        else:
            recommendations.extend([
                "Maintenir les bonnes pratiques actuelles",
                "Inspection de routine selon calendrier normal"
            ])
        
        # Recommandations financières
        if financial_impact_pct > 15:
            recommendations.append("Considérer un financement pour les mesures correctives")
        
        if financial_results.get('fallback_data', False):
            recommendations.append("Vérifier les données financières avec le système FACE")
        
        return recommendations

def demo_integration_face():
    """Démonstration de l'intégration MAPAQ-FACE."""
    
    print("DÉMONSTRATION INTÉGRATION MAPAQ-FACE")
    print("="*50)
    
    # Initialisation
    integrator = MapaqFaceIntegrator()
    
    # Test de connexion FACE
    print("\n--- TEST CONNEXION FACE ---")
    connection_ok = integrator.face_client.test_connection()
    print(f"Connexion FACE: {'✓ OK' if connection_ok else '✗ ÉCHEC (mode fallback)'}")
    
    # Restaurant de test
    restaurant_test = {
        'id': 'REST_001',
        'nom': 'Restaurant Test Intégration',
        'theme': 'fast_food',
        'taille': 'grand',
        'zone': 'montreal',
        'historique_infractions': ['2024-01-15', '2023-11-20']
    }
    
    print(f"\n--- TRAITEMENT COMPLET ---")
    print(f"Restaurant: {restaurant_test['nom']}")
    
    # Traitement intégré
    results = integrator.process_restaurant_complete(restaurant_test)
    
    # Affichage des résultats
    print(f"\nRÉSULTATS INTÉGRÉS:")
    print(f"Score MAPAQ: {results['evaluation_mapaq']['score_risque']:.1f}/100")
    print(f"Catégorie: {results['evaluation_mapaq']['categorie_risque'].upper()}")
    print(f"Score composite: {results['score_composite']['score_composite']:.1f}/100")
    print(f"Impact financier: +{results['impact_financier_risque']['pourcentage_augmentation']:.1f}%")
    
    print(f"\nRECOMMANDATIONS INTÉGRÉES:")
    for i, rec in enumerate(results['recommandations_integrees'], 1):
        print(f"{i}. {rec}")
    
    return results

if __name__ == "__main__":
    demo_integration_face()
