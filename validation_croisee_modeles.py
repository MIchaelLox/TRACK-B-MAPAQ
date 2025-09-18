"""
Validation Croisée des Modèles MAPAQ
Comparaison et évaluation robuste des modèles baseline et probabilités conditionnelles

Auteur: Mouhamed Thiaw
Date: 2025-01-17
Heures: 49-52 (Mardi - Validation Croisée)
"""

import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

# Import des modules développés précédemment
from model_baseline_complet import BaselineModel, RegressionLogistique, NaiveBayes, FeaturePreprocessor
from probability_engine_complet import ProbabilityEngine

class ValidationCroisee:
    """
    Système de validation croisée pour évaluer et comparer les modèles MAPAQ.
    Implémente k-fold cross-validation et métriques de performance avancées.
    """
    
    def __init__(self, k_folds: int = 5):
        """
        Initialise le système de validation croisée.
        
        Args:
            k_folds: Nombre de plis pour la validation croisée
        """
        self.k_folds = k_folds
        self.resultats_validation = {}
        self.comparaisons_modeles = {}
        self.metriques_detaillees = {}
        
        print(f"Système de validation croisée initialisé avec {k_folds} plis")
    
    def generer_donnees_test_robustes(self, n_samples: int = 2000) -> List[Dict]:
        """
        Génère un dataset robuste pour la validation croisée.
        
        Args:
            n_samples: Nombre d'échantillons à générer
            
        Returns:
            Liste des données d'inspection simulées
        """
        print(f"Génération de {n_samples} échantillons pour validation robuste...")
        
        donnees = []
        
        # Paramètres de génération réalistes
        themes = ['restaurant', 'fast_food', 'cafe', 'bar', 'hotel']
        tailles = ['petit', 'moyen', 'grand', 'enterprise']
        zones = ['urbain_dense', 'urbain', 'periurbain', 'rural']
        saisons = ['hiver', 'printemps', 'ete', 'automne']
        
        # Probabilités réalistes par thème
        prob_infractions_theme = {
            'restaurant': 0.35,
            'fast_food': 0.45,
            'cafe': 0.25,
            'bar': 0.40,
            'hotel': 0.30
        }
        
        for i in range(n_samples):
            # Sélection aléatoire des caractéristiques
            theme = random.choice(themes)
            taille = random.choice(tailles)
            zone = random.choice(zones)
            saison = random.choice(saisons)
            
            # Génération d'infractions basée sur les probabilités réalistes
            prob_base = prob_infractions_theme[theme]
            
            # Ajustements selon la taille
            if taille == 'petit':
                prob_base *= 1.1
            elif taille == 'grand':
                prob_base *= 1.2
            elif taille == 'enterprise':
                prob_base *= 1.3
            
            # Ajustements selon la zone
            if zone == 'urbain_dense':
                prob_base *= 1.2
            elif zone == 'rural':
                prob_base *= 0.8
            
            # Génération des infractions
            a_infraction = random.random() < prob_base
            nb_infractions = 0
            infractions = []
            
            if a_infraction:
                # Nombre d'infractions (distribution réaliste)
                if random.random() < 0.6:
                    nb_infractions = 1
                elif random.random() < 0.8:
                    nb_infractions = 2
                elif random.random() < 0.95:
                    nb_infractions = random.randint(3, 5)
                else:
                    nb_infractions = random.randint(6, 10)
                
                for j in range(nb_infractions):
                    # Génération d'amendes réalistes
                    if theme == 'fast_food':
                        amende_base = random.uniform(200, 2000)
                    elif theme == 'restaurant':
                        amende_base = random.uniform(300, 1500)
                    elif theme == 'bar':
                        amende_base = random.uniform(400, 2500)
                    else:
                        amende_base = random.uniform(150, 1200)
                    
                    infractions.append({
                        'type': f'infraction_{j+1}',
                        'amende': f"{amende_base:.2f}$",
                        'gravite': 'grave' if amende_base > 1500 else 'moderee' if amende_base > 500 else 'legere'
                    })
            
            # Création de l'échantillon
            echantillon = {
                'id': f'TEST_{i:05d}',
                'nom': f'{theme.title()} {i}',
                'type_etablissement': theme,
                'theme': theme,
                'taille': taille,
                'adresse': f'{random.randint(100, 9999)} Rue Test, Ville, QC',
                'localisation': zone,
                'saison': saison,
                'date_inspection': f'2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                'infractions': infractions,
                'historique': infractions,  # Pour compatibilité
                'age_donnees_jours': random.randint(1, 365),
                'label_reel': 1 if a_infraction else 0  # Label de vérité terrain
            }
            
            donnees.append(echantillon)
        
        print(f"Dataset généré: {len(donnees)} échantillons")
        return donnees
    
    def diviser_en_plis(self, donnees: List[Dict]) -> List[Tuple[List[Dict], List[Dict]]]:
        """
        Divise les données en k plis pour la validation croisée.
        
        Args:
            donnees: Dataset complet
            
        Returns:
            Liste de tuples (train, test) pour chaque pli
        """
        print(f"Division en {self.k_folds} plis...")
        
        # Mélange aléatoire
        donnees_melangees = donnees.copy()
        random.shuffle(donnees_melangees)
        
        taille_pli = len(donnees_melangees) // self.k_folds
        plis = []
        
        for i in range(self.k_folds):
            debut = i * taille_pli
            fin = debut + taille_pli if i < self.k_folds - 1 else len(donnees_melangees)
            
            # Test = pli courant, Train = tous les autres
            test_set = donnees_melangees[debut:fin]
            train_set = donnees_melangees[:debut] + donnees_melangees[fin:]
            
            plis.append((train_set, test_set))
            print(f"Pli {i+1}: {len(train_set)} train, {len(test_set)} test")
        
        return plis
    
    def evaluer_modele_baseline(self, train_data: List[Dict], test_data: List[Dict]) -> Dict[str, Any]:
        """
        Évalue les modèles baseline sur un pli donné.
        
        Args:
            train_data: Données d'entraînement
            test_data: Données de test
            
        Returns:
            Dictionnaire avec les résultats d'évaluation
        """
        # Initialisation du modèle baseline
        modele = BaselineModel(train_data)
        modele.preparer_donnees(test_size=0.0)  # Pas de division, on utilise nos plis
        
        # Préparation manuelle des données
        preprocessor = FeaturePreprocessor()
        
        # Features d'entraînement
        features_train, labels_train = preprocessor.prepare_features(train_data)
        features_test, labels_test = preprocessor.prepare_features(test_data)
        
        # Labels réels pour comparaison
        labels_test_reels = [item['label_reel'] for item in test_data]
        
        resultats = {}
        
        # Test Régression Logistique
        try:
            reg_log = RegressionLogistique(learning_rate=0.01, max_iterations=300)
            reg_log.fit(features_train, labels_train)
            
            pred_log = reg_log.predict(features_test)
            prob_log = reg_log.predict_proba(features_test)
            
            resultats['regression_logistique'] = self._calculer_metriques_detaillees(
                labels_test_reels, pred_log, prob_log
            )
            
        except Exception as e:
            print(f"Erreur régression logistique: {e}")
            resultats['regression_logistique'] = None
        
        # Test Naïve Bayes
        try:
            naive_bayes = NaiveBayes()
            naive_bayes.fit(features_train, labels_train)
            
            pred_nb = naive_bayes.predict(features_test)
            prob_nb = naive_bayes.predict_proba(features_test)
            
            resultats['naive_bayes'] = self._calculer_metriques_detaillees(
                labels_test_reels, pred_nb, prob_nb
            )
            
        except Exception as e:
            print(f"Erreur Naïve Bayes: {e}")
            resultats['naive_bayes'] = None
        
        return resultats
    
    def evaluer_moteur_probabilites(self, train_data: List[Dict], test_data: List[Dict]) -> Dict[str, Any]:
        """
        Évalue le moteur de probabilités sur un pli donné.
        
        Args:
            train_data: Données d'entraînement (pour calibration)
            test_data: Données de test
            
        Returns:
            Dictionnaire avec les résultats d'évaluation
        """
        # Initialisation du moteur
        engine = ProbabilityEngine()
        
        # Prédictions sur les données de test
        predictions = []
        probabilites = []
        labels_reels = []
        
        for restaurant in test_data:
            # Calcul des probabilités
            resultats_prob = engine.calculate_infraction_probability(restaurant)
            
            prob_infraction = resultats_prob['probabilite_infraction']
            prediction = 1 if prob_infraction >= 0.5 else 0
            
            predictions.append(prediction)
            probabilites.append(prob_infraction)
            labels_reels.append(restaurant['label_reel'])
        
        # Calcul des métriques
        metriques = self._calculer_metriques_detaillees(labels_reels, predictions, probabilites)
        
        return {'moteur_probabilites': metriques}
    
    def _calculer_metriques_detaillees(self, y_true: List[int], y_pred: List[int], 
                                     y_prob: List[float]) -> Dict[str, float]:
        """Calcule des métriques détaillées pour l'évaluation."""
        
        # Matrice de confusion
        tp = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 1)
        tn = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 0)
        fp = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 1)
        fn = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 0)
        
        # Métriques de base
        accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Spécificité
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        # AUC approximée (méthode trapézoïdale simplifiée)
        auc = self._calculer_auc_approximee(y_true, y_prob)
        
        # Brier Score (calibration des probabilités)
        brier_score = sum((y_prob[i] - y_true[i]) ** 2 for i in range(len(y_true))) / len(y_true)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'specificity': specificity,
            'auc': auc,
            'brier_score': brier_score,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        }
    
    def _calculer_auc_approximee(self, y_true: List[int], y_prob: List[float]) -> float:
        """Calcule une approximation de l'AUC."""
        # Tri par probabilités décroissantes
        indices_tries = sorted(range(len(y_prob)), key=lambda i: y_prob[i], reverse=True)
        
        # Calcul simplifié de l'AUC
        n_pos = sum(y_true)
        n_neg = len(y_true) - n_pos
        
        if n_pos == 0 or n_neg == 0:
            return 0.5
        
        # Approximation par comptage des paires correctement ordonnées
        auc_sum = 0
        for i, idx in enumerate(indices_tries):
            if y_true[idx] == 1:
                # Compter les négatifs après cette position
                negatifs_apres = sum(1 for j in range(i+1, len(indices_tries)) 
                                   if y_true[indices_tries[j]] == 0)
                auc_sum += negatifs_apres
        
        return auc_sum / (n_pos * n_neg)
    
    def executer_validation_croisee_complete(self, donnees: List[Dict] = None) -> Dict[str, Any]:
        """
        Exécute la validation croisée complète sur tous les modèles.
        
        Args:
            donnees: Dataset (généré automatiquement si None)
            
        Returns:
            Résultats complets de la validation croisée
        """
        print("\n" + "="*60)
        print("VALIDATION CROISÉE COMPLÈTE DES MODÈLES MAPAQ")
        print("="*60)
        
        # Génération des données si nécessaire
        if donnees is None:
            donnees = self.generer_donnees_test_robustes(1500)
        
        # Division en plis
        plis = self.diviser_en_plis(donnees)
        
        # Stockage des résultats par modèle
        resultats_par_modele = {
            'regression_logistique': [],
            'naive_bayes': [],
            'moteur_probabilites': []
        }
        
        # Validation sur chaque pli
        for i, (train_data, test_data) in enumerate(plis):
            print(f"\n--- PLI {i+1}/{self.k_folds} ---")
            
            # Évaluation modèles baseline
            print("Évaluation modèles baseline...")
            resultats_baseline = self.evaluer_modele_baseline(train_data, test_data)
            
            # Évaluation moteur probabilités
            print("Évaluation moteur probabilités...")
            resultats_probabilites = self.evaluer_moteur_probabilites(train_data, test_data)
            
            # Stockage des résultats
            if resultats_baseline.get('regression_logistique'):
                resultats_par_modele['regression_logistique'].append(
                    resultats_baseline['regression_logistique']
                )
            
            if resultats_baseline.get('naive_bayes'):
                resultats_par_modele['naive_bayes'].append(
                    resultats_baseline['naive_bayes']
                )
            
            if resultats_probabilites.get('moteur_probabilites'):
                resultats_par_modele['moteur_probabilites'].append(
                    resultats_probabilites['moteur_probabilites']
                )
        
        # Calcul des moyennes et écarts-types
        resultats_finaux = self._calculer_statistiques_validation(resultats_par_modele)
        
        # Comparaison des modèles
        comparaisons = self._comparer_modeles(resultats_finaux)
        
        self.resultats_validation = resultats_finaux
        self.comparaisons_modeles = comparaisons
        
        return {
            'resultats_par_modele': resultats_finaux,
            'comparaisons': comparaisons,
            'nb_plis': self.k_folds,
            'taille_dataset': len(donnees)
        }
    
    def _calculer_statistiques_validation(self, resultats_par_modele: Dict) -> Dict[str, Any]:
        """Calcule les statistiques (moyenne, écart-type) pour chaque modèle."""
        
        statistiques = {}
        
        for modele, resultats_plis in resultats_par_modele.items():
            if not resultats_plis:
                continue
            
            # Métriques à calculer
            metriques = ['accuracy', 'precision', 'recall', 'f1_score', 'specificity', 'auc', 'brier_score']
            
            stats_modele = {}
            
            for metrique in metriques:
                valeurs = [pli[metrique] for pli in resultats_plis if metrique in pli]
                
                if valeurs:
                    moyenne = sum(valeurs) / len(valeurs)
                    variance = sum((x - moyenne) ** 2 for x in valeurs) / len(valeurs)
                    ecart_type = math.sqrt(variance)
                    
                    stats_modele[metrique] = {
                        'moyenne': moyenne,
                        'ecart_type': ecart_type,
                        'min': min(valeurs),
                        'max': max(valeurs),
                        'valeurs': valeurs
                    }
            
            statistiques[modele] = stats_modele
        
        return statistiques
    
    def _comparer_modeles(self, resultats_finaux: Dict) -> Dict[str, Any]:
        """Compare les performances des différents modèles."""
        
        comparaisons = {}
        
        # Métriques principales pour la comparaison
        metriques_principales = ['accuracy', 'f1_score', 'auc']
        
        for metrique in metriques_principales:
            classement = []
            
            for modele, stats in resultats_finaux.items():
                if metrique in stats:
                    moyenne = stats[metrique]['moyenne']
                    ecart_type = stats[metrique]['ecart_type']
                    
                    classement.append({
                        'modele': modele,
                        'moyenne': moyenne,
                        'ecart_type': ecart_type,
                        'score_robustesse': moyenne - ecart_type  # Pénalise la variabilité
                    })
            
            # Tri par performance
            classement.sort(key=lambda x: x['moyenne'], reverse=True)
            comparaisons[metrique] = classement
        
        # Modèle gagnant global
        scores_globaux = defaultdict(float)
        
        for metrique, classement in comparaisons.items():
            for i, modele_info in enumerate(classement):
                # Points selon le rang (1er = 3 pts, 2e = 2 pts, 3e = 1 pt)
                points = len(classement) - i
                scores_globaux[modele_info['modele']] += points
        
        # Classement final
        classement_final = sorted(scores_globaux.items(), key=lambda x: x[1], reverse=True)
        comparaisons['classement_global'] = classement_final
        
        return comparaisons
    
    def generer_rapport_validation_croisee(self) -> str:
        """Génère un rapport complet de la validation croisée."""
        
        if not self.resultats_validation:
            return "Aucun résultat de validation disponible"
        
        rapport = []
        rapport.append("="*70)
        rapport.append("RAPPORT COMPLET - VALIDATION CROISÉE MODÈLES MAPAQ")
        rapport.append("="*70)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rapport.append(f"Validation croisée: {self.k_folds} plis")
        
        # Résultats par modèle
        rapport.append("\n" + "-"*50)
        rapport.append("PERFORMANCES MOYENNES PAR MODÈLE")
        rapport.append("-"*50)
        
        for modele, stats in self.resultats_validation.items():
            rapport.append(f"\n{modele.upper().replace('_', ' ')}:")
            
            metriques_affichage = ['accuracy', 'precision', 'recall', 'f1_score', 'auc']
            for metrique in metriques_affichage:
                if metrique in stats:
                    moy = stats[metrique]['moyenne']
                    std = stats[metrique]['ecart_type']
                    rapport.append(f"  {metrique.capitalize():12}: {moy:.3f} ± {std:.3f}")
        
        # Comparaisons
        if self.comparaisons_modeles:
            rapport.append("\n" + "-"*50)
            rapport.append("CLASSEMENT DES MODÈLES")
            rapport.append("-"*50)
            
            if 'classement_global' in self.comparaisons_modeles:
                rapport.append("\nClassement global (points cumulés):")
                for i, (modele, points) in enumerate(self.comparaisons_modeles['classement_global']):
                    rapport.append(f"  {i+1}. {modele.replace('_', ' ').title()}: {points} points")
            
            # Meilleur par métrique
            rapport.append("\nMeilleur modèle par métrique:")
            for metrique in ['accuracy', 'f1_score', 'auc']:
                if metrique in self.comparaisons_modeles:
                    classement = self.comparaisons_modeles[metrique]
                    if classement:
                        meilleur = classement[0]
                        rapport.append(f"  {metrique.upper():8}: {meilleur['modele'].replace('_', ' ').title()} ({meilleur['moyenne']:.3f})")
        
        return "\n".join(rapport)

# === FONCTION DE DÉMONSTRATION ===

def demo_validation_croisee():
    """Démonstration complète de la validation croisée."""
    print("DÉMONSTRATION VALIDATION CROISÉE MODÈLES MAPAQ")
    print("="*55)
    
    # Initialisation
    validateur = ValidationCroisee(k_folds=3)  # 3 plis pour la démo (plus rapide)
    
    # Exécution de la validation croisée
    resultats = validateur.executer_validation_croisee_complete()
    
    # Affichage des résultats
    print("\n" + validateur.generer_rapport_validation_croisee())
    
    return validateur, resultats

if __name__ == "__main__":
    # Exécution de la démonstration
    validateur, resultats = demo_validation_croisee()
