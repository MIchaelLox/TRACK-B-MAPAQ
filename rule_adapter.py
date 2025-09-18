
"""
Adaptateur de Règles MAPAQ - Gestion des Changements Réglementaires
Système d'adaptation dynamique des règles et pondérations temporelles

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleAdapter:
    """
    Adaptateur de règles pour gérer les changements réglementaires MAPAQ.
    Applique des pondérations temporelles et adapte les modèles aux nouvelles règles.
    """
    
    def __init__(self, base_model=None):
        """
        Initialise l'adaptateur de règles.
        
        Args:
            base_model: Modèle de base à adapter (optionnel)
        """
        self.base_model = base_model
        self.rules_history = []
        self.current_rules = {}
        self.temporal_weights = {}
        self.effective_dates = {}
        
        # Initialisation des règles par défaut
        self._initialize_default_rules()
        
        logger.info("Adaptateur de règles MAPAQ initialisé")
    
    def _initialize_default_rules(self):
        """Initialise les règles réglementaires par défaut."""
        
        # Règles de base MAPAQ (version 2024)
        self.current_rules = {
            'version': '2024.1',
            'date_effective': '2024-01-01',
            'categories_infractions': {
                'critique': {
                    'poids': 3.0,
                    'seuil_fermeture': 0.8,
                    'delai_correction': 24  # heures
                },
                'majeure': {
                    'poids': 2.0,
                    'seuil_fermeture': 0.6,
                    'delai_correction': 72  # heures
                },
                'mineure': {
                    'poids': 1.0,
                    'seuil_fermeture': 0.3,
                    'delai_correction': 168  # heures (7 jours)
                }
            },
            'facteurs_risque': {
                'historique_infractions': {
                    'poids_base': 0.4,
                    'decroissance_temporelle': 0.1  # par mois
                },
                'type_etablissement': {
                    'restaurant': 1.0,
                    'fast_food': 1.2,
                    'hotel': 0.8,
                    'cafe': 0.6,
                    'bar': 0.9
                },
                'taille_etablissement': {
                    'petit': 0.8,
                    'moyen': 1.0,
                    'grand': 1.3
                },
                'saison': {
                    'ete': 1.2,  # Juin-Août
                    'hiver': 0.9,  # Décembre-Février
                    'printemps': 1.0,  # Mars-Mai
                    'automne': 1.1   # Septembre-Novembre
                }
            },
            'seuils_categorisation': {
                'faible': 0.3,
                'moyen': 0.6,
                'eleve': 0.8
            }
        }
        
        # Historique des changements réglementaires
        self.rules_history = [
            {
                'version': '2023.2',
                'date_effective': '2023-07-01',
                'changements': ['Nouveau seuil fast_food', 'Ajout catégorie critique'],
                'impact': 'majeur'
            },
            {
                'version': '2024.1',
                'date_effective': '2024-01-01',
                'changements': ['Révision pondérations saisonnières', 'Nouveaux délais correction'],
                'impact': 'modéré'
            }
        ]
    
    def apply_time_based_weights(self, effective_date: str, current_date: str = None) -> Dict[str, float]:
        """
        Applique des pondérations basées sur la date effective des règles.
        
        Args:
            effective_date: Date d'entrée en vigueur (format YYYY-MM-DD)
            current_date: Date actuelle (défaut: aujourd'hui)
            
        Returns:
            Dictionnaire des pondérations temporelles
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            date_effective = datetime.strptime(effective_date, '%Y-%m-%d')
            date_courante = datetime.strptime(current_date, '%Y-%m-%d')
            
            # Calcul de la différence en jours
            delta_jours = (date_courante - date_effective).days
            
            # Fonction de pondération temporelle
            if delta_jours < 0:
                # Règles futures : pondération réduite
                poids_temporel = 0.5
            elif delta_jours <= 30:
                # Règles récentes : pondération maximale
                poids_temporel = 1.0
            elif delta_jours <= 90:
                # Règles de 1-3 mois : pondération décroissante
                poids_temporel = 1.0 - (delta_jours - 30) * 0.01
            else:
                # Règles anciennes : pondération minimale
                poids_temporel = max(0.7, 1.0 - delta_jours * 0.001)
            
            # Application aux différentes catégories
            ponderation_temporelle = {
                'facteur_global': poids_temporel,
                'infractions_critiques': poids_temporel * 1.2,
                'infractions_majeures': poids_temporel * 1.0,
                'infractions_mineures': poids_temporel * 0.8,
                'historique_recent': min(1.0, poids_temporel * 1.5),
                'saisonnalite': poids_temporel * 0.9
            }
            
            self.temporal_weights = ponderation_temporelle
            
            logger.info(f"Pondérations temporelles appliquées pour {effective_date}")
            logger.info(f"Facteur global: {poids_temporel:.3f}")
            
            return ponderation_temporelle
            
        except ValueError as e:
            logger.error(f"Erreur format date: {e}")
            return {'facteur_global': 1.0}
    
    def update_rules(self, new_regulation_data: Dict[str, Any]) -> bool:
        """
        Met à jour les règles avec de nouvelles réglementations.
        
        Args:
            new_regulation_data: Nouvelles données réglementaires
            
        Returns:
            True si mise à jour réussie, False sinon
        """
        try:
            # Sauvegarde des règles actuelles
            old_rules = self.current_rules.copy()
            
            # Validation des nouvelles règles
            if not self._validate_regulation_data(new_regulation_data):
                logger.error("Données réglementaires invalides")
                return False
            
            # Mise à jour progressive
            if 'categories_infractions' in new_regulation_data:
                self._update_infraction_categories(new_regulation_data['categories_infractions'])
            
            if 'facteurs_risque' in new_regulation_data:
                self._update_risk_factors(new_regulation_data['facteurs_risque'])
            
            if 'seuils_categorisation' in new_regulation_data:
                self._update_categorization_thresholds(new_regulation_data['seuils_categorisation'])
            
            # Mise à jour des métadonnées
            self.current_rules['version'] = new_regulation_data.get('version', 'custom')
            self.current_rules['date_effective'] = new_regulation_data.get('date_effective', 
                                                                         datetime.now().strftime('%Y-%m-%d'))
            
            # Ajout à l'historique
            self.rules_history.append({
                'version': self.current_rules['version'],
                'date_effective': self.current_rules['date_effective'],
                'changements': new_regulation_data.get('changements', ['Mise à jour personnalisée']),
                'impact': new_regulation_data.get('impact', 'modéré'),
                'regles_precedentes': old_rules['version']
            })
            
            # Application des pondérations temporelles
            self.apply_time_based_weights(self.current_rules['date_effective'])
            
            logger.info(f"Règles mises à jour vers version {self.current_rules['version']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour règles: {e}")
            return False
    
    def _validate_regulation_data(self, data: Dict[str, Any]) -> bool:
        """Valide la structure des données réglementaires."""
        
        required_fields = ['version', 'date_effective']
        
        # Vérification des champs obligatoires
        for field in required_fields:
            if field not in data:
                logger.warning(f"Champ manquant: {field}")
                return False
        
        # Validation du format de date
        try:
            datetime.strptime(data['date_effective'], '%Y-%m-%d')
        except ValueError:
            logger.error("Format de date invalide")
            return False
        
        return True
    
    def _update_infraction_categories(self, new_categories: Dict[str, Any]):
        """Met à jour les catégories d'infractions."""
        
        for categorie, params in new_categories.items():
            if categorie in self.current_rules['categories_infractions']:
                self.current_rules['categories_infractions'][categorie].update(params)
            else:
                self.current_rules['categories_infractions'][categorie] = params
        
        logger.info(f"Catégories d'infractions mises à jour: {list(new_categories.keys())}")
    
    def _update_risk_factors(self, new_factors: Dict[str, Any]):
        """Met à jour les facteurs de risque."""
        
        for facteur, params in new_factors.items():
            if facteur in self.current_rules['facteurs_risque']:
                if isinstance(params, dict) and isinstance(self.current_rules['facteurs_risque'][facteur], dict):
                    self.current_rules['facteurs_risque'][facteur].update(params)
                else:
                    self.current_rules['facteurs_risque'][facteur] = params
            else:
                self.current_rules['facteurs_risque'][facteur] = params
        
        logger.info(f"Facteurs de risque mis à jour: {list(new_factors.keys())}")
    
    def _update_categorization_thresholds(self, new_thresholds: Dict[str, float]):
        """Met à jour les seuils de catégorisation."""
        
        self.current_rules['seuils_categorisation'].update(new_thresholds)
        logger.info(f"Seuils de catégorisation mis à jour: {new_thresholds}")
    
    def get_adjusted_probability(self, base_probability: float, restaurant_data: Dict[str, Any]) -> float:
        """
        Calcule la probabilité ajustée selon les règles actuelles.
        
        Args:
            base_probability: Probabilité de base
            restaurant_data: Données du restaurant
            
        Returns:
            Probabilité ajustée
        """
        try:
            # Application des facteurs de risque
            facteur_type = self.current_rules['facteurs_risque']['type_etablissement'].get(
                restaurant_data.get('theme', 'restaurant').lower(), 1.0
            )
            
            facteur_taille = self.current_rules['facteurs_risque']['taille_etablissement'].get(
                restaurant_data.get('taille', 'moyen').lower(), 1.0
            )
            
            # Facteur saisonnier
            mois_actuel = datetime.now().month
            if mois_actuel in [6, 7, 8]:
                saison = 'ete'
            elif mois_actuel in [12, 1, 2]:
                saison = 'hiver'
            elif mois_actuel in [3, 4, 5]:
                saison = 'printemps'
            else:
                saison = 'automne'
            
            facteur_saison = self.current_rules['facteurs_risque']['saison'][saison]
            
            # Application des pondérations temporelles
            facteur_temporel = self.temporal_weights.get('facteur_global', 1.0)
            
            # Calcul de la probabilité ajustée
            probabilite_ajustee = base_probability * facteur_type * facteur_taille * facteur_saison * facteur_temporel
            
            # Limitation entre 0 et 1
            probabilite_ajustee = max(0.0, min(1.0, probabilite_ajustee))
            
            return probabilite_ajustee
            
        except Exception as e:
            logger.error(f"Erreur calcul probabilité ajustée: {e}")
            return base_probability
    
    def get_current_rules_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des règles actuelles."""
        
        return {
            'version': self.current_rules['version'],
            'date_effective': self.current_rules['date_effective'],
            'nb_categories_infractions': len(self.current_rules['categories_infractions']),
            'nb_facteurs_risque': len(self.current_rules['facteurs_risque']),
            'seuils_categorisation': self.current_rules['seuils_categorisation'],
            'ponderation_temporelle_active': bool(self.temporal_weights),
            'historique_versions': len(self.rules_history)
        }
    
    def simulate_rule_change_impact(self, proposed_changes: Dict[str, Any], 
                                  test_restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simule l'impact d'un changement de règles sur un échantillon de restaurants.
        
        Args:
            proposed_changes: Changements proposés
            test_restaurants: Échantillon de restaurants pour test
            
        Returns:
            Analyse d'impact
        """
        try:
            # Sauvegarde des règles actuelles
            rules_backup = self.current_rules.copy()
            
            # Application temporaire des changements
            temp_rules = rules_backup.copy()
            temp_rules.update(proposed_changes)
            
            # Calcul des impacts
            impacts = {
                'restaurants_testes': len(test_restaurants),
                'changements_categorisation': 0,
                'augmentation_risque_moyenne': 0.0,
                'restaurants_impactes': []
            }
            
            probabilites_avant = []
            probabilites_apres = []
            
            for restaurant in test_restaurants:
                # Probabilité avec règles actuelles
                prob_avant = self.get_adjusted_probability(0.5, restaurant)  # Base 50%
                
                # Application temporaire des nouvelles règles
                self.current_rules = temp_rules
                prob_apres = self.get_adjusted_probability(0.5, restaurant)
                
                probabilites_avant.append(prob_avant)
                probabilites_apres.append(prob_apres)
                
                # Détection des changements significatifs
                if abs(prob_apres - prob_avant) > 0.1:
                    impacts['changements_categorisation'] += 1
                    impacts['restaurants_impactes'].append({
                        'nom': restaurant.get('nom', f"Restaurant_{len(impacts['restaurants_impactes'])}"),
                        'prob_avant': prob_avant,
                        'prob_apres': prob_apres,
                        'changement': prob_apres - prob_avant
                    })
            
            # Calcul des statistiques globales
            if probabilites_avant and probabilites_apres:
                impacts['augmentation_risque_moyenne'] = (
                    sum(probabilites_apres) / len(probabilites_apres) - 
                    sum(probabilites_avant) / len(probabilites_avant)
                )
            
            # Restauration des règles originales
            self.current_rules = rules_backup
            
            logger.info(f"Simulation impact terminée: {impacts['changements_categorisation']} restaurants impactés")
            
            return impacts
            
        except Exception as e:
            logger.error(f"Erreur simulation impact: {e}")
            return {'erreur': str(e)}
    
    def export_rules_configuration(self, filepath: str = None) -> str:
        """
        Exporte la configuration actuelle des règles.
        
        Args:
            filepath: Chemin de sauvegarde (optionnel)
            
        Returns:
            Configuration JSON
        """
        try:
            config_export = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'version': self.current_rules['version']
                },
                'rules': self.current_rules,
                'temporal_weights': self.temporal_weights,
                'history': self.rules_history
            }
            
            config_json = json.dumps(config_export, indent=2, ensure_ascii=False)
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(config_json)
                logger.info(f"Configuration exportée vers {filepath}")
            
            return config_json
            
        except Exception as e:
            logger.error(f"Erreur export configuration: {e}")
            return "{}"

# === FONCTION DE DÉMONSTRATION ===

def demo_rule_adapter():
    """Démonstration complète de l'adaptateur de règles."""
    print("DÉMONSTRATION ADAPTATEUR DE RÈGLES MAPAQ")
    print("="*50)
    
    # Initialisation
    adapter = RuleAdapter()
    
    # Affichage des règles actuelles
    print("\n--- RÈGLES ACTUELLES ---")
    summary = adapter.get_current_rules_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Test pondération temporelle
    print("\n--- TEST PONDÉRATION TEMPORELLE ---")
    weights = adapter.apply_time_based_weights('2024-01-01')
    for key, value in weights.items():
        print(f"{key}: {value:.3f}")
    
    # Test ajustement probabilité
    print("\n--- TEST AJUSTEMENT PROBABILITÉ ---")
    restaurant_test = {
        'nom': 'Restaurant Test',
        'theme': 'fast_food',
        'taille': 'grand'
    }
    
    prob_base = 0.6
    prob_ajustee = adapter.get_adjusted_probability(prob_base, restaurant_test)
    print(f"Probabilité base: {prob_base:.3f}")
    print(f"Probabilité ajustée: {prob_ajustee:.3f}")
    print(f"Facteur d'ajustement: {prob_ajustee/prob_base:.3f}")
    
    # Test mise à jour règles
    print("\n--- TEST MISE À JOUR RÈGLES ---")
    nouvelles_regles = {
        'version': '2024.2',
        'date_effective': '2024-06-01',
        'changements': ['Nouveau facteur fast_food', 'Seuils révisés'],
        'impact': 'majeur',
        'facteurs_risque': {
            'type_etablissement': {
                'fast_food': 1.4  # Augmentation du risque
            }
        }
    }
    
    success = adapter.update_rules(nouvelles_regles)
    print(f"Mise à jour réussie: {success}")
    
    if success:
        prob_nouvelle = adapter.get_adjusted_probability(prob_base, restaurant_test)
        print(f"Nouvelle probabilité ajustée: {prob_nouvelle:.3f}")
        print(f"Impact du changement: {prob_nouvelle - prob_ajustee:+.3f}")
    
    return adapter

if __name__ == "__main__":
    # Exécution de la démonstration
    adapter = demo_rule_adapter()
