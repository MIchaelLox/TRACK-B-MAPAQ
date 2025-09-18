"""
Optimisation des Hyperparamètres pour Modèles MAPAQ
Grid Search et optimisation automatique pour maximiser les performances

Auteur: Mouhamed Thiaw
Date: 2025-01-17
Heures: 53-56 (Mardi - Optimisation Hyperparamètres)
"""

import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import itertools

# Import des modules développés précédemment
from model_baseline_complet import BaselineModel, RegressionLogistique, NaiveBayes, FeaturePreprocessor
from probability_engine_complet import ProbabilityEngine
from validation_croisee_modeles import ValidationCroisee

class OptimisateurHyperparametres:
    """
    Système d'optimisation des hyperparamètres pour les modèles MAPAQ.
    Implémente Grid Search, Random Search et optimisation bayésienne simplifiée.
    """
    
    def __init__(self, validation_croisee: ValidationCroisee = None):
        """
        Initialise l'optimisateur d'hyperparamètres.
        
        Args:
            validation_croisee: Instance de validation croisée (optionnel)
        """
        self.validateur = validation_croisee or ValidationCroisee(k_folds=3)
        self.historique_optimisation = {}
        self.meilleurs_parametres = {}
        self.resultats_optimisation = {}
        
        print("Optimisateur d'hyperparamètres initialisé")
    
    def definir_espaces_recherche(self) -> Dict[str, Dict[str, List]]:
        """
        Définit les espaces de recherche pour chaque modèle.
        
        Returns:
            Dictionnaire des hyperparamètres à optimiser
        """
        espaces = {
            'regression_logistique': {
                'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.2],
                'max_iterations': [100, 300, 500, 1000, 1500],
                'regularization': [0.0, 0.01, 0.1, 0.5]  # L2 regularization
            },
            'naive_bayes': {
                'smoothing': [1e-9, 1e-6, 1e-3, 1.0, 2.0],  # Laplace smoothing
                'threshold': [0.3, 0.4, 0.5, 0.6, 0.7]  # Seuil de décision
            },
            'moteur_probabilites': {
                'poids_theme': [0.4, 0.5, 0.6, 0.7, 0.8],
                'poids_taille': [0.2, 0.3, 0.4, 0.5, 0.6],
                'facteur_historique_max': [1.5, 2.0, 2.5, 3.0],
                'seuil_decision': [0.4, 0.45, 0.5, 0.55, 0.6]
            }
        }
        
        return espaces
    
    def grid_search_regression_logistique(self, donnees: List[Dict]) -> Dict[str, Any]:
        """
        Optimise la régression logistique par Grid Search.
        
        Args:
            donnees: Dataset pour l'optimisation
            
        Returns:
            Meilleurs hyperparamètres et performances
        """
        print("\n=== GRID SEARCH - RÉGRESSION LOGISTIQUE ===")
        
        espaces = self.definir_espaces_recherche()
        params_reg = espaces['regression_logistique']
        
        meilleur_score = 0
        meilleurs_params = {}
        historique = []
        
        # Génération de toutes les combinaisons
        combinaisons = list(itertools.product(
            params_reg['learning_rate'],
            params_reg['max_iterations'],
            params_reg['regularization']
        ))
        
        print(f"Test de {len(combinaisons)} combinaisons de paramètres...")
        
        # Test de chaque combinaison (limité pour la démo)
        for i, (lr, max_iter, reg) in enumerate(combinaisons[:20]):  # Limite à 20 pour la démo
            print(f"Combinaison {i+1}/20: lr={lr}, iter={max_iter}, reg={reg}")
            
            try:
                # Test avec validation croisée
                score = self._evaluer_regression_logistique_avec_params(
                    donnees, lr, max_iter, reg
                )
                
                historique.append({
                    'learning_rate': lr,
                    'max_iterations': max_iter,
                    'regularization': reg,
                    'f1_score': score
                })
                
                if score > meilleur_score:
                    meilleur_score = score
                    meilleurs_params = {
                        'learning_rate': lr,
                        'max_iterations': max_iter,
                        'regularization': reg
                    }
                    print(f"  Nouveau meilleur score: {score:.3f}")
                
            except Exception as e:
                print(f"  Erreur: {e}")
                continue
        
        self.historique_optimisation['regression_logistique'] = historique
        self.meilleurs_parametres['regression_logistique'] = meilleurs_params
        
        return {
            'meilleurs_parametres': meilleurs_params,
            'meilleur_score': meilleur_score,
            'historique': historique
        }
    
    def _evaluer_regression_logistique_avec_params(self, donnees: List[Dict], 
                                                 lr: float, max_iter: int, reg: float) -> float:
        """Évalue la régression logistique avec des paramètres spécifiques."""
        
        # Division simple train/test pour l'optimisation
        random.shuffle(donnees)
        split_idx = int(len(donnees) * 0.8)
        train_data = donnees[:split_idx]
        test_data = donnees[split_idx:]
        
        # Préparation des features
        preprocessor = FeaturePreprocessor()
        features_train, labels_train = preprocessor.prepare_features(train_data)
        features_test, labels_test = preprocessor.prepare_features(test_data)
        
        # Labels réels
        labels_test_reels = [item['label_reel'] for item in test_data]
        
        # Entraînement avec paramètres spécifiques
        modele = RegressionLogistiqueOptimisee(
            learning_rate=lr, 
            max_iterations=max_iter, 
            regularization=reg
        )
        modele.fit(features_train, labels_train)
        
        # Prédiction et évaluation
        predictions = modele.predict(features_test)
        
        # Calcul F1-Score
        tp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 1)
        fp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 0 and predictions[i] == 1)
        fn = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 0)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return f1_score
    
    def optimiser_naive_bayes(self, donnees: List[Dict]) -> Dict[str, Any]:
        """
        Optimise Naïve Bayes en ajustant le seuil de décision.
        
        Args:
            donnees: Dataset pour l'optimisation
            
        Returns:
            Meilleurs hyperparamètres et performances
        """
        print("\n=== OPTIMISATION - NAÏVE BAYES ===")
        
        espaces = self.definir_espaces_recherche()
        params_nb = espaces['naive_bayes']
        
        meilleur_score = 0
        meilleurs_params = {}
        historique = []
        
        # Test de différents seuils
        for threshold in params_nb['threshold']:
            for smoothing in params_nb['smoothing']:
                print(f"Test seuil={threshold}, smoothing={smoothing}")
                
                try:
                    score = self._evaluer_naive_bayes_avec_params(
                        donnees, threshold, smoothing
                    )
                    
                    historique.append({
                        'threshold': threshold,
                        'smoothing': smoothing,
                        'f1_score': score
                    })
                    
                    if score > meilleur_score:
                        meilleur_score = score
                        meilleurs_params = {
                            'threshold': threshold,
                            'smoothing': smoothing
                        }
                        print(f"  Nouveau meilleur score: {score:.3f}")
                
                except Exception as e:
                    print(f"  Erreur: {e}")
                    continue
        
        self.historique_optimisation['naive_bayes'] = historique
        self.meilleurs_parametres['naive_bayes'] = meilleurs_params
        
        return {
            'meilleurs_parametres': meilleurs_params,
            'meilleur_score': meilleur_score,
            'historique': historique
        }
    
    def _evaluer_naive_bayes_avec_params(self, donnees: List[Dict], 
                                       threshold: float, smoothing: float) -> float:
        """Évalue Naïve Bayes avec des paramètres spécifiques."""
        
        # Division train/test
        random.shuffle(donnees)
        split_idx = int(len(donnees) * 0.8)
        train_data = donnees[:split_idx]
        test_data = donnees[split_idx:]
        
        # Préparation des features
        preprocessor = FeaturePreprocessor()
        features_train, labels_train = preprocessor.prepare_features(train_data)
        features_test, labels_test = preprocessor.prepare_features(test_data)
        
        # Labels réels
        labels_test_reels = [item['label_reel'] for item in test_data]
        
        # Entraînement
        modele = NaiveBayesOptimise(smoothing=smoothing)
        modele.fit(features_train, labels_train)
        
        # Prédiction avec seuil ajusté
        probabilites = modele.predict_proba(features_test)
        predictions = [1 if p >= threshold else 0 for p in probabilites]
        
        # Calcul F1-Score
        tp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 1)
        fp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 0 and predictions[i] == 1)
        fn = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 0)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return f1_score
    
    def optimiser_moteur_probabilites(self, donnees: List[Dict]) -> Dict[str, Any]:
        """
        Optimise le moteur de probabilités par ajustement des facteurs.
        
        Args:
            donnees: Dataset pour l'optimisation
            
        Returns:
            Meilleurs hyperparamètres et performances
        """
        print("\n=== OPTIMISATION - MOTEUR PROBABILITÉS ===")
        
        espaces = self.definir_espaces_recherche()
        params_mp = espaces['moteur_probabilites']
        
        meilleur_score = 0
        meilleurs_params = {}
        historique = []
        
        # Random Search (plus efficace que Grid Search pour cet espace)
        n_iterations = 25
        
        for i in range(n_iterations):
            # Sélection aléatoire des paramètres
            params = {
                'poids_theme': random.choice(params_mp['poids_theme']),
                'poids_taille': random.choice(params_mp['poids_taille']),
                'facteur_historique_max': random.choice(params_mp['facteur_historique_max']),
                'seuil_decision': random.choice(params_mp['seuil_decision'])
            }
            
            print(f"Itération {i+1}/{n_iterations}: {params}")
            
            try:
                score = self._evaluer_moteur_probabilites_avec_params(donnees, params)
                
                historique.append({**params, 'f1_score': score})
                
                if score > meilleur_score:
                    meilleur_score = score
                    meilleurs_params = params.copy()
                    print(f"  Nouveau meilleur score: {score:.3f}")
            
            except Exception as e:
                print(f"  Erreur: {e}")
                continue
        
        self.historique_optimisation['moteur_probabilites'] = historique
        self.meilleurs_parametres['moteur_probabilites'] = meilleurs_params
        
        return {
            'meilleurs_parametres': meilleurs_params,
            'meilleur_score': meilleur_score,
            'historique': historique
        }
    
    def _evaluer_moteur_probabilites_avec_params(self, donnees: List[Dict], 
                                               params: Dict[str, float]) -> float:
        """Évalue le moteur de probabilités avec des paramètres spécifiques."""
        
        # Division train/test
        random.shuffle(donnees)
        split_idx = int(len(donnees) * 0.8)
        test_data = donnees[split_idx:]
        
        # Labels réels
        labels_test_reels = [item['label_reel'] for item in test_data]
        
        # Initialisation du moteur avec paramètres optimisés
        engine = MoteurProbabilitesOptimise(params)
        
        # Prédictions
        predictions = []
        for restaurant in test_data:
            resultats_prob = engine.calculate_infraction_probability(restaurant)
            prob_infraction = resultats_prob['probabilite_infraction']
            prediction = 1 if prob_infraction >= params['seuil_decision'] else 0
            predictions.append(prediction)
        
        # Calcul F1-Score
        tp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 1)
        fp = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 0 and predictions[i] == 1)
        fn = sum(1 for i in range(len(labels_test_reels)) if labels_test_reels[i] == 1 and predictions[i] == 0)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return f1_score
    
    def executer_optimisation_complete(self, donnees: List[Dict] = None) -> Dict[str, Any]:
        """
        Exécute l'optimisation complète de tous les modèles.
        
        Args:
            donnees: Dataset (généré si None)
            
        Returns:
            Résultats complets de l'optimisation
        """
        print("\n" + "="*60)
        print("OPTIMISATION COMPLÈTE DES HYPERPARAMÈTRES")
        print("="*60)
        
        # Génération des données si nécessaire
        if donnees is None:
            donnees = self.validateur.generer_donnees_test_robustes(1000)
        
        resultats_optimisation = {}
        
        # Optimisation Régression Logistique
        try:
            resultats_optimisation['regression_logistique'] = self.grid_search_regression_logistique(donnees)
        except Exception as e:
            print(f"Erreur optimisation régression logistique: {e}")
        
        # Optimisation Naïve Bayes
        try:
            resultats_optimisation['naive_bayes'] = self.optimiser_naive_bayes(donnees)
        except Exception as e:
            print(f"Erreur optimisation Naïve Bayes: {e}")
        
        # Optimisation Moteur Probabilités
        try:
            resultats_optimisation['moteur_probabilites'] = self.optimiser_moteur_probabilites(donnees)
        except Exception as e:
            print(f"Erreur optimisation moteur probabilités: {e}")
        
        self.resultats_optimisation = resultats_optimisation
        
        # Comparaison des améliorations
        ameliorations = self._calculer_ameliorations()
        
        return {
            'resultats_par_modele': resultats_optimisation,
            'ameliorations': ameliorations,
            'meilleurs_parametres': self.meilleurs_parametres
        }
    
    def _calculer_ameliorations(self) -> Dict[str, Dict[str, float]]:
        """Calcule les améliorations apportées par l'optimisation."""
        
        # Scores de base (avant optimisation)
        scores_base = {
            'regression_logistique': 0.000,  # De la validation croisée
            'naive_bayes': 0.149,
            'moteur_probabilites': 0.670
        }
        
        ameliorations = {}
        
        for modele, resultats in self.resultats_optimisation.items():
            if 'meilleur_score' in resultats:
                score_optimise = resultats['meilleur_score']
                score_initial = scores_base.get(modele, 0)
                
                amelioration_absolue = score_optimise - score_initial
                amelioration_relative = (amelioration_absolue / max(score_initial, 0.001)) * 100
                
                ameliorations[modele] = {
                    'score_initial': score_initial,
                    'score_optimise': score_optimise,
                    'amelioration_absolue': amelioration_absolue,
                    'amelioration_relative': amelioration_relative
                }
        
        return ameliorations
    
    def generer_rapport_optimisation(self) -> str:
        """Génère un rapport complet de l'optimisation."""
        
        if not self.resultats_optimisation:
            return "Aucun résultat d'optimisation disponible"
        
        rapport = []
        rapport.append("="*70)
        rapport.append("RAPPORT COMPLET - OPTIMISATION HYPERPARAMÈTRES")
        rapport.append("="*70)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Résultats par modèle
        rapport.append("\n" + "-"*50)
        rapport.append("MEILLEURS HYPERPARAMÈTRES PAR MODÈLE")
        rapport.append("-"*50)
        
        for modele, params in self.meilleurs_parametres.items():
            rapport.append(f"\n{modele.upper().replace('_', ' ')}:")
            for param, valeur in params.items():
                rapport.append(f"  {param}: {valeur}")
            
            if modele in self.resultats_optimisation:
                score = self.resultats_optimisation[modele].get('meilleur_score', 0)
                rapport.append(f"  Meilleur F1-Score: {score:.3f}")
        
        # Améliorations
        ameliorations = self._calculer_ameliorations()
        if ameliorations:
            rapport.append("\n" + "-"*50)
            rapport.append("AMÉLIORATIONS APPORTÉES")
            rapport.append("-"*50)
            
            for modele, stats in ameliorations.items():
                rapport.append(f"\n{modele.upper().replace('_', ' ')}:")
                rapport.append(f"  Score initial: {stats['score_initial']:.3f}")
                rapport.append(f"  Score optimisé: {stats['score_optimise']:.3f}")
                rapport.append(f"  Amélioration: +{stats['amelioration_absolue']:.3f} ({stats['amelioration_relative']:+.1f}%)")
        
        return "\n".join(rapport)

# === CLASSES OPTIMISÉES ===

class RegressionLogistiqueOptimisee(RegressionLogistique):
    """Version optimisée de la régression logistique avec régularisation."""
    
    def __init__(self, learning_rate: float = 0.01, max_iterations: int = 1000, 
                 regularization: float = 0.0):
        super().__init__(learning_rate, max_iterations)
        self.regularization = regularization
    
    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """Entraînement avec régularisation L2."""
        if not X or not y:
            raise ValueError("Données d'entraînement vides")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Initialisation des poids
        self.weights = [random.uniform(-0.1, 0.1) for _ in range(n_features)]
        self.bias = 0.0
        
        # Gradient descent avec régularisation
        for iteration in range(self.max_iterations):
            predictions = [self._predict_proba_single(x) for x in X]
            
            # Calcul du coût avec régularisation
            cost = self._calculate_cost(predictions, y)
            reg_cost = self.regularization * sum(w**2 for w in self.weights) / 2
            total_cost = cost + reg_cost
            self.cost_history.append(total_cost)
            
            # Gradients avec régularisation
            dw = [0.0] * n_features
            db = 0.0
            
            for i in range(n_samples):
                error = predictions[i] - y[i]
                db += error
                for j in range(n_features):
                    dw[j] += error * X[i][j]
            
            # Mise à jour avec régularisation
            for j in range(n_features):
                reg_term = self.regularization * self.weights[j]
                self.weights[j] -= self.learning_rate * ((dw[j] / n_samples) + reg_term)
            self.bias -= self.learning_rate * (db / n_samples)

class NaiveBayesOptimise(NaiveBayes):
    """Version optimisée de Naïve Bayes avec smoothing ajustable."""
    
    def __init__(self, smoothing: float = 1.0):
        super().__init__()
        self.smoothing = smoothing
    
    def _gaussian_probability(self, x: float, mean: float, std: float) -> float:
        """Probabilité gaussienne avec smoothing."""
        try:
            # Ajout du smoothing à l'écart-type
            std_smoothed = std + self.smoothing * 1e-6
            exponent = -0.5 * ((x - mean) / std_smoothed) ** 2
            return (1.0 / (std_smoothed * math.sqrt(2 * math.pi))) * math.exp(exponent)
        except (ZeroDivisionError, OverflowError):
            return self.smoothing * 1e-6

class MoteurProbabilitesOptimise(ProbabilityEngine):
    """Version optimisée du moteur de probabilités avec paramètres ajustables."""
    
    def __init__(self, params_optimises: Dict[str, float]):
        super().__init__()
        self.params = params_optimises
        self._ajuster_probabilites_base()
    
    def _ajuster_probabilites_base(self):
        """Ajuste les probabilités de base selon les paramètres optimisés."""
        # Ajustement des facteurs de pondération
        facteur_theme = self.params.get('poids_theme', 0.6)
        facteur_taille = self.params.get('poids_taille', 0.4)
        
        # Les probabilités sont ajustées dynamiquement dans les calculs
        self.facteur_theme_global = facteur_theme
        self.facteur_taille_global = facteur_taille
    
    def _calculer_probabilite_base(self, theme: str, taille: str, historique: str) -> float:
        """Version optimisée du calcul de probabilité de base."""
        prob_theme = self.prob_theme.get(theme, self.prob_theme['restaurant'])['p_infraction']
        prob_taille = self.prob_taille.get(taille, self.prob_taille['moyen'])['p_infraction']
        
        # Utilisation des poids optimisés
        prob_base = (prob_theme * self.facteur_theme_global + 
                    prob_taille * self.facteur_taille_global)
        
        return prob_base

# === FONCTION DE DÉMONSTRATION ===

def demo_optimisation_hyperparametres():
    """Démonstration complète de l'optimisation des hyperparamètres."""
    print("DÉMONSTRATION OPTIMISATION HYPERPARAMÈTRES")
    print("="*50)
    
    # Initialisation
    optimisateur = OptimisateurHyperparametres()
    
    # Exécution de l'optimisation
    resultats = optimisateur.executer_optimisation_complete()
    
    # Affichage des résultats
    print("\n" + optimisateur.generer_rapport_optimisation())
    
    return optimisateur, resultats

if __name__ == "__main__":
    # Exécution de la démonstration
    optimisateur, resultats = demo_optimisation_hyperparametres()
