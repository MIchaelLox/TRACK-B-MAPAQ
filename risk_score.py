
"""
Générateur de Scores de Risque MAPAQ - Algorithme Composite
Système de scoring avancé pour évaluation des risques sanitaires

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import logging

# Import des modules développés
from probability_engine_complet import ProbabilityEngine
from rule_adapter import RuleAdapter

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskScorer:
    """
    Générateur de scores de risque composite pour restaurants MAPAQ.
    Combine probabilités, historique, facteurs contextuels et règles réglementaires.
    """
    
    def __init__(self, probability_engine=None, rule_adapter=None):
        """
        Initialise le générateur de scores de risque.
        
        Args:
            probability_engine: Moteur de probabilités (optionnel)
            rule_adapter: Adaptateur de règles (optionnel)
        """
        self.probability_engine = probability_engine or ProbabilityEngine()
        self.rule_adapter = rule_adapter or RuleAdapter()
        
        # Configuration des poids pour l'algorithme composite
        self.composite_weights = {
            'probabilite_base': 0.35,      # Probabilité d'infraction de base
            'historique_infractions': 0.25, # Historique des infractions
            'facteurs_contextuels': 0.20,  # Contexte (saison, taille, etc.)
            'tendance_temporelle': 0.10,   # Évolution dans le temps
            'facteurs_reglementaires': 0.10 # Ajustements réglementaires
        }
        
        # Paramètres de scoring
        self.score_params = {
            'score_min': 0,
            'score_max': 100,
            'seuil_critique': 80,
            'seuil_eleve': 60,
            'seuil_moyen': 40,
            'facteur_amplification': 1.2,
            'facteur_attenuation': 0.8
        }
        
        logger.info("Générateur de scores de risque MAPAQ initialisé")
    
    def compute_score(self, restaurant_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule un score de risque composite (0-100) pour un restaurant.
        
        Args:
            restaurant_features: Caractéristiques du restaurant
            
        Returns:
            Dictionnaire avec score et détails
        """
        try:
            # 1. Calcul de la probabilité de base
            prob_results = self.probability_engine.calculate_infraction_probability(restaurant_features)
            probabilite_base = prob_results['probabilite_infraction']
            
            # 2. Analyse de l'historique des infractions
            score_historique = self._calculate_history_score(restaurant_features)
            
            # 3. Évaluation des facteurs contextuels
            score_contextuel = self._calculate_contextual_score(restaurant_features)
            
            # 4. Analyse de la tendance temporelle
            score_tendance = self._calculate_trend_score(restaurant_features)
            
            # 5. Application des ajustements réglementaires
            score_reglementaire = self._calculate_regulatory_score(restaurant_features)
            
            # 6. Calcul du score composite
            score_composite = (
                probabilite_base * self.composite_weights['probabilite_base'] +
                score_historique * self.composite_weights['historique_infractions'] +
                score_contextuel * self.composite_weights['facteurs_contextuels'] +
                score_tendance * self.composite_weights['tendance_temporelle'] +
                score_reglementaire * self.composite_weights['facteurs_reglementaires']
            )
            
            # 7. Normalisation et ajustements finaux
            score_final = self._normalize_and_adjust_score(score_composite, restaurant_features)
            
            # 8. Génération du rapport détaillé
            rapport_scoring = {
                'score_final': round(score_final, 1),
                'composantes': {
                    'probabilite_base': round(probabilite_base * 100, 1),
                    'score_historique': round(score_historique * 100, 1),
                    'score_contextuel': round(score_contextuel * 100, 1),
                    'score_tendance': round(score_tendance * 100, 1),
                    'score_reglementaire': round(score_reglementaire * 100, 1)
                },
                'poids_appliques': self.composite_weights,
                'facteurs_dominants': self._identify_dominant_factors(
                    probabilite_base, score_historique, score_contextuel, 
                    score_tendance, score_reglementaire
                ),
                'niveau_confiance': prob_results.get('confiance', 0.8),
                'recommandations': self._generate_recommendations(score_final, restaurant_features)
            }
            
            logger.info(f"Score calculé: {score_final:.1f}/100 pour {restaurant_features.get('nom', 'Restaurant')}")
            
            return rapport_scoring
            
        except Exception as e:
            logger.error(f"Erreur calcul score: {e}")
            return {
                'score_final': 50.0,
                'erreur': str(e),
                'composantes': {},
                'niveau_confiance': 0.0
            }
    
    def _calculate_history_score(self, restaurant_features: Dict[str, Any]) -> float:
        """Calcule le score basé sur l'historique des infractions."""
        
        historique = restaurant_features.get('historique_infractions', [])
        
        if not historique:
            return 0.2  # Score faible si pas d'historique
        
        # Analyse de la fréquence
        nb_infractions = len(historique)
        if nb_infractions >= 5:
            score_frequence = 0.9
        elif nb_infractions >= 3:
            score_frequence = 0.7
        elif nb_infractions >= 1:
            score_frequence = 0.5
        else:
            score_frequence = 0.2
        
        # Analyse de la récence
        try:
            dates_infractions = []
            for infraction in historique:
                if isinstance(infraction, str):
                    try:
                        date_infraction = datetime.strptime(infraction, '%Y-%m-%d')
                        dates_infractions.append(date_infraction)
                    except ValueError:
                        continue
            
            if dates_infractions:
                date_plus_recente = max(dates_infractions)
                jours_depuis = (datetime.now() - date_plus_recente).days
                
                if jours_depuis <= 30:
                    facteur_recence = 1.2
                elif jours_depuis <= 90:
                    facteur_recence = 1.0
                elif jours_depuis <= 365:
                    facteur_recence = 0.8
                else:
                    facteur_recence = 0.6
            else:
                facteur_recence = 0.8
                
        except Exception:
            facteur_recence = 0.8
        
        # Score historique composite
        score_historique = min(1.0, score_frequence * facteur_recence)
        
        return score_historique
    
    def _calculate_contextual_score(self, restaurant_features: Dict[str, Any]) -> float:
        """Calcule le score basé sur les facteurs contextuels."""
        
        # Facteur type d'établissement
        theme = restaurant_features.get('theme', 'restaurant').lower()
        facteurs_theme = {
            'fast_food': 0.8,
            'restaurant': 0.6,
            'bar': 0.5,
            'hotel': 0.4,
            'cafe': 0.3
        }
        score_theme = facteurs_theme.get(theme, 0.5)
        
        # Facteur taille
        taille = restaurant_features.get('taille', 'moyen').lower()
        facteurs_taille = {
            'grand': 0.8,
            'moyen': 0.6,
            'petit': 0.4
        }
        score_taille = facteurs_taille.get(taille, 0.6)
        
        # Facteur saisonnier
        mois_actuel = datetime.now().month
        if mois_actuel in [6, 7, 8]:  # Été
            facteur_saison = 0.8
        elif mois_actuel in [12, 1, 2]:  # Hiver
            facteur_saison = 0.5
        elif mois_actuel in [3, 4, 5]:  # Printemps
            facteur_saison = 0.6
        else:  # Automne
            facteur_saison = 0.7
        
        # Facteur géographique
        zone = restaurant_features.get('zone', 'montreal').lower()
        facteurs_zone = {
            'montreal': 0.7,
            'quebec': 0.6,
            'laval': 0.6,
            'gatineau': 0.5,
            'sherbrooke': 0.5
        }
        score_zone = facteurs_zone.get(zone, 0.6)
        
        # Score contextuel composite
        score_contextuel = (score_theme * 0.4 + score_taille * 0.3 + 
                           facteur_saison * 0.2 + score_zone * 0.1)
        
        return score_contextuel
    
    def _calculate_trend_score(self, restaurant_features: Dict[str, Any]) -> float:
        """Calcule le score basé sur la tendance temporelle."""
        
        historique = restaurant_features.get('historique_infractions', [])
        
        if len(historique) < 2:
            return 0.5  # Tendance neutre si pas assez de données
        
        try:
            # Analyse des dates d'infractions
            dates_infractions = []
            for infraction in historique:
                if isinstance(infraction, str):
                    try:
                        date_infraction = datetime.strptime(infraction, '%Y-%m-%d')
                        dates_infractions.append(date_infraction)
                    except ValueError:
                        continue
            
            if len(dates_infractions) < 2:
                return 0.5
            
            # Tri par date
            dates_infractions.sort()
            
            # Calcul de la tendance (infractions récentes vs anciennes)
            milieu = len(dates_infractions) // 2
            infractions_recentes = dates_infractions[milieu:]
            infractions_anciennes = dates_infractions[:milieu]
            
            # Calcul de la fréquence par période
            if infractions_recentes and infractions_anciennes:
                duree_recente = (max(infractions_recentes) - min(infractions_recentes)).days + 1
                duree_ancienne = (max(infractions_anciennes) - min(infractions_anciennes)).days + 1
                
                freq_recente = len(infractions_recentes) / max(duree_recente, 1) * 365
                freq_ancienne = len(infractions_anciennes) / max(duree_ancienne, 1) * 365
                
                if freq_recente > freq_ancienne * 1.5:
                    return 0.9  # Tendance à la hausse
                elif freq_recente < freq_ancienne * 0.5:
                    return 0.3  # Tendance à la baisse
                else:
                    return 0.6  # Tendance stable
            
        except Exception:
            pass
        
        return 0.5  # Tendance neutre par défaut
    
    def _calculate_regulatory_score(self, restaurant_features: Dict[str, Any]) -> float:
        """Calcule le score basé sur les ajustements réglementaires."""
        
        try:
            # Utilisation de l'adaptateur de règles
            probabilite_base = 0.5  # Probabilité de référence
            probabilite_ajustee = self.rule_adapter.get_adjusted_probability(
                probabilite_base, restaurant_features
            )
            
            # Conversion en score (facteur d'ajustement)
            facteur_ajustement = probabilite_ajustee / probabilite_base
            
            # Normalisation du score réglementaire
            if facteur_ajustement > 1.2:
                return 0.8  # Impact réglementaire élevé
            elif facteur_ajustement > 1.0:
                return 0.6  # Impact réglementaire modéré
            elif facteur_ajustement > 0.8:
                return 0.4  # Impact réglementaire faible
            else:
                return 0.2  # Impact réglementaire très faible
                
        except Exception:
            return 0.5  # Score neutre en cas d'erreur
    
    def _normalize_and_adjust_score(self, score_composite: float, 
                                  restaurant_features: Dict[str, Any]) -> float:
        """Normalise et ajuste le score final."""
        
        # Conversion en échelle 0-100
        score_normalise = score_composite * 100
        
        # Application des ajustements finaux
        theme = restaurant_features.get('theme', 'restaurant').lower()
        
        # Amplification pour certains types à risque
        if theme in ['fast_food', 'bar']:
            score_normalise *= self.score_params['facteur_amplification']
        
        # Atténuation pour types moins risqués
        elif theme in ['cafe', 'hotel']:
            score_normalise *= self.score_params['facteur_attenuation']
        
        # Limitation dans la plage valide
        score_final = max(self.score_params['score_min'], 
                         min(self.score_params['score_max'], score_normalise))
        
        return score_final
    
    def _identify_dominant_factors(self, prob_base: float, hist: float, 
                                 context: float, trend: float, reg: float) -> List[str]:
        """Identifie les facteurs dominants dans le calcul du score."""
        
        facteurs = {
            'probabilite_base': prob_base * self.composite_weights['probabilite_base'],
            'historique': hist * self.composite_weights['historique_infractions'],
            'contexte': context * self.composite_weights['facteurs_contextuels'],
            'tendance': trend * self.composite_weights['tendance_temporelle'],
            'reglementaire': reg * self.composite_weights['facteurs_reglementaires']
        }
        
        # Tri par contribution décroissante
        facteurs_tries = sorted(facteurs.items(), key=lambda x: x[1], reverse=True)
        
        # Retour des 2 facteurs dominants
        return [facteur[0] for facteur in facteurs_tries[:2]]
    
    def _generate_recommendations(self, score: float, 
                                restaurant_features: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur le score."""
        
        recommendations = []
        
        if score >= self.score_params['seuil_critique']:
            recommendations.extend([
                "Inspection prioritaire recommandée dans les 7 jours",
                "Surveillance renforcée nécessaire",
                "Vérification des mesures correctives précédentes"
            ])
        elif score >= self.score_params['seuil_eleve']:
            recommendations.extend([
                "Inspection recommandée dans les 30 jours",
                "Suivi des infractions antérieures",
                "Formation du personnel suggérée"
            ])
        elif score >= self.score_params['seuil_moyen']:
            recommendations.extend([
                "Inspection de routine dans les 90 jours",
                "Sensibilisation aux bonnes pratiques"
            ])
        else:
            recommendations.extend([
                "Inspection de routine selon calendrier normal",
                "Maintien des bonnes pratiques"
            ])
        
        # Recommandations spécifiques au type
        theme = restaurant_features.get('theme', 'restaurant').lower()
        if theme == 'fast_food':
            recommendations.append("Attention particulière aux chaînes de froid")
        elif theme == 'restaurant':
            recommendations.append("Vérification des procédures HACCP")
        elif theme == 'bar':
            recommendations.append("Contrôle de la salubrité des surfaces")
        
        return recommendations
    
    def compute_batch_scores(self, restaurants_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les scores pour une liste de restaurants.
        
        Args:
            restaurants_list: Liste des restaurants à évaluer
            
        Returns:
            Résultats groupés avec statistiques
        """
        try:
            resultats = []
            scores = []
            
            for restaurant in restaurants_list:
                resultat = self.compute_score(restaurant)
                resultats.append({
                    'restaurant': restaurant.get('nom', f"Restaurant_{len(resultats)}"),
                    'score': resultat['score_final'],
                    'niveau_risque': self._categorize_risk_level(resultat['score_final']),
                    'facteurs_dominants': resultat.get('facteurs_dominants', []),
                    'confiance': resultat.get('niveau_confiance', 0.8)
                })
                scores.append(resultat['score_final'])
            
            # Calcul des statistiques globales
            if scores:
                statistiques = {
                    'nb_restaurants': len(scores),
                    'score_moyen': statistics.mean(scores),
                    'score_median': statistics.median(scores),
                    'score_min': min(scores),
                    'score_max': max(scores),
                    'ecart_type': statistics.stdev(scores) if len(scores) > 1 else 0
                }
                
                # Distribution par niveau de risque
                distribution = {'critique': 0, 'eleve': 0, 'moyen': 0, 'faible': 0}
                for score in scores:
                    niveau = self._categorize_risk_level(score)
                    distribution[niveau] += 1
            else:
                statistiques = {}
                distribution = {}
            
            return {
                'resultats_detailles': resultats,
                'statistiques_globales': statistiques,
                'distribution_risques': distribution,
                'restaurants_prioritaires': [r for r in resultats if r['score'] >= 80]
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul batch: {e}")
            return {'erreur': str(e)}
    
    def _categorize_risk_level(self, score: float) -> str:
        """Catégorise le niveau de risque selon le score."""
        
        if score >= self.score_params['seuil_critique']:
            return 'critique'
        elif score >= self.score_params['seuil_eleve']:
            return 'eleve'
        elif score >= self.score_params['seuil_moyen']:
            return 'moyen'
        else:
            return 'faible'
    
    def generate_scoring_report(self, results: Dict[str, Any]) -> str:
        """Génère un rapport de scoring détaillé."""
        
        if 'erreur' in results:
            return f"Erreur dans le calcul: {results['erreur']}"
        
        rapport = []
        rapport.append("="*60)
        rapport.append("RAPPORT DE SCORING RISQUE MAPAQ")
        rapport.append("="*60)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'score_final' in results:
            # Rapport individuel
            rapport.append(f"\nScore final: {results['score_final']}/100")
            rapport.append(f"Niveau de risque: {self._categorize_risk_level(results['score_final']).upper()}")
            rapport.append(f"Confiance: {results.get('niveau_confiance', 0.8):.1%}")
            
            if 'composantes' in results:
                rapport.append("\n--- COMPOSANTES DU SCORE ---")
                for comp, valeur in results['composantes'].items():
                    rapport.append(f"{comp}: {valeur}")
            
            if 'facteurs_dominants' in results:
                rapport.append(f"\nFacteurs dominants: {', '.join(results['facteurs_dominants'])}")
            
            if 'recommandations' in results:
                rapport.append("\n--- RECOMMANDATIONS ---")
                for rec in results['recommandations']:
                    rapport.append(f"• {rec}")
        
        elif 'statistiques_globales' in results:
            # Rapport batch
            stats = results['statistiques_globales']
            rapport.append(f"\nNombre de restaurants évalués: {stats.get('nb_restaurants', 0)}")
            rapport.append(f"Score moyen: {stats.get('score_moyen', 0):.1f}")
            rapport.append(f"Score médian: {stats.get('score_median', 0):.1f}")
            rapport.append(f"Plage: {stats.get('score_min', 0):.1f} - {stats.get('score_max', 0):.1f}")
            
            if 'distribution_risques' in results:
                rapport.append("\n--- DISTRIBUTION DES RISQUES ---")
                for niveau, count in results['distribution_risques'].items():
                    pourcentage = (count / stats.get('nb_restaurants', 1)) * 100
                    rapport.append(f"{niveau.capitalize()}: {count} ({pourcentage:.1f}%)")
        
        return "\n".join(rapport)

# === FONCTION DE DÉMONSTRATION ===

def demo_risk_scorer():
    """Démonstration complète du générateur de scores de risque."""
    print("DÉMONSTRATION GÉNÉRATEUR DE SCORES DE RISQUE")
    print("="*55)
    
    # Initialisation
    scorer = RiskScorer()
    
    # Test sur un restaurant individuel
    print("\n--- TEST RESTAURANT INDIVIDUEL ---")
    restaurant_test = {
        'nom': 'Fast Food Downtown',
        'theme': 'fast_food',
        'taille': 'grand',
        'zone': 'montreal',
        'historique_infractions': ['2024-01-15', '2023-08-20', '2023-03-10']
    }
    
    resultat = scorer.compute_score(restaurant_test)
    print(scorer.generate_scoring_report(resultat))
    
    # Test sur un batch de restaurants
    print("\n\n--- TEST BATCH RESTAURANTS ---")
    restaurants_batch = [
        {
            'nom': 'Restaurant Italien',
            'theme': 'restaurant',
            'taille': 'moyen',
            'zone': 'montreal',
            'historique_infractions': ['2023-12-01']
        },
        {
            'nom': 'Café Quartier',
            'theme': 'cafe',
            'taille': 'petit',
            'zone': 'quebec',
            'historique_infractions': []
        },
        {
            'nom': 'Bar Sports',
            'theme': 'bar',
            'taille': 'grand',
            'zone': 'laval',
            'historique_infractions': ['2024-02-01', '2023-11-15', '2023-09-20', '2023-06-10']
        }
    ]
    
    resultats_batch = scorer.compute_batch_scores(restaurants_batch)
    print(scorer.generate_scoring_report(resultats_batch))
    
    return scorer

if __name__ == "__main__":
    # Exécution de la démonstration
    scorer = demo_risk_scorer()
