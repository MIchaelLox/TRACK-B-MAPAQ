
"""
Catégorisateur de Risques MAPAQ - Seuils Dynamiques
Système de catégorisation avancé avec seuils adaptatifs

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskCategorizer:
    """
    Catégorisateur de risques avec seuils dynamiques pour restaurants MAPAQ.
    Adapte les seuils selon le contexte et l'historique des données.
    """
    
    def __init__(self):
        """Initialise le catégorisateur de risques."""
        
        # Seuils de base (statiques)
        self.base_thresholds = {
            'faible': {'min': 0, 'max': 40},
            'moyen': {'min': 40, 'max': 60},
            'eleve': {'min': 60, 'max': 80},
            'critique': {'min': 80, 'max': 100}
        }
        
        # Seuils dynamiques (ajustés selon contexte)
        self.dynamic_thresholds = self.base_thresholds.copy()
        
        # Historique des scores pour calibration
        self.score_history = []
        self.calibration_data = {
            'mean': 50.0,
            'std': 20.0,
            'percentiles': {'25': 35, '50': 50, '75': 65, '90': 80}
        }
        
        # Configuration des ajustements contextuels
        self.context_adjustments = {
            'saison_ete': {'factor': 1.1, 'shift': 5},
            'zone_urbaine': {'factor': 1.05, 'shift': 2},
            'type_fast_food': {'factor': 1.15, 'shift': 8},
            'historique_recent': {'factor': 1.2, 'shift': 10}
        }
        
        logger.info("Catégorisateur de risques MAPAQ initialisé")
    
    def categorize(self, risk_score: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Catégorise un restaurant selon son score de risque.
        
        Args:
            risk_score: Score de risque (0-100)
            context: Contexte pour ajustements dynamiques
            
        Returns:
            Dictionnaire avec catégorie et détails
        """
        try:
            # Ajout du score à l'historique
            self.score_history.append(risk_score)
            
            # Mise à jour des seuils dynamiques si nécessaire
            if len(self.score_history) % 10 == 0:  # Recalibration tous les 10 scores
                self._update_dynamic_thresholds()
            
            # Application des ajustements contextuels
            adjusted_score = self._apply_contextual_adjustments(risk_score, context or {})
            
            # Détermination de la catégorie
            category = self._determine_category(adjusted_score)
            
            # Calcul de la confiance de catégorisation
            confidence = self._calculate_categorization_confidence(adjusted_score, category)
            
            # Génération des détails
            result = {
                'score_original': risk_score,
                'score_ajuste': round(adjusted_score, 1),
                'categorie': category,
                'niveau_confiance': confidence,
                'seuils_utilises': self.dynamic_thresholds[category],
                'ajustements_appliques': self._get_applied_adjustments(context or {}),
                'recommandations_action': self._generate_action_recommendations(category, adjusted_score),
                'priorite_inspection': self._calculate_inspection_priority(category, adjusted_score),
                'delai_recommande': self._calculate_recommended_delay(category)
            }
            
            logger.info(f"Catégorisation: {risk_score:.1f} → {category.upper()} (confiance: {confidence:.1%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur catégorisation: {e}")
            return {
                'score_original': risk_score,
                'categorie': 'moyen',
                'niveau_confiance': 0.5,
                'erreur': str(e)
            }
    
    def _apply_contextual_adjustments(self, score: float, context: Dict[str, Any]) -> float:
        """Applique les ajustements contextuels au score."""
        
        adjusted_score = score
        
        # Ajustement saisonnier
        mois_actuel = datetime.now().month
        if mois_actuel in [6, 7, 8]:  # Été
            adjustment = self.context_adjustments['saison_ete']
            adjusted_score = adjusted_score * adjustment['factor'] + adjustment['shift']
        
        # Ajustement géographique
        zone = context.get('zone', '').lower()
        if zone in ['montreal', 'quebec', 'laval']:
            adjustment = self.context_adjustments['zone_urbaine']
            adjusted_score = adjusted_score * adjustment['factor'] + adjustment['shift']
        
        # Ajustement type d'établissement
        theme = context.get('theme', '').lower()
        if theme == 'fast_food':
            adjustment = self.context_adjustments['type_fast_food']
            adjusted_score = adjusted_score * adjustment['factor'] + adjustment['shift']
        
        # Ajustement historique récent
        historique = context.get('historique_infractions', [])
        if historique:
            try:
                dates_recentes = [d for d in historique if isinstance(d, str)]
                if dates_recentes:
                    date_plus_recente = max(dates_recentes)
                    date_infraction = datetime.strptime(date_plus_recente, '%Y-%m-%d')
                    jours_depuis = (datetime.now() - date_infraction).days
                    
                    if jours_depuis <= 90:  # Infraction récente
                        adjustment = self.context_adjustments['historique_recent']
                        adjusted_score = adjusted_score * adjustment['factor'] + adjustment['shift']
            except:
                pass
        
        # Limitation dans la plage valide
        return max(0, min(100, adjusted_score))
    
    def _determine_category(self, score: float) -> str:
        """Détermine la catégorie selon le score ajusté."""
        
        for category, thresholds in self.dynamic_thresholds.items():
            if thresholds['min'] <= score < thresholds['max']:
                return category
        
        # Cas limite (score = 100)
        if score >= 80:
            return 'critique'
        
        return 'moyen'  # Défaut
    
    def _calculate_categorization_confidence(self, score: float, category: str) -> float:
        """Calcule la confiance de la catégorisation."""
        
        thresholds = self.dynamic_thresholds[category]
        range_size = thresholds['max'] - thresholds['min']
        
        if range_size == 0:
            return 1.0
        
        # Distance aux bornes
        dist_min = abs(score - thresholds['min'])
        dist_max = abs(score - thresholds['max'])
        min_dist_to_border = min(dist_min, dist_max)
        
        # Confiance basée sur la position dans la plage
        confidence = min_dist_to_border / (range_size / 2)
        confidence = max(0.5, min(1.0, confidence))  # Entre 50% et 100%
        
        return confidence
    
    def _update_dynamic_thresholds(self):
        """Met à jour les seuils dynamiques basés sur l'historique."""
        
        if len(self.score_history) < 10:
            return
        
        # Calcul des statistiques récentes
        recent_scores = self.score_history[-50:]  # 50 derniers scores
        
        self.calibration_data['mean'] = statistics.mean(recent_scores)
        self.calibration_data['std'] = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 20.0
        
        # Calcul des percentiles
        sorted_scores = sorted(recent_scores)
        n = len(sorted_scores)
        
        self.calibration_data['percentiles'] = {
            '25': sorted_scores[int(n * 0.25)],
            '50': sorted_scores[int(n * 0.50)],
            '75': sorted_scores[int(n * 0.75)],
            '90': sorted_scores[int(n * 0.90)]
        }
        
        # Ajustement des seuils dynamiques
        p25, p50, p75, p90 = (self.calibration_data['percentiles'][k] for k in ['25', '50', '75', '90'])
        
        self.dynamic_thresholds = {
            'faible': {'min': 0, 'max': max(35, p25)},
            'moyen': {'min': max(35, p25), 'max': max(55, p75)},
            'eleve': {'min': max(55, p75), 'max': max(75, p90)},
            'critique': {'min': max(75, p90), 'max': 100}
        }
        
        logger.info(f"Seuils dynamiques mis à jour: P25={p25:.1f}, P75={p75:.1f}, P90={p90:.1f}")
    
    def _get_applied_adjustments(self, context: Dict[str, Any]) -> List[str]:
        """Retourne la liste des ajustements appliqués."""
        
        adjustments = []
        
        # Vérification saisonnière
        mois_actuel = datetime.now().month
        if mois_actuel in [6, 7, 8]:
            adjustments.append("Ajustement saisonnier été (+10%)")
        
        # Vérification géographique
        zone = context.get('zone', '').lower()
        if zone in ['montreal', 'quebec', 'laval']:
            adjustments.append("Ajustement zone urbaine (+5%)")
        
        # Vérification type
        theme = context.get('theme', '').lower()
        if theme == 'fast_food':
            adjustments.append("Ajustement fast-food (+15%)")
        
        # Vérification historique
        historique = context.get('historique_infractions', [])
        if historique:
            try:
                dates_recentes = [d for d in historique if isinstance(d, str)]
                if dates_recentes:
                    date_plus_recente = max(dates_recentes)
                    date_infraction = datetime.strptime(date_plus_recente, '%Y-%m-%d')
                    jours_depuis = (datetime.now() - date_infraction).days
                    
                    if jours_depuis <= 90:
                        adjustments.append("Ajustement historique récent (+20%)")
            except:
                pass
        
        return adjustments if adjustments else ["Aucun ajustement contextuel"]
    
    def _generate_action_recommendations(self, category: str, score: float) -> List[str]:
        """Génère des recommandations d'action selon la catégorie."""
        
        recommendations = {
            'critique': [
                "INSPECTION IMMÉDIATE REQUISE",
                "Fermeture temporaire possible",
                "Suivi quotidien jusqu'à conformité",
                "Audit complet des procédures"
            ],
            'eleve': [
                "Inspection prioritaire dans 7-14 jours",
                "Surveillance renforcée",
                "Formation obligatoire du personnel",
                "Plan de mise en conformité exigé"
            ],
            'moyen': [
                "Inspection programmée dans 30-60 jours",
                "Sensibilisation aux bonnes pratiques",
                "Vérification des mesures préventives",
                "Suivi des améliorations"
            ],
            'faible': [
                "Inspection de routine selon calendrier",
                "Maintien des bonnes pratiques",
                "Reconnaissance des efforts",
                "Partage des meilleures pratiques"
            ]
        }
        
        return recommendations.get(category, recommendations['moyen'])
    
    def _calculate_inspection_priority(self, category: str, score: float) -> int:
        """Calcule la priorité d'inspection (1-10, 10 = max priorité)."""
        
        priority_map = {
            'critique': 10,
            'eleve': 7,
            'moyen': 4,
            'faible': 2
        }
        
        base_priority = priority_map.get(category, 5)
        
        # Ajustement fin selon le score exact
        if category == 'critique' and score >= 90:
            return 10
        elif category == 'eleve' and score >= 70:
            return 8
        elif category == 'moyen' and score >= 50:
            return 5
        
        return base_priority
    
    def _calculate_recommended_delay(self, category: str) -> str:
        """Calcule le délai recommandé pour l'inspection."""
        
        delays = {
            'critique': "Immédiat (0-3 jours)",
            'eleve': "Urgent (7-14 jours)",
            'moyen': "Programmé (30-60 jours)",
            'faible': "Routine (90-180 jours)"
        }
        
        return delays.get(category, "Programmé (30-60 jours)")
    
    def categorize_batch(self, scores_with_context: List[Tuple[float, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Catégorise un lot de restaurants.
        
        Args:
            scores_with_context: Liste de tuples (score, contexte)
            
        Returns:
            Résultats groupés avec statistiques
        """
        try:
            results = []
            categories_count = defaultdict(int)
            priorities = []
            
            for i, (score, context) in enumerate(scores_with_context):
                result = self.categorize(score, context)
                result['restaurant_id'] = context.get('nom', f"Restaurant_{i}")
                results.append(result)
                
                categories_count[result['categorie']] += 1
                priorities.append(result['priorite_inspection'])
            
            # Statistiques globales
            total_restaurants = len(results)
            
            return {
                'resultats_detailles': results,
                'statistiques': {
                    'total_restaurants': total_restaurants,
                    'distribution_categories': dict(categories_count),
                    'pourcentages': {cat: (count/total_restaurants)*100 
                                   for cat, count in categories_count.items()},
                    'priorite_moyenne': statistics.mean(priorities) if priorities else 0,
                    'restaurants_critiques': categories_count['critique'],
                    'restaurants_prioritaires': categories_count['critique'] + categories_count['eleve']
                },
                'seuils_dynamiques_actuels': self.dynamic_thresholds,
                'calibration_actuelle': self.calibration_data
            }
            
        except Exception as e:
            logger.error(f"Erreur catégorisation batch: {e}")
            return {'erreur': str(e)}
    
    def generate_categorization_report(self, results: Dict[str, Any]) -> str:
        """Génère un rapport de catégorisation détaillé."""
        
        if 'erreur' in results:
            return f"Erreur dans la catégorisation: {results['erreur']}"
        
        rapport = []
        rapport.append("="*60)
        rapport.append("RAPPORT DE CATÉGORISATION RISQUES MAPAQ")
        rapport.append("="*60)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'categorie' in results:
            # Rapport individuel
            rapport.append(f"\nScore original: {results['score_original']}")
            rapport.append(f"Score ajusté: {results['score_ajuste']}")
            rapport.append(f"Catégorie: {results['categorie'].upper()}")
            rapport.append(f"Confiance: {results['niveau_confiance']:.1%}")
            rapport.append(f"Priorité inspection: {results['priorite_inspection']}/10")
            rapport.append(f"Délai recommandé: {results['delai_recommande']}")
            
            rapport.append("\n--- AJUSTEMENTS APPLIQUÉS ---")
            for adj in results['ajustements_appliques']:
                rapport.append(f"• {adj}")
            
            rapport.append("\n--- RECOMMANDATIONS D'ACTION ---")
            for rec in results['recommandations_action']:
                rapport.append(f"• {rec}")
        
        elif 'statistiques' in results:
            # Rapport batch
            stats = results['statistiques']
            rapport.append(f"\nNombre total de restaurants: {stats['total_restaurants']}")
            
            rapport.append("\n--- DISTRIBUTION DES CATÉGORIES ---")
            for cat, count in stats['distribution_categories'].items():
                pct = stats['pourcentages'][cat]
                rapport.append(f"{cat.capitalize()}: {count} ({pct:.1f}%)")
            
            rapport.append(f"\nPriorité moyenne: {stats['priorite_moyenne']:.1f}/10")
            rapport.append(f"Restaurants critiques: {stats['restaurants_critiques']}")
            rapport.append(f"Restaurants prioritaires: {stats['restaurants_prioritaires']}")
        
        return "\n".join(rapport)

# === FONCTION DE DÉMONSTRATION ===

def demo_risk_categorizer():
    """Démonstration complète du catégorisateur de risques."""
    print("DÉMONSTRATION CATÉGORISATEUR DE RISQUES")
    print("="*50)
    
    # Initialisation
    categorizer = RiskCategorizer()
    
    # Test catégorisation individuelle
    print("\n--- TEST CATÉGORISATION INDIVIDUELLE ---")
    
    test_cases = [
        (85.5, {'nom': 'Fast Food Critique', 'theme': 'fast_food', 'zone': 'montreal', 
                'historique_infractions': ['2024-01-15']}),
        (72.3, {'nom': 'Restaurant Élevé', 'theme': 'restaurant', 'zone': 'quebec'}),
        (45.8, {'nom': 'Café Moyen', 'theme': 'cafe', 'zone': 'sherbrooke'}),
        (25.2, {'nom': 'Hotel Faible', 'theme': 'hotel', 'zone': 'gatineau'})
    ]
    
    for score, context in test_cases:
        result = categorizer.categorize(score, context)
        print(f"\n{context['nom']}: {score} -> {result['categorie'].upper()} "
              f"(confiance: {result['niveau_confiance']:.1%})")
    
    # Test catégorisation batch
    print("\n\n--- TEST CATÉGORISATION BATCH ---")
    batch_results = categorizer.categorize_batch(test_cases)
    print(categorizer.generate_categorization_report(batch_results))
    
    return categorizer

if __name__ == "__main__":
    # Exécution de la démonstration
    categorizer = demo_risk_categorizer()
