"""
Moteur de Probabilités Conditionnelles pour MAPAQ
Calcul des probabilités d'infractions basées sur thème, taille, historique

Auteur: Mouhamed Thiaw
Date: 2025-01-17
Heures: 45-48 (Lundi-Mardi - Probability Engine)
"""

import math
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter

class ProbabilityEngine:
    """
    Moteur de calcul des probabilités conditionnelles pour prédiction des risques.
    Utilise les variables: thème, taille, historique pour calculer P(infraction|variables).
    """
    
    def __init__(self, modele_baseline=None):
        """
        Initialise le moteur de probabilités.
        
        Args:
            modele_baseline: Modèle baseline entraîné (optionnel)
        """
        self.modele = modele_baseline
        self.probabilites_conditionnelles = {}
        self.historique_calculs = []
        
        # Tables de probabilités pré-calculées
        self.prob_theme = {}
        self.prob_taille = {}
        self.prob_historique = {}
        self.prob_conjointes = {}
        
        # Initialisation des probabilités de base
        self._initialiser_probabilites_base()
        
        print("Moteur de probabilités conditionnelles initialisé")
    
    def _initialiser_probabilites_base(self):
        """Initialise les probabilités de base par catégorie."""
        
        # Probabilités par thème de restaurant
        self.prob_theme = {
            'restaurant': {
                'p_infraction': 0.35,
                'p_grave': 0.15,
                'facteur_saisonnier': 1.2
            },
            'fast_food': {
                'p_infraction': 0.45,
                'p_grave': 0.25,
                'facteur_saisonnier': 1.1
            },
            'cafe': {
                'p_infraction': 0.25,
                'p_grave': 0.08,
                'facteur_saisonnier': 0.9
            },
            'bar': {
                'p_infraction': 0.40,
                'p_grave': 0.20,
                'facteur_saisonnier': 1.3
            },
            'hotel': {
                'p_infraction': 0.30,
                'p_grave': 0.12,
                'facteur_saisonnier': 1.0
            }
        }
        
        # Probabilités par taille d'établissement
        self.prob_taille = {
            'petit': {
                'p_infraction': 0.40,
                'p_multiple': 0.20,
                'facteur_complexite': 0.8
            },
            'moyen': {
                'p_infraction': 0.35,
                'p_multiple': 0.30,
                'facteur_complexite': 1.0
            },
            'grand': {
                'p_infraction': 0.30,
                'p_multiple': 0.45,
                'facteur_complexite': 1.3
            },
            'enterprise': {
                'p_infraction': 0.25,
                'p_multiple': 0.55,
                'facteur_complexite': 1.5
            }
        }
        
        # Probabilités basées sur l'historique
        self.prob_historique = {
            'aucun': {'p_recidive': 0.15, 'facteur_vigilance': 1.0},
            'leger': {'p_recidive': 0.35, 'facteur_vigilance': 1.2},
            'modere': {'p_recidive': 0.55, 'facteur_vigilance': 1.5},
            'lourd': {'p_recidive': 0.75, 'facteur_vigilance': 2.0}
        }
    
    def calculate_infraction_probability(self, restaurant_features: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule la probabilité d'infractions pour un restaurant donné.
        
        Args:
            restaurant_features: Caractéristiques du restaurant
                - theme: Type de restaurant
                - taille: Taille de l'établissement
                - historique: Historique d'infractions
                - localisation: Zone géographique (optionnel)
                - saison: Période de l'année (optionnel)
        
        Returns:
            Dictionnaire avec les probabilités calculées
        """
        print(f"Calcul probabilités pour: {restaurant_features.get('nom', 'Restaurant')}")
        
        # Extraction des variables principales
        theme = restaurant_features.get('theme', 'restaurant').lower()
        taille = restaurant_features.get('taille', 'moyen').lower()
        historique = self._analyser_historique(restaurant_features.get('historique', []))
        
        # Calcul des probabilités conditionnelles
        prob_base = self._calculer_probabilite_base(theme, taille, historique)
        prob_conditionnelle = self._calculer_probabilite_conditionnelle(theme, taille, historique)
        prob_ajustee = self._ajuster_probabilites_contextuelles(
            prob_conditionnelle, restaurant_features
        )
        
        # Calcul des probabilités spécifiques
        resultats = {
            'probabilite_infraction': prob_ajustee,
            'probabilite_infraction_grave': self._calculer_prob_infraction_grave(theme, taille, historique),
            'probabilite_infractions_multiples': self._calculer_prob_infractions_multiples(theme, taille),
            'probabilite_recidive': self._calculer_prob_recidive(historique),
            'score_risque_global': self._calculer_score_risque_global(prob_ajustee, theme, taille, historique),
            'confiance_prediction': self._calculer_confiance_prediction(restaurant_features)
        }
        
        # Sauvegarde du calcul
        self._sauvegarder_calcul(restaurant_features, resultats)
        
        return resultats
    
    def _analyser_historique(self, historique: List[Dict]) -> str:
        """Analyse l'historique d'infractions et retourne une catégorie."""
        if not historique:
            return 'aucun'
        
        nb_infractions = len(historique)
        gravite_totale = 0
        
        for infraction in historique:
            # Estimation de gravité basée sur l'amende
            amende = infraction.get('amende', 0)
            if isinstance(amende, str):
                try:
                    amende = float(amende.replace('$', '').replace(',', ''))
                except:
                    amende = 0
            
            if amende > 2000:
                gravite_totale += 3
            elif amende > 500:
                gravite_totale += 2
            else:
                gravite_totale += 1
        
        # Catégorisation de l'historique
        if nb_infractions == 0:
            return 'aucun'
        elif nb_infractions <= 2 and gravite_totale <= 3:
            return 'leger'
        elif nb_infractions <= 5 and gravite_totale <= 8:
            return 'modere'
        else:
            return 'lourd'
    
    def _calculer_probabilite_base(self, theme: str, taille: str, historique: str) -> float:
        """Calcule la probabilité de base P(infraction)."""
        # Probabilité moyenne pondérée
        prob_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['p_infraction']
        prob_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['p_infraction']
        
        # Moyenne pondérée (thème 60%, taille 40%)
        prob_base = prob_theme * 0.6 + prob_taille * 0.4
        
        return prob_base
    
    def _calculer_probabilite_conditionnelle(self, theme: str, taille: str, historique: str) -> float:
        """
        Calcule P(infraction|theme, taille, historique) en utilisant la règle de Bayes.
        
        P(infraction|variables) = P(variables|infraction) * P(infraction) / P(variables)
        """
        # P(infraction) - probabilité a priori
        p_infraction = self._calculer_probabilite_base(theme, taille, historique)
        
        # P(variables|infraction) - vraisemblance
        p_variables_given_infraction = self._calculer_vraisemblance(theme, taille, historique, True)
        
        # P(variables) - évidence (normalisation)
        p_variables = self._calculer_evidence(theme, taille, historique)
        
        # Application de Bayes
        if p_variables > 0:
            prob_conditionnelle = (p_variables_given_infraction * p_infraction) / p_variables
        else:
            prob_conditionnelle = p_infraction
        
        return min(max(prob_conditionnelle, 0.01), 0.99)  # Borner entre 1% et 99%
    
    def _calculer_vraisemblance(self, theme: str, taille: str, historique: str, 
                               infraction_presente: bool) -> float:
        """Calcule la vraisemblance P(variables|infraction)."""
        
        # Facteurs de vraisemblance
        facteur_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['p_infraction']
        facteur_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['facteur_complexite']
        facteur_historique = self.prob_historique.get(historique, self.prob_historique['aucun'])['facteur_vigilance']
        
        if infraction_presente:
            # Si infraction présente, les facteurs augmentent la vraisemblance
            vraisemblance = facteur_theme * facteur_taille * facteur_historique / 3.0
        else:
            # Si pas d'infraction, les facteurs diminuent la vraisemblance
            vraisemblance = (1 - facteur_theme) * (2 - facteur_taille) * (2 - facteur_historique) / 6.0
        
        return min(max(vraisemblance, 0.01), 0.99)
    
    def _calculer_evidence(self, theme: str, taille: str, historique: str) -> float:
        """Calcule l'évidence P(variables) pour la normalisation."""
        
        # P(variables) = P(variables|infraction) * P(infraction) + P(variables|pas_infraction) * P(pas_infraction)
        p_infraction = self._calculer_probabilite_base(theme, taille, historique)
        p_pas_infraction = 1 - p_infraction
        
        p_var_given_inf = self._calculer_vraisemblance(theme, taille, historique, True)
        p_var_given_no_inf = self._calculer_vraisemblance(theme, taille, historique, False)
        
        evidence = (p_var_given_inf * p_infraction) + (p_var_given_no_inf * p_pas_infraction)
        
        return max(evidence, 0.01)  # Éviter division par 0
    
    def _ajuster_probabilites_contextuelles(self, prob_base: float, 
                                          restaurant_features: Dict) -> float:
        """Ajuste les probabilités selon le contexte (saison, localisation, etc.)."""
        
        prob_ajustee = prob_base
        
        # Ajustement saisonnier
        saison = restaurant_features.get('saison', 'printemps')
        facteur_saison = self._get_facteur_saisonnier(saison)
        prob_ajustee *= facteur_saison
        
        # Ajustement géographique
        localisation = restaurant_features.get('localisation', 'urbain')
        facteur_geo = self._get_facteur_geographique(localisation)
        prob_ajustee *= facteur_geo
        
        # Ajustement temporel (récence des données)
        age_donnees = restaurant_features.get('age_donnees_jours', 30)
        facteur_temporal = self._get_facteur_temporal(age_donnees)
        prob_ajustee *= facteur_temporal
        
        return min(max(prob_ajustee, 0.01), 0.99)
    
    def _get_facteur_saisonnier(self, saison: str) -> float:
        """Retourne le facteur d'ajustement saisonnier."""
        facteurs = {
            'hiver': 0.9,    # Moins d'activité
            'printemps': 1.0, # Normal
            'ete': 1.2,      # Plus d'activité, plus de risques
            'automne': 1.1   # Rentrée, activité élevée
        }
        return facteurs.get(saison.lower(), 1.0)
    
    def _get_facteur_geographique(self, localisation: str) -> float:
        """Retourne le facteur d'ajustement géographique."""
        facteurs = {
            'urbain_dense': 1.3,  # Plus de contrôles
            'urbain': 1.1,
            'periurbain': 1.0,
            'rural': 0.8          # Moins de contrôles
        }
        return facteurs.get(localisation.lower(), 1.0)
    
    def _get_facteur_temporal(self, age_jours: int) -> float:
        """Retourne le facteur d'ajustement temporel."""
        if age_jours <= 30:
            return 1.0      # Données récentes
        elif age_jours <= 90:
            return 0.95     # Légère dépréciation
        elif age_jours <= 180:
            return 0.9      # Dépréciation modérée
        else:
            return 0.8      # Données anciennes
    
    def _calculer_prob_infraction_grave(self, theme: str, taille: str, historique: str) -> float:
        """Calcule la probabilité d'infraction grave."""
        prob_grave_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['p_grave']
        
        # Ajustement selon la taille (plus grand = plus de risques graves)
        facteur_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['facteur_complexite']
        
        # Ajustement selon l'historique
        facteur_historique = self.prob_historique.get(historique, self.prob_historique['aucun'])['facteur_vigilance']
        
        prob_grave = prob_grave_theme * facteur_taille * (facteur_historique / 2.0)
        
        return min(max(prob_grave, 0.01), 0.8)
    
    def _calculer_prob_infractions_multiples(self, theme: str, taille: str) -> float:
        """Calcule la probabilité d'infractions multiples."""
        prob_multiple_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['p_multiple']
        
        # Ajustement selon le thème
        facteur_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['facteur_saisonnier']
        
        prob_multiple = prob_multiple_taille * (facteur_theme / 1.2)
        
        return min(max(prob_multiple, 0.05), 0.7)
    
    def _calculer_prob_recidive(self, historique: str) -> float:
        """Calcule la probabilité de récidive."""
        return self.prob_historique.get(historique, self.prob_historique['aucun'])['p_recidive']
    
    def _calculer_score_risque_global(self, prob_infraction: float, theme: str, 
                                    taille: str, historique: str) -> float:
        """Calcule un score de risque global (0-100)."""
        
        # Pondération des différents facteurs
        score_base = prob_infraction * 40  # 40% du score
        
        # Facteur thème
        facteur_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['p_infraction']
        score_theme = facteur_theme * 25  # 25% du score
        
        # Facteur taille
        facteur_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['facteur_complexite']
        score_taille = (facteur_taille - 1) * 20 + 15  # 20% du score
        
        # Facteur historique
        facteur_historique = self.prob_historique.get(historique, self.prob_historique['aucun'])['facteur_vigilance']
        score_historique = (facteur_historique - 1) * 15  # 15% du score
        
        score_global = score_base + score_theme + score_taille + score_historique
        
        return min(max(score_global, 0), 100)
    
    def _calculer_confiance_prediction(self, restaurant_features: Dict) -> float:
        """Calcule la confiance dans la prédiction."""
        confiance_base = 0.7
        
        # Plus de données = plus de confiance
        if restaurant_features.get('historique'):
            confiance_base += 0.15
        
        if restaurant_features.get('localisation'):
            confiance_base += 0.05
        
        if restaurant_features.get('age_donnees_jours', 100) <= 30:
            confiance_base += 0.1
        
        return min(confiance_base, 0.95)
    
    def _sauvegarder_calcul(self, features: Dict, resultats: Dict):
        """Sauvegarde le calcul dans l'historique."""
        calcul = {
            'timestamp': datetime.now().isoformat(),
            'restaurant': features.get('nom', 'Inconnu'),
            'features': features,
            'resultats': resultats
        }
        
        self.historique_calculs.append(calcul)
        
        # Garder seulement les 100 derniers calculs
        if len(self.historique_calculs) > 100:
            self.historique_calculs = self.historique_calculs[-100:]
    
    def analyser_tendances_probabilites(self) -> Dict[str, Any]:
        """Analyse les tendances dans les calculs de probabilités."""
        if not self.historique_calculs:
            return {'message': 'Aucun calcul disponible pour analyse'}
        
        # Statistiques par thème
        stats_theme = defaultdict(list)
        stats_taille = defaultdict(list)
        
        for calcul in self.historique_calculs:
            theme = calcul['features'].get('theme', 'inconnu')
            taille = calcul['features'].get('taille', 'inconnu')
            prob = calcul['resultats']['probabilite_infraction']
            
            stats_theme[theme].append(prob)
            stats_taille[taille].append(prob)
        
        # Calcul des moyennes
        moyennes_theme = {
            theme: sum(probs) / len(probs) 
            for theme, probs in stats_theme.items()
        }
        
        moyennes_taille = {
            taille: sum(probs) / len(probs) 
            for taille, probs in stats_taille.items()
        }
        
        return {
            'nb_calculs': len(self.historique_calculs),
            'moyennes_par_theme': moyennes_theme,
            'moyennes_par_taille': moyennes_taille,
            'derniere_analyse': datetime.now().isoformat()
        }
    
    def generer_rapport_probabilites(self) -> str:
        """Génère un rapport détaillé des probabilités."""
        rapport = []
        rapport.append("="*60)
        rapport.append("RAPPORT MOTEUR DE PROBABILITÉS CONDITIONNELLES")
        rapport.append("="*60)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rapport.append(f"Calculs effectués: {len(self.historique_calculs)}")
        
        # Analyse des tendances
        tendances = self.analyser_tendances_probabilites()
        
        if 'moyennes_par_theme' in tendances:
            rapport.append("\n" + "-"*40)
            rapport.append("PROBABILITÉS MOYENNES PAR THÈME")
            rapport.append("-"*40)
            
            for theme, moyenne in tendances['moyennes_par_theme'].items():
                rapport.append(f"{theme.capitalize():15}: {moyenne:.3f}")
            
            rapport.append("\n" + "-"*40)
            rapport.append("PROBABILITÉS MOYENNES PAR TAILLE")
            rapport.append("-"*40)
            
            for taille, moyenne in tendances['moyennes_par_taille'].items():
                rapport.append(f"{taille.capitalize():15}: {moyenne:.3f}")
        
        return "\n".join(rapport)

# === FONCTION DE DÉMONSTRATION ===

def demo_probability_engine():
    """Démonstration du moteur de probabilités conditionnelles."""
    print("DÉMONSTRATION MOTEUR DE PROBABILITÉS CONDITIONNELLES")
    print("="*55)
    
    # Initialisation
    engine = ProbabilityEngine()
    
    # Cas de test variés
    restaurants_test = [
        {
            'nom': 'Restaurant Italien Centre-ville',
            'theme': 'restaurant',
            'taille': 'moyen',
            'historique': [
                {'type': 'hygiene', 'amende': '500$'},
                {'type': 'temperature', 'amende': '300$'}
            ],
            'localisation': 'urbain_dense',
            'saison': 'ete'
        },
        {
            'nom': 'Fast Food Banlieue',
            'theme': 'fast_food',
            'taille': 'grand',
            'historique': [],
            'localisation': 'periurbain',
            'saison': 'hiver'
        },
        {
            'nom': 'Café Quartier',
            'theme': 'cafe',
            'taille': 'petit',
            'historique': [
                {'type': 'documentation', 'amende': '1500$'},
                {'type': 'equipement', 'amende': '2500$'},
                {'type': 'formation', 'amende': '800$'}
            ],
            'localisation': 'urbain',
            'saison': 'printemps'
        }
    ]
    
    # Calculs pour chaque restaurant
    resultats_globaux = []
    
    for restaurant in restaurants_test:
        print(f"\n--- ANALYSE: {restaurant['nom']} ---")
        resultats = engine.calculate_infraction_probability(restaurant)
        
        print(f"Probabilité infraction: {resultats['probabilite_infraction']:.3f}")
        print(f"Probabilité grave: {resultats['probabilite_infraction_grave']:.3f}")
        print(f"Score risque global: {resultats['score_risque_global']:.1f}/100")
        print(f"Confiance: {resultats['confiance_prediction']:.3f}")
        
        resultats_globaux.append(resultats)
    
    # Rapport final
    print("\n" + engine.generer_rapport_probabilites())
    
    return engine, resultats_globaux

if __name__ == "__main__":
    # Exécution de la démonstration
    engine, resultats = demo_probability_engine()
