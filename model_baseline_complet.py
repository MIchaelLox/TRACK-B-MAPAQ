"""
Modèles Baseline pour MAPAQ - Prédiction des Risques Restaurants
Implémentation de régression logistique et Naïve Bayes avec préparation features

Auteur: Mouhamed Thiaw
Date: 2025-01-17
Heures: 41-44 (Lundi - Modèle Baseline)
"""

import json
import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter

# === CLASSES DE PRÉPARATION DES FEATURES ===

class FeaturePreprocessor:
    """Préprocesseur pour la préparation des features MAPAQ."""
    
    def __init__(self):
        """Initialise le préprocesseur de features."""
        self.feature_encoders = {}
        self.feature_scalers = {}
        self.feature_stats = {}
        
    def prepare_features(self, donnees: List[Dict]) -> Tuple[List[List[float]], List[int]]:
        """
        Prépare les features pour l'entraînement des modèles.
        
        Args:
            donnees: Liste des données d'inspection MAPAQ
            
        Returns:
            Tuple (features_matrix, labels)
        """
        print("Préparation des features pour modélisation...")
        
        features_matrix = []
        labels = []
        
        for inspection in donnees:
            # Extraction des features
            features = self._extraire_features_inspection(inspection)
            
            # Création du label (0=faible risque, 1=risque élevé)
            label = self._creer_label_risque(inspection)
            
            if features and label is not None:
                features_matrix.append(features)
                labels.append(label)
        
        print(f"Features préparées: {len(features_matrix)} échantillons, {len(features_matrix[0]) if features_matrix else 0} features")
        
        return features_matrix, labels
    
    def _extraire_features_inspection(self, inspection: Dict) -> List[float]:
        """Extrait les features numériques d'une inspection."""
        features = []
        
        try:
            # Feature 1: Type d'établissement (encodage)
            type_etab = inspection.get('type_etablissement', 'inconnu')
            features.append(self._encoder_type_etablissement(type_etab))
            
            # Feature 2: Taille de l'établissement (proxy par nombre d'infractions)
            nb_infractions = len(inspection.get('infractions', []))
            features.append(min(nb_infractions, 10) / 10.0)  # Normalisation
            
            # Feature 3: Gravité moyenne des infractions
            gravite_moyenne = self._calculer_gravite_moyenne(inspection.get('infractions', []))
            features.append(gravite_moyenne)
            
            # Feature 4: Récurrence (basée sur l'historique)
            recurrence = self._calculer_recurrence(inspection)
            features.append(recurrence)
            
            # Feature 5: Saisonnalité (mois de l'inspection)
            mois = self._extraire_mois_inspection(inspection.get('date_inspection', ''))
            features.append(mois / 12.0)  # Normalisation
            
            # Feature 6: Zone géographique (encodage simplifié)
            zone_geo = self._encoder_zone_geographique(inspection.get('adresse', ''))
            features.append(zone_geo)
            
            # Feature 7: Âge de l'établissement (estimation)
            age_etablissement = self._estimer_age_etablissement(inspection)
            features.append(age_etablissement)
            
            return features
            
        except Exception as e:
            print(f"Erreur extraction features: {e}")
            return None
    
    def _encoder_type_etablissement(self, type_etab: str) -> float:
        """Encode le type d'établissement en valeur numérique."""
        encodage = {
            'restaurant': 0.8,
            'fast_food': 0.6,
            'cafe': 0.4,
            'bar': 0.7,
            'hotel': 0.5,
            'epicerie': 0.3,
            'boulangerie': 0.2,
            'inconnu': 0.5
        }
        
        # Recherche par mots-clés
        type_lower = type_etab.lower()
        for key, value in encodage.items():
            if key in type_lower:
                return value
        
        return encodage['inconnu']
    
    def _calculer_gravite_moyenne(self, infractions: List[Dict]) -> float:
        """Calcule la gravité moyenne des infractions."""
        if not infractions:
            return 0.0
        
        gravites = []
        for infraction in infractions:
            # Estimation de gravité basée sur l'amende
            amende = infraction.get('amende', 0)
            if isinstance(amende, str):
                try:
                    amende = float(amende.replace('$', '').replace(',', ''))
                except:
                    amende = 0
            
            # Normalisation de la gravité (0-1)
            gravite = min(amende / 5000.0, 1.0) if amende > 0 else 0.3
            gravites.append(gravite)
        
        return sum(gravites) / len(gravites)
    
    def _calculer_recurrence(self, inspection: Dict) -> float:
        """Calcule un score de récurrence basé sur l'historique."""
        # Simulation de récurrence basée sur le nombre d'infractions
        nb_infractions = len(inspection.get('infractions', []))
        
        if nb_infractions == 0:
            return 0.0
        elif nb_infractions <= 2:
            return 0.3
        elif nb_infractions <= 5:
            return 0.6
        else:
            return 0.9
    
    def _extraire_mois_inspection(self, date_str: str) -> int:
        """Extrait le mois de l'inspection."""
        try:
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) >= 2:
                    return int(parts[1])
            return 6  # Valeur par défaut (juin)
        except:
            return 6
    
    def _encoder_zone_geographique(self, adresse: str) -> float:
        """Encode la zone géographique en valeur numérique."""
        if not adresse:
            return 0.5
        
        # Encodage basé sur des mots-clés d'adresse
        adresse_lower = adresse.lower()
        
        if any(zone in adresse_lower for zone in ['montreal', 'mtl', 'downtown']):
            return 0.8  # Zone urbaine dense
        elif any(zone in adresse_lower for zone in ['laval', 'longueuil', 'brossard']):
            return 0.6  # Zone périurbaine
        elif any(zone in adresse_lower for zone in ['quebec', 'sherbrooke', 'gatineau']):
            return 0.7  # Autres grandes villes
        else:
            return 0.4  # Zone rurale/petite ville
    
    def _estimer_age_etablissement(self, inspection: Dict) -> float:
        """Estime l'âge de l'établissement (simulation)."""
        # Simulation basée sur le type et la complexité
        type_etab = inspection.get('type_etablissement', '')
        nb_infractions = len(inspection.get('infractions', []))
        
        # Heuristique: plus d'infractions = établissement plus ancien
        age_estime = min(nb_infractions * 2 + 1, 20)  # Max 20 ans
        return age_estime / 20.0  # Normalisation
    
    def _creer_label_risque(self, inspection: Dict) -> Optional[int]:
        """Crée le label de risque (0=faible, 1=élevé)."""
        try:
            infractions = inspection.get('infractions', [])
            
            if not infractions:
                return 0  # Pas d'infraction = faible risque
            
            # Calcul du score de risque basé sur les infractions
            score_risque = 0
            
            for infraction in infractions:
                # Points basés sur l'amende
                amende = infraction.get('amende', 0)
                if isinstance(amende, str):
                    try:
                        amende = float(amende.replace('$', '').replace(',', ''))
                    except:
                        amende = 0
                
                if amende > 2000:
                    score_risque += 3
                elif amende > 500:
                    score_risque += 2
                else:
                    score_risque += 1
            
            # Seuil: score > 5 = risque élevé
            return 1 if score_risque > 5 else 0
            
        except Exception as e:
            print(f"Erreur création label: {e}")
            return None

# === MODÈLE DE RÉGRESSION LOGISTIQUE ===

class RegressionLogistique:
    """Implémentation de régression logistique sans dépendances externes."""
    
    def __init__(self, learning_rate: float = 0.01, max_iterations: int = 1000):
        """
        Initialise le modèle de régression logistique.
        
        Args:
            learning_rate: Taux d'apprentissage
            max_iterations: Nombre maximum d'itérations
        """
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.weights = None
        self.bias = 0.0
        self.cost_history = []
        
    def _sigmoid(self, z: float) -> float:
        """Fonction sigmoid."""
        try:
            return 1.0 / (1.0 + math.exp(-z))
        except OverflowError:
            return 0.0 if z < 0 else 1.0
    
    def _predict_proba_single(self, features: List[float]) -> float:
        """Prédit la probabilité pour un échantillon."""
        if not self.weights:
            return 0.5
        
        z = self.bias + sum(w * f for w, f in zip(self.weights, features))
        return self._sigmoid(z)
    
    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """
        Entraîne le modèle de régression logistique.
        
        Args:
            X: Matrice des features
            y: Labels (0 ou 1)
        """
        print("Entraînement régression logistique...")
        
        if not X or not y:
            raise ValueError("Données d'entraînement vides")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Initialisation des poids
        self.weights = [random.uniform(-0.1, 0.1) for _ in range(n_features)]
        self.bias = 0.0
        
        # Gradient descent
        for iteration in range(self.max_iterations):
            # Forward pass
            predictions = [self._predict_proba_single(x) for x in X]
            
            # Calcul du coût (log-likelihood)
            cost = self._calculate_cost(predictions, y)
            self.cost_history.append(cost)
            
            # Backward pass (calcul des gradients)
            dw = [0.0] * n_features
            db = 0.0
            
            for i in range(n_samples):
                error = predictions[i] - y[i]
                db += error
                for j in range(n_features):
                    dw[j] += error * X[i][j]
            
            # Mise à jour des poids
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * (dw[j] / n_samples)
            self.bias -= self.learning_rate * (db / n_samples)
            
            # Affichage du progrès
            if iteration % 100 == 0:
                print(f"Itération {iteration}, Coût: {cost:.4f}")
        
        print(f"Entraînement terminé après {self.max_iterations} itérations")
    
    def _calculate_cost(self, predictions: List[float], y: List[int]) -> float:
        """Calcule le coût (cross-entropy)."""
        cost = 0.0
        n = len(y)
        
        for i in range(n):
            pred = max(min(predictions[i], 0.9999), 0.0001)  # Éviter log(0)
            cost += y[i] * math.log(pred) + (1 - y[i]) * math.log(1 - pred)
        
        return -cost / n
    
    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """Prédit les probabilités."""
        return [self._predict_proba_single(x) for x in X]
    
    def predict(self, X: List[List[float]]) -> List[int]:
        """Prédit les classes (0 ou 1)."""
        probas = self.predict_proba(X)
        return [1 if p >= 0.5 else 0 for p in probas]

# === MODÈLE NAÏVE BAYES ===

class NaiveBayes:
    """Implémentation de Naïve Bayes pour classification binaire."""
    
    def __init__(self):
        """Initialise le modèle Naïve Bayes."""
        self.class_priors = {}
        self.feature_stats = {}  # {classe: {feature_idx: {'mean': x, 'std': y}}}
        self.classes = [0, 1]
        
    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """
        Entraîne le modèle Naïve Bayes.
        
        Args:
            X: Matrice des features
            y: Labels (0 ou 1)
        """
        print("Entraînement Naïve Bayes...")
        
        if not X or not y:
            raise ValueError("Données d'entraînement vides")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Calcul des priors de classe
        class_counts = Counter(y)
        for classe in self.classes:
            self.class_priors[classe] = class_counts.get(classe, 0) / n_samples
        
        # Calcul des statistiques par feature et par classe
        self.feature_stats = {classe: {} for classe in self.classes}
        
        for classe in self.classes:
            # Filtrer les échantillons de cette classe
            class_samples = [X[i] for i in range(n_samples) if y[i] == classe]
            
            if not class_samples:
                continue
            
            # Calculer mean et std pour chaque feature
            for feature_idx in range(n_features):
                feature_values = [sample[feature_idx] for sample in class_samples]
                
                mean = sum(feature_values) / len(feature_values)
                variance = sum((x - mean) ** 2 for x in feature_values) / len(feature_values)
                std = math.sqrt(variance + 1e-6)  # Éviter division par 0
                
                self.feature_stats[classe][feature_idx] = {
                    'mean': mean,
                    'std': std
                }
        
        print(f"Modèle entraîné sur {n_samples} échantillons, {n_features} features")
    
    def _gaussian_probability(self, x: float, mean: float, std: float) -> float:
        """Calcule la probabilité gaussienne."""
        try:
            exponent = -0.5 * ((x - mean) / std) ** 2
            return (1.0 / (std * math.sqrt(2 * math.pi))) * math.exp(exponent)
        except (ZeroDivisionError, OverflowError):
            return 1e-6
    
    def _predict_single(self, features: List[float]) -> Tuple[int, float]:
        """Prédit la classe pour un échantillon."""
        class_probabilities = {}
        
        for classe in self.classes:
            # Prior de la classe
            prob = math.log(self.class_priors.get(classe, 1e-6))
            
            # Likelihood des features
            for feature_idx, feature_value in enumerate(features):
                if feature_idx in self.feature_stats[classe]:
                    stats = self.feature_stats[classe][feature_idx]
                    likelihood = self._gaussian_probability(
                        feature_value, stats['mean'], stats['std']
                    )
                    prob += math.log(likelihood)
            
            class_probabilities[classe] = prob
        
        # Classe avec la plus haute probabilité
        predicted_class = max(class_probabilities, key=class_probabilities.get)
        confidence = class_probabilities[predicted_class]
        
        return predicted_class, confidence
    
    def predict(self, X: List[List[float]]) -> List[int]:
        """Prédit les classes."""
        predictions = []
        for features in X:
            pred_class, _ = self._predict_single(features)
            predictions.append(pred_class)
        return predictions
    
    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """Prédit les probabilités (approximation)."""
        probabilities = []
        for features in X:
            pred_class, confidence = self._predict_single(features)
            # Conversion de log-prob en probabilité approximative
            prob = 0.7 if pred_class == 1 else 0.3
            probabilities.append(prob)
        return probabilities

# === CLASSE PRINCIPALE DES MODÈLES BASELINE ===

class BaselineModel:
    """Gestionnaire principal des modèles baseline MAPAQ."""
    
    def __init__(self, donnees_nettoyees: List[Dict] = None):
        """
        Initialise les modèles baseline.
        
        Args:
            donnees_nettoyees: Données d'inspection nettoyées
        """
        self.donnees = donnees_nettoyees or []
        self.preprocessor = FeaturePreprocessor()
        self.modele_logistique = None
        self.modele_naive_bayes = None
        self.features_train = None
        self.labels_train = None
        self.features_test = None
        self.labels_test = None
        self.resultats_evaluation = {}
        
        print(f"Modèles baseline initialisés avec {len(self.donnees)} échantillons")
    
    def preparer_donnees(self, test_size: float = 0.2) -> None:
        """Prépare et divise les données en train/test."""
        print("Préparation des données pour modélisation...")
        
        if not self.donnees:
            print("Génération de données simulées...")
            self.donnees = self._generer_donnees_simulees(1000)
        
        # Préparation des features
        features, labels = self.preprocessor.prepare_features(self.donnees)
        
        if not features:
            raise ValueError("Aucune feature valide extraite")
        
        # Division train/test
        n_test = int(len(features) * test_size)
        indices = list(range(len(features)))
        random.shuffle(indices)
        
        test_indices = indices[:n_test]
        train_indices = indices[n_test:]
        
        self.features_train = [features[i] for i in train_indices]
        self.labels_train = [labels[i] for i in train_indices]
        self.features_test = [features[i] for i in test_indices]
        self.labels_test = [labels[i] for i in test_indices]
        
        print(f"Données préparées: {len(self.features_train)} train, {len(self.features_test)} test")
    
    def train_logistic_regression(self) -> None:
        """Entraîne le modèle de régression logistique."""
        if not self.features_train:
            self.preparer_donnees()
        
        print("\n=== ENTRAÎNEMENT RÉGRESSION LOGISTIQUE ===")
        self.modele_logistique = RegressionLogistique(learning_rate=0.01, max_iterations=500)
        self.modele_logistique.fit(self.features_train, self.labels_train)
        print("Régression logistique entraînée avec succès")
    
    def train_naive_bayes(self) -> None:
        """Entraîne le modèle Naïve Bayes."""
        if not self.features_train:
            self.preparer_donnees()
        
        print("\n=== ENTRAÎNEMENT NAÏVE BAYES ===")
        self.modele_naive_bayes = NaiveBayes()
        self.modele_naive_bayes.fit(self.features_train, self.labels_train)
        print("Naïve Bayes entraîné avec succès")
    
    def evaluate_model(self, modele_type: str = 'both') -> Dict[str, Any]:
        """
        Évalue les modèles entraînés.
        
        Args:
            modele_type: 'logistic', 'naive_bayes', ou 'both'
            
        Returns:
            Dictionnaire avec les métriques d'évaluation
        """
        print(f"\n=== ÉVALUATION DES MODÈLES ({modele_type.upper()}) ===")
        
        if not self.features_test:
            raise ValueError("Données de test non disponibles")
        
        resultats = {}
        
        # Évaluation régression logistique
        if modele_type in ['logistic', 'both'] and self.modele_logistique:
            pred_log = self.modele_logistique.predict(self.features_test)
            prob_log = self.modele_logistique.predict_proba(self.features_test)
            
            metriques_log = self._calculer_metriques(self.labels_test, pred_log, prob_log)
            resultats['regression_logistique'] = metriques_log
            
            print(f"Régression Logistique - Accuracy: {metriques_log['accuracy']:.3f}")
        
        # Évaluation Naïve Bayes
        if modele_type in ['naive_bayes', 'both'] and self.modele_naive_bayes:
            pred_nb = self.modele_naive_bayes.predict(self.features_test)
            prob_nb = self.modele_naive_bayes.predict_proba(self.features_test)
            
            metriques_nb = self._calculer_metriques(self.labels_test, pred_nb, prob_nb)
            resultats['naive_bayes'] = metriques_nb
            
            print(f"Naïve Bayes - Accuracy: {metriques_nb['accuracy']:.3f}")
        
        self.resultats_evaluation = resultats
        return resultats
    
    def _calculer_metriques(self, y_true: List[int], y_pred: List[int], 
                          y_prob: List[float]) -> Dict[str, float]:
        """Calcule les métriques d'évaluation."""
        # Matrice de confusion
        tp = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 1)
        tn = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 0)
        fp = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 1)
        fn = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 0)
        
        # Métriques
        accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        }
    
    def _generer_donnees_simulees(self, n_samples: int) -> List[Dict]:
        """Génère des données d'inspection simulées pour les tests."""
        print(f"Génération de {n_samples} échantillons simulés...")
        
        donnees_simulees = []
        types_etablissement = ['restaurant', 'fast_food', 'cafe', 'bar', 'hotel']
        
        for i in range(n_samples):
            # Génération aléatoire d'une inspection
            nb_infractions = random.randint(0, 8)
            infractions = []
            
            for j in range(nb_infractions):
                amende = random.uniform(100, 3000)
                infractions.append({
                    'type': f'infraction_{j}',
                    'amende': f"{amende:.2f}$",
                    'description': f'Violation {j+1}'
                })
            
            inspection = {
                'id': f'INSP_{i:04d}',
                'type_etablissement': random.choice(types_etablissement),
                'adresse': f'{random.randint(100, 9999)} Rue Test, Montréal, QC',
                'date_inspection': f'2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                'infractions': infractions
            }
            
            donnees_simulees.append(inspection)
        
        return donnees_simulees
    
    def generer_rapport_complet(self) -> str:
        """Génère un rapport complet des modèles baseline."""
        rapport = []
        rapport.append("="*60)
        rapport.append("RAPPORT COMPLET - MODÈLES BASELINE MAPAQ")
        rapport.append("="*60)
        rapport.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rapport.append(f"Échantillons total: {len(self.donnees)}")
        
        if self.features_train:
            rapport.append(f"Échantillons entraînement: {len(self.features_train)}")
            rapport.append(f"Échantillons test: {len(self.features_test)}")
            rapport.append(f"Nombre de features: {len(self.features_train[0])}")
        
        rapport.append("\n" + "-"*40)
        rapport.append("RÉSULTATS D'ÉVALUATION")
        rapport.append("-"*40)
        
        for modele, metriques in self.resultats_evaluation.items():
            rapport.append(f"\n{modele.upper().replace('_', ' ')}:")
            rapport.append(f"  Accuracy:  {metriques['accuracy']:.3f}")
            rapport.append(f"  Precision: {metriques['precision']:.3f}")
            rapport.append(f"  Recall:    {metriques['recall']:.3f}")
            rapport.append(f"  F1-Score:  {metriques['f1_score']:.3f}")
            rapport.append(f"  TP: {metriques['tp']}, TN: {metriques['tn']}")
            rapport.append(f"  FP: {metriques['fp']}, FN: {metriques['fn']}")
        
        return "\n".join(rapport)

# === FONCTION DE DÉMONSTRATION ===

def demo_modeles_baseline():
    """Démonstration complète des modèles baseline."""
    print("DÉMONSTRATION MODÈLES BASELINE MAPAQ")
    print("="*50)
    
    # Initialisation
    modeles = BaselineModel()
    
    # Préparation des données
    modeles.preparer_donnees(test_size=0.2)
    
    # Entraînement des modèles
    modeles.train_logistic_regression()
    modeles.train_naive_bayes()
    
    # Évaluation
    resultats = modeles.evaluate_model('both')
    
    # Rapport final
    rapport = modeles.generer_rapport_complet()
    print("\n" + rapport)
    
    return modeles, resultats

if __name__ == "__main__":
    # Exécution de la démonstration
    modeles, resultats = demo_modeles_baseline()
