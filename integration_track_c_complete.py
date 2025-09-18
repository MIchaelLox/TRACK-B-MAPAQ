"""
Intégration Complète Track-C avec Track-A et Track-B
Module d'intégration refait avec architecture adaptée aux projets existants

Ce module intègre:
- Track-A (FACE): Moteur de calcul financier des coûts
- Track-B (MAPAQ): Modèle prédictif des risques restaurants  
- Track-C (Integration Utils): Hub d'intégration et composants partagés

Auteur: Mouhamed Thiaw
Date: 2025-01-17
"""

import os
import json
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
import aiohttp
from marshmallow import Schema, fields, ValidationError

# Imports des modules Track-B (MAPAQ)
from data_ingest import DataIngestor
from data_cleaner import DataCleaner
from address_dict import AddressNormalizer
from theme_dict import ThemeClassifier
from config import IntegrationConfig

# Configuration du logging en français
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration_track_c.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== MODÈLES DE DONNÉES INTÉGRÉS ==========

@dataclass
class RestaurantComplet:
    """Modèle complet d'un restaurant pour l'intégration tri-track."""
    # Données de base
    nom: str
    adresse: str
    theme_cuisine: str
    telephone: Optional[str] = None
    
    # Données Track-B (MAPAQ)
    historique_inspections: List[Dict] = None
    score_risque_mapaq: Optional[float] = None
    categorie_risque: Optional[str] = None
    
    # Données Track-A (FACE)
    taille_revenus: Optional[str] = None
    nombre_employes: Optional[int] = None
    taille_cuisine: Optional[float] = None
    cout_total_estime: Optional[float] = None
    
    # Métadonnées d'intégration
    id_integration: Optional[str] = None
    timestamp_creation: Optional[datetime] = None
    
    def __post_init__(self):
        if self.historique_inspections is None:
            self.historique_inspections = []
        if self.timestamp_creation is None:
            self.timestamp_creation = datetime.now()
        if self.id_integration is None:
            self.id_integration = f"rest_{hash(self.nom + self.adresse)}_{int(datetime.now().timestamp())}"

@dataclass
class AnalyseComposite:
    """Résultat d'analyse composite Track-A + Track-B."""
    restaurant_id: str
    
    # Résultats Track-B (Prédiction de risque)
    score_risque: float
    categorie_risque: str
    facteurs_risque: List[str]
    confiance_prediction: float
    
    # Résultats Track-A (Analyse financière)
    cout_total_estime: float
    cout_personnel: float
    cout_equipement: float
    cout_immobilier: float
    cout_operationnel: float
    
    # Analyse composite
    score_composite: float
    recommandations: List[str]
    prochaine_inspection_suggeree: Optional[datetime]
    
    # Métadonnées
    timestamp_analyse: datetime
    version_modele: str = "1.0"

# ========== SCHÉMAS DE VALIDATION ==========

class SchemaRestaurantEntree(Schema):
    """Schéma de validation pour les données d'entrée restaurant."""
    nom = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0, 
                     error_messages={'required': 'Le nom du restaurant est obligatoire'})
    adresse = fields.Str(required=True, validate=lambda x: len(x.strip()) > 5,
                        error_messages={'required': 'L\'adresse est obligatoire'})
    theme_cuisine = fields.Str(missing="", allow_none=True)
    telephone = fields.Str(missing="", allow_none=True)
    taille_revenus = fields.Str(missing="medium", validate=lambda x: x in ['small', 'medium', 'large'])
    nombre_employes = fields.Int(missing=5, validate=lambda x: x > 0)
    taille_cuisine = fields.Float(missing=50.0, validate=lambda x: x > 0)

class SchemaReponseAPI(Schema):
    """Schéma standardisé pour toutes les réponses API."""
    succes = fields.Bool(required=True)
    donnees = fields.Raw(allow_none=True)
    erreur = fields.Str(allow_none=True)
    timestamp = fields.DateTime(missing=datetime.now)
    temps_execution = fields.Float(missing=0.0)

# ========== GESTIONNAIRE D'INTÉGRATION PRINCIPAL ==========

class GestionnaireIntegrationTrackC:
    """
    Gestionnaire principal pour l'intégration des trois tracks.
    Orchestre les communications entre Track-A, Track-B et Track-C.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'intégration."""
        # Configuration des URLs des services
        self.url_track_a = os.getenv('TRACK_A_URL', 'http://localhost:8000')
        self.url_track_c = os.getenv('TRACK_C_URL', 'http://localhost:9000')
        
        # Initialisation des modules Track-B
        self.ingesteur_donnees = DataIngestor()
        self.nettoyeur_donnees = DataCleaner()
        self.normaliseur_adresses = AddressNormalizer()
        self.classificateur_themes = ThemeClassifier()
        
        # Schémas de validation
        self.schema_entree = SchemaRestaurantEntree()
        self.schema_reponse = SchemaReponseAPI()
        
        # Cache pour optimiser les performances
        self.cache_predictions = {}
        self.cache_analyses_financieres = {}
        
        # Statistiques d'utilisation
        self.stats = {
            'requetes_traitees': 0,
            'erreurs_track_a': 0,
            'erreurs_track_c': 0,
            'temps_reponse_moyen': 0.0,
            'heure_demarrage': datetime.now()
        }
        
        logger.info("🚀 Gestionnaire d'intégration Track-C initialisé avec succès")
    
    async def analyser_restaurant_complet(self, donnees_restaurant: Dict) -> AnalyseComposite:
        """
        Effectue une analyse complète d'un restaurant en utilisant les trois tracks.
        
        Args:
            donnees_restaurant: Données du restaurant à analyser
            
        Returns:
            AnalyseComposite: Résultat de l'analyse tri-track
        """
        debut_analyse = datetime.now()
        
        try:
            # Étape 1: Validation des données d'entrée
            donnees_validees = self.schema_entree.load(donnees_restaurant)
            logger.info(f"📝 Analyse démarrée pour: {donnees_validees['nom']}")
            
            # Étape 2: Création du modèle restaurant complet
            restaurant = RestaurantComplet(
                nom=donnees_validees['nom'],
                adresse=donnees_validees['adresse'],
                theme_cuisine=donnees_validees.get('theme_cuisine', ''),
                telephone=donnees_validees.get('telephone'),
                taille_revenus=donnees_validees.get('taille_revenus', 'medium'),
                nombre_employes=donnees_validees.get('nombre_employes', 5),
                taille_cuisine=donnees_validees.get('taille_cuisine', 50.0)
            )
            
            # Étape 3: Traitement Track-B (Prédiction de risque MAPAQ)
            logger.info("🔍 Traitement Track-B: Prédiction de risque MAPAQ")
            resultats_track_b = await self._traiter_track_b(restaurant)
            
            # Étape 4: Traitement Track-A (Analyse financière FACE)
            logger.info("💰 Traitement Track-A: Analyse financière FACE")
            resultats_track_a = await self._traiter_track_a(restaurant)
            
            # Étape 5: Synthèse et analyse composite
            logger.info("🔄 Synthèse des résultats Track-A + Track-B")
            analyse_composite = self._creer_analyse_composite(
                restaurant, resultats_track_b, resultats_track_a
            )
            
            # Étape 6: Communication avec Track-C pour enrichissement
            logger.info("🌐 Communication avec Track-C pour enrichissement")
            await self._enrichir_avec_track_c(analyse_composite)
            
            # Mise à jour des statistiques
            temps_execution = (datetime.now() - debut_analyse).total_seconds()
            self._mettre_a_jour_stats(temps_execution, succes=True)
            
            logger.info(f"✅ Analyse complète terminée en {temps_execution:.2f}s")
            return analyse_composite
            
        except Exception as e:
            temps_execution = (datetime.now() - debut_analyse).total_seconds()
            self._mettre_a_jour_stats(temps_execution, succes=False)
            logger.error(f"❌ Erreur lors de l'analyse complète: {str(e)}")
            raise
    
    async def _traiter_track_b(self, restaurant: RestaurantComplet) -> Dict:
        """
        Traite les données avec les modules Track-B (MAPAQ).
        
        Args:
            restaurant: Données du restaurant
            
        Returns:
            Dict: Résultats de l'analyse Track-B
        """
        try:
            # Normalisation de l'adresse
            adresse_normalisee = self.normaliseur_adresses.normalize_address(restaurant.adresse)
            
            # Géocodage de l'adresse
            donnees_geo = self.normaliseur_adresses.geocode_address(adresse_normalisee)
            
            # Classification du thème culinaire
            theme_detecte = self.theme_classifier.classify_restaurant_theme(
                restaurant.nom, restaurant.theme_cuisine
            )
            
            # Simulation de prédiction de risque (à remplacer par le vrai modèle)
            score_risque = self._calculer_score_risque_simule(restaurant, theme_detecte, donnees_geo)
            
            return {
                'adresse_normalisee': adresse_normalisee,
                'coordonnees': donnees_geo,
                'theme_detecte': theme_detecte,
                'score_risque': score_risque,
                'categorie_risque': self._categoriser_risque(score_risque),
                'facteurs_risque': self._identifier_facteurs_risque(restaurant, theme_detecte),
                'confiance': 0.85  # Simulation
            }
            
        except Exception as e:
            logger.error(f"Erreur Track-B: {str(e)}")
            raise
    
    async def _traiter_track_a(self, restaurant: RestaurantComplet) -> Dict:
        """
        Communique avec Track-A (FACE) pour l'analyse financière.
        
        Args:
            restaurant: Données du restaurant
            
        Returns:
            Dict: Résultats de l'analyse Track-A
        """
        try:
            # Préparation des données pour Track-A (format FACE)
            donnees_face = {
                'session_name': f"analyse_{restaurant.nom}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'restaurant_theme': restaurant.theme_cuisine or 'restaurant',
                'revenue_size': restaurant.taille_revenus,
                'staff_count': restaurant.nombre_employes,
                'kitchen_size': restaurant.taille_cuisine,
                'training_hours_needed': 40,  # Valeur par défaut
                'equipment_condition': 'good',  # Valeur par défaut
                'equipment_age_years': 3,  # Valeur par défaut
                'location_type': 'commercial'  # Valeur par défaut
            }
            
            # Appel à l'API Track-A
            url_calcul = f"{self.url_track_a}/api/calculate"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url_calcul, json=donnees_face, timeout=30) as response:
                    if response.status == 200:
                        resultats = await response.json()
                        logger.info("✅ Réponse Track-A reçue avec succès")
                        return resultats
                    else:
                        logger.warning(f"⚠️ Track-A indisponible (status: {response.status})")
                        return self._generer_analyse_financiere_fallback(restaurant)
                        
        except Exception as e:
            logger.error(f"Erreur communication Track-A: {str(e)}")
            self.stats['erreurs_track_a'] += 1
            return self._generer_analyse_financiere_fallback(restaurant)
    
    def _creer_analyse_composite(self, restaurant: RestaurantComplet, 
                               track_b: Dict, track_a: Dict) -> AnalyseComposite:
        """
        Crée l'analyse composite en combinant les résultats Track-A et Track-B.
        
        Args:
            restaurant: Données du restaurant
            track_b: Résultats Track-B
            track_a: Résultats Track-A
            
        Returns:
            AnalyseComposite: Analyse combinée
        """
        # Calcul du score composite (pondération Track-B: 60%, Track-A: 40%)
        score_risque_normalise = track_b['score_risque'] / 100.0
        score_financier_normalise = min(track_a.get('total_cost', 50000) / 100000.0, 1.0)
        
        score_composite = (score_risque_normalise * 0.6) + (score_financier_normalise * 0.4)
        score_composite = score_composite * 100  # Retour en pourcentage
        
        # Génération des recommandations
        recommandations = self._generer_recommandations(track_b, track_a, score_composite)
        
        # Suggestion de prochaine inspection
        prochaine_inspection = self._calculer_prochaine_inspection(
            track_b['score_risque'], track_b['categorie_risque']
        )
        
        return AnalyseComposite(
            restaurant_id=restaurant.id_integration,
            score_risque=track_b['score_risque'],
            categorie_risque=track_b['categorie_risque'],
            facteurs_risque=track_b['facteurs_risque'],
            confiance_prediction=track_b['confiance'],
            cout_total_estime=track_a.get('total_cost', 0.0),
            cout_personnel=track_a.get('staff_costs', 0.0),
            cout_equipement=track_a.get('equipment_costs', 0.0),
            cout_immobilier=track_a.get('location_costs', 0.0),
            cout_operationnel=track_a.get('operational_costs', 0.0),
            score_composite=score_composite,
            recommandations=recommandations,
            prochaine_inspection_suggeree=prochaine_inspection,
            timestamp_analyse=datetime.now()
        )
    
    async def _enrichir_avec_track_c(self, analyse: AnalyseComposite):
        """
        Enrichit l'analyse avec les services Track-C.
        
        Args:
            analyse: Analyse composite à enrichir
        """
        try:
            # Préparation des données pour Track-C
            donnees_enrichissement = {
                'restaurant_id': analyse.restaurant_id,
                'risk_score': analyse.score_risque,
                'financial_analysis': {
                    'total_cost': analyse.cout_total_estime,
                    'cost_breakdown': {
                        'staff': analyse.cout_personnel,
                        'equipment': analyse.cout_equipement,
                        'location': analyse.cout_immobilier,
                        'operations': analyse.cout_operationnel
                    }
                },
                'composite_score': analyse.score_composite
            }
            
            # Appel à Track-C pour enrichissement
            url_enrichissement = f"{self.url_track_c}/api/v1/enrich-analysis"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url_enrichissement, json=donnees_enrichissement, timeout=15) as response:
                    if response.status == 200:
                        enrichissement = await response.json()
                        
                        # Mise à jour des recommandations avec celles de Track-C
                        if 'recommendations' in enrichissement:
                            analyse.recommandations.extend(enrichissement['recommendations'])
                        
                        logger.info("✅ Enrichissement Track-C appliqué")
                    else:
                        logger.warning(f"⚠️ Track-C indisponible pour enrichissement (status: {response.status})")
                        
        except Exception as e:
            logger.error(f"Erreur enrichissement Track-C: {str(e)}")
            self.stats['erreurs_track_c'] += 1
            # L'enrichissement est optionnel, on continue sans erreur
    
    def _calculer_score_risque_simule(self, restaurant: RestaurantComplet, 
                                    theme: Dict, geo: Dict) -> float:
        """Calcule un score de risque simulé basé sur les données disponibles."""
        score_base = 50.0
        
        # Facteur thématique
        facteurs_theme = {
            'fast_food': 1.3, 'sushi': 1.2, 'bbq': 1.25,
            'fine_dining': 0.8, 'cafe': 0.9, 'italian': 1.0
        }
        theme_detecte = theme.get('theme', 'restaurant')
        facteur_theme = facteurs_theme.get(theme_detecte, 1.0)
        
        # Facteur de taille (plus grand = plus de risque)
        facteur_taille = 1.0 + (restaurant.nombre_employes - 5) * 0.02
        
        # Facteur géographique (simulation)
        facteur_geo = 1.0
        if geo and 'latitude' in geo and 'longitude' in geo:
            # Zone centre-ville = plus de risque
            if 45.5 <= geo['latitude'] <= 45.6 and -73.6 <= geo['longitude'] <= -73.5:
                facteur_geo = 1.15
        
        score_final = score_base * facteur_theme * facteur_taille * facteur_geo
        return min(max(score_final, 0.0), 100.0)
    
    def _categoriser_risque(self, score: float) -> str:
        """Catégorise le niveau de risque."""
        if score < 30:
            return "FAIBLE"
        elif score < 70:
            return "MOYEN"
        else:
            return "ÉLEVÉ"
    
    def _identifier_facteurs_risque(self, restaurant: RestaurantComplet, theme: Dict) -> List[str]:
        """Identifie les facteurs de risque principaux."""
        facteurs = []
        
        # Facteurs thématiques
        themes_risque = ['fast_food', 'sushi', 'bbq']
        if theme.get('theme') in themes_risque:
            facteurs.append(f"Type de cuisine à risque: {theme.get('theme')}")
        
        # Facteurs de taille
        if restaurant.nombre_employes > 15:
            facteurs.append("Grande équipe (gestion complexe)")
        
        # Facteurs d'infrastructure
        if restaurant.taille_cuisine and restaurant.taille_cuisine > 100:
            facteurs.append("Grande cuisine (surface étendue)")
        
        return facteurs
    
    def _generer_analyse_financiere_fallback(self, restaurant: RestaurantComplet) -> Dict:
        """Génère une analyse financière de fallback si Track-A est indisponible."""
        # Estimations basiques basées sur la taille et le type
        multiplicateurs_taille = {'small': 0.7, 'medium': 1.0, 'large': 1.5}
        multiplicateur = multiplicateurs_taille.get(restaurant.taille_revenus, 1.0)
        
        cout_base = 30000 * multiplicateur
        
        return {
            'total_cost': cout_base,
            'staff_costs': cout_base * 0.4,
            'equipment_costs': cout_base * 0.25,
            'location_costs': cout_base * 0.2,
            'operational_costs': cout_base * 0.15,
            'fallback': True,
            'message': 'Estimation basique (Track-A indisponible)'
        }
    
    def _generer_recommandations(self, track_b: Dict, track_a: Dict, score_composite: float) -> List[str]:
        """Génère des recommandations basées sur les analyses."""
        recommandations = []
        
        # Recommandations basées sur le risque MAPAQ
        if track_b['score_risque'] > 70:
            recommandations.append("🔴 Priorité élevée: Révision des procédures de sécurité alimentaire")
            recommandations.append("📋 Formation urgente du personnel sur l'hygiène")
        elif track_b['score_risque'] > 40:
            recommandations.append("🟡 Surveillance renforcée des pratiques d'hygiène")
        
        # Recommandations basées sur l'analyse financière
        cout_total = track_a.get('total_cost', 0)
        if cout_total > 80000:
            recommandations.append("💰 Coûts élevés détectés: Optimisation budgétaire recommandée")
        
        # Recommandations composites
        if score_composite > 75:
            recommandations.append("⚠️ Score composite élevé: Inspection rapprochée recommandée")
        
        return recommandations
    
    def _calculer_prochaine_inspection(self, score_risque: float, categorie: str) -> datetime:
        """Calcule la date suggérée pour la prochaine inspection."""
        # Intervalles basés sur le niveau de risque
        intervalles = {
            'FAIBLE': 365,    # 1 an
            'MOYEN': 180,     # 6 mois
            'ÉLEVÉ': 90       # 3 mois
        }
        
        jours_intervalle = intervalles.get(categorie, 180)
        
        # Ajustement basé sur le score exact
        if score_risque > 85:
            jours_intervalle = min(jours_intervalle, 60)  # Maximum 2 mois
        elif score_risque < 20:
            jours_intervalle = max(jours_intervalle, 400)  # Minimum 13 mois
        
        return datetime.now() + timedelta(days=jours_intervalle)
    
    def _mettre_a_jour_stats(self, temps_execution: float, succes: bool):
        """Met à jour les statistiques d'utilisation."""
        self.stats['requetes_traitees'] += 1
        
        if not succes:
            return
        
        # Calcul de la moyenne mobile du temps de réponse
        ancien_temps_moyen = self.stats['temps_reponse_moyen']
        nouveau_temps_moyen = (
            (ancien_temps_moyen * (self.stats['requetes_traitees'] - 1) + temps_execution) /
            self.stats['requetes_traitees']
        )
        self.stats['temps_reponse_moyen'] = nouveau_temps_moyen
    
    def obtenir_statistiques(self) -> Dict:
        """Retourne les statistiques d'utilisation du gestionnaire."""
        duree_fonctionnement = datetime.now() - self.stats['heure_demarrage']
        
        return {
            **self.stats,
            'duree_fonctionnement_heures': duree_fonctionnement.total_seconds() / 3600,
            'taux_erreur_track_a': (
                self.stats['erreurs_track_a'] / max(self.stats['requetes_traitees'], 1) * 100
            ),
            'taux_erreur_track_c': (
                self.stats['erreurs_track_c'] / max(self.stats['requetes_traitees'], 1) * 100
            )
        }

# ========== API FLASK POUR L'INTÉGRATION ==========

def creer_app_integration() -> Flask:
    """Crée l'application Flask pour l'intégration Track-C."""
    app = Flask(__name__)
    CORS(app)
    
    # Initialisation du gestionnaire
    gestionnaire = GestionnaireIntegrationTrackC()
    
    @app.route('/api/v1/sante', methods=['GET'])
    def verifier_sante():
        """Endpoint de vérification de santé du service d'intégration."""
        stats = gestionnaire.obtenir_statistiques()
        
        return jsonify({
            'succes': True,
            'service': 'Intégration Track-C MAPAQ',
            'statut': 'opérationnel',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'statistiques': stats
        })
    
    @app.route('/api/v1/analyser-restaurant', methods=['POST'])
    def analyser_restaurant():
        """Endpoint principal pour l'analyse complète d'un restaurant."""
        try:
            donnees = request.get_json()
            
            if not donnees:
                return jsonify({
                    'succes': False,
                    'erreur': 'Données JSON requises',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            # Analyse asynchrone dans un contexte synchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                analyse = loop.run_until_complete(
                    gestionnaire.analyser_restaurant_complet(donnees)
                )
                
                return jsonify({
                    'succes': True,
                    'donnees': asdict(analyse),
                    'timestamp': datetime.now().isoformat()
                })
                
            finally:
                loop.close()
                
        except ValidationError as e:
            return jsonify({
                'succes': False,
                'erreur': 'Données invalides',
                'details': e.messages,
                'timestamp': datetime.now().isoformat()
            }), 400
            
        except Exception as e:
            logger.error(f"Erreur analyse restaurant: {str(e)}")
            return jsonify({
                'succes': False,
                'erreur': 'Erreur interne du serveur',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/v1/statistiques', methods=['GET'])
    def obtenir_statistiques():
        """Endpoint pour récupérer les statistiques d'utilisation."""
        stats = gestionnaire.obtenir_statistiques()
        
        return jsonify({
            'succes': True,
            'donnees': stats,
            'timestamp': datetime.now().isoformat()
        })
    
    return app

# ========== POINT D'ENTRÉE ==========

if __name__ == "__main__":
    # Configuration du serveur
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Création et lancement de l'application
    app = creer_app_integration()
    
    logger.info(f"🚀 Démarrage du serveur d'intégration Track-C sur {host}:{port}")
    logger.info("📋 Endpoints disponibles:")
    logger.info("   GET  /api/v1/sante - Vérification de santé")
    logger.info("   POST /api/v1/analyser-restaurant - Analyse complète")
    logger.info("   GET  /api/v1/statistiques - Statistiques d'utilisation")
    
    app.run(host=host, port=port, debug=debug)
