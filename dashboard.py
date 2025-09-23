
"""
Dashboard Backend MAPAQ - Architecture Flask/FastAPI
Interface web pour le système prédictif de risques sanitaires

Auteur: Mouhamed Thiaw
Date: 2025-01-19
Heures: 81-84 (Lundi - Architecture Dashboard Backend)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sqlite3
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RestaurantData:
    """Structure de données pour un restaurant."""
    id: str
    nom: str
    theme: str
    taille: str
    zone: str
    adresse: str
    score_risque: float
    categorie_risque: str
    probabilite_infraction: float
    derniere_inspection: str
    prochaine_inspection: str
    historique_infractions: List[str]

@dataclass
class PredictionResult:
    """Résultat de prédiction de risque."""
    restaurant_id: str
    score_risque: float
    categorie_risque: str
    probabilite_infraction: float
    confiance: float
    facteurs_risque: Dict[str, float]
    recommandations: List[str]
    timestamp: str

class DatabaseManager:
    """Gestionnaire de base de données pour le dashboard."""
    
    def __init__(self, db_path: str = "mapaq_dashboard.db"):
        """Initialise le gestionnaire de base de données."""
        self.db_path = db_path
        self.init_database()
        logger.info(f"Base de données dashboard initialisée: {db_path}")
    
    def init_database(self):
        """Initialise les tables de la base de données."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table restaurants
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS restaurants (
                    id TEXT PRIMARY KEY,
                    nom TEXT NOT NULL,
                    theme TEXT,
                    taille TEXT,
                    zone TEXT,
                    adresse TEXT,
                    score_risque REAL,
                    categorie_risque TEXT,
                    probabilite_infraction REAL,
                    derniere_inspection TEXT,
                    prochaine_inspection TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table historique prédictions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurant_id TEXT,
                    score_risque REAL,
                    categorie_risque TEXT,
                    probabilite_infraction REAL,
                    confiance REAL,
                    facteurs_risque TEXT,
                    recommandations TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                )
            ''')
            
            # Table infractions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS infractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurant_id TEXT,
                    date_infraction TEXT,
                    type_infraction TEXT,
                    gravite TEXT,
                    description TEXT,
                    statut TEXT,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                )
            ''')
            
            # Table métriques système
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value REAL,
                    metric_unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Tables de base de données créées avec succès")
    
    def save_restaurant(self, restaurant: RestaurantData) -> bool:
        """Sauvegarde un restaurant en base."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO restaurants 
                    (id, nom, theme, taille, zone, adresse, score_risque, 
                     categorie_risque, probabilite_infraction, derniere_inspection, 
                     prochaine_inspection, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    restaurant.id, restaurant.nom, restaurant.theme, restaurant.taille,
                    restaurant.zone, restaurant.adresse, restaurant.score_risque,
                    restaurant.categorie_risque, restaurant.probabilite_infraction,
                    restaurant.derniere_inspection, restaurant.prochaine_inspection,
                    datetime.now().isoformat()
                ))
                
                # Sauvegarde historique infractions
                cursor.execute('DELETE FROM infractions WHERE restaurant_id = ?', (restaurant.id,))
                for infraction_date in restaurant.historique_infractions:
                    cursor.execute('''
                        INSERT INTO infractions (restaurant_id, date_infraction, type_infraction, gravite)
                        VALUES (?, ?, ?, ?)
                    ''', (restaurant.id, infraction_date, 'Infraction générale', 'Moyenne'))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde restaurant {restaurant.id}: {e}")
            return False
    
    def get_restaurant(self, restaurant_id: str) -> Optional[RestaurantData]:
        """Récupère un restaurant par ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
                row = cursor.fetchone()
                
                if row:
                    # Récupération historique infractions
                    cursor.execute('SELECT date_infraction FROM infractions WHERE restaurant_id = ?', (restaurant_id,))
                    infractions = [r[0] for r in cursor.fetchall()]
                    
                    return RestaurantData(
                        id=row[0], nom=row[1], theme=row[2], taille=row[3],
                        zone=row[4], adresse=row[5], score_risque=row[6],
                        categorie_risque=row[7], probabilite_infraction=row[8],
                        derniere_inspection=row[9], prochaine_inspection=row[10],
                        historique_infractions=infractions
                    )
                return None
        except Exception as e:
            logger.error(f"Erreur récupération restaurant {restaurant_id}: {e}")
            return None
    
    def get_all_restaurants(self) -> List[RestaurantData]:
        """Récupère tous les restaurants."""
        restaurants = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM restaurants ORDER BY score_risque DESC')
                rows = cursor.fetchall()
                
                for row in rows:
                    # Récupération historique infractions
                    cursor.execute('SELECT date_infraction FROM infractions WHERE restaurant_id = ?', (row[0],))
                    infractions = [r[0] for r in cursor.fetchall()]
                    
                    restaurants.append(RestaurantData(
                        id=row[0], nom=row[1], theme=row[2], taille=row[3],
                        zone=row[4], adresse=row[5], score_risque=row[6],
                        categorie_risque=row[7], probabilite_infraction=row[8],
                        derniere_inspection=row[9], prochaine_inspection=row[10],
                        historique_infractions=infractions
                    ))
        except Exception as e:
            logger.error(f"Erreur récupération restaurants: {e}")
        
        return restaurants
    
    def save_prediction(self, prediction: PredictionResult) -> bool:
        """Sauvegarde une prédiction en historique."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO predictions_history 
                    (restaurant_id, score_risque, categorie_risque, probabilite_infraction,
                     confiance, facteurs_risque, recommandations, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction.restaurant_id, prediction.score_risque, prediction.categorie_risque,
                    prediction.probabilite_infraction, prediction.confiance,
                    json.dumps(prediction.facteurs_risque), json.dumps(prediction.recommandations),
                    prediction.timestamp
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde prédiction: {e}")
            return False

class MapaqDashboardBackend:
    """Backend principal du dashboard MAPAQ."""
    
    def __init__(self):
        """Initialise le backend du dashboard."""
        self.db_manager = DatabaseManager()
        
        # Import des modules MAPAQ
        try:
            from risk_score import RiskScorer
            from risk_categorizer import RiskCategorizer
            from probability_engine_complet import ProbabilityEngine
            from integration_track_a_face_sans_dependances import MapaqFaceIntegratorSimulated
            
            self.risk_scorer = RiskScorer()
            self.risk_categorizer = RiskCategorizer()
            self.probability_engine = ProbabilityEngine()
            self.face_integrator = MapaqFaceIntegratorSimulated()
            
            logger.info("Backend dashboard MAPAQ initialisé avec succès")
        except ImportError as e:
            logger.error(f"Erreur import modules MAPAQ: {e}")
            raise
        
        # Initialisation données de démonstration
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialise des données de démonstration."""
        demo_restaurants = [
            RestaurantData(
                id="REST_001", nom="Fast Food Central", theme="fast_food", taille="grand",
                zone="montreal", adresse="123 Rue Sainte-Catherine, Montréal",
                score_risque=78.5, categorie_risque="eleve", probabilite_infraction=0.72,
                derniere_inspection="2024-01-15", prochaine_inspection="2024-02-15",
                historique_infractions=["2024-01-15", "2023-11-20", "2023-08-10"]
            ),
            RestaurantData(
                id="REST_002", nom="Restaurant Le Gourmet", theme="restaurant", taille="moyen",
                zone="quebec", adresse="456 Grande Allée, Québec",
                score_risque=45.2, categorie_risque="moyen", probabilite_infraction=0.38,
                derniere_inspection="2024-01-20", prochaine_inspection="2024-03-20",
                historique_infractions=["2023-12-01"]
            ),
            RestaurantData(
                id="REST_003", nom="Café du Coin", theme="cafe", taille="petit",
                zone="laval", adresse="789 Boulevard des Laurentides, Laval",
                score_risque=22.8, categorie_risque="faible", probabilite_infraction=0.15,
                derniere_inspection="2024-01-25", prochaine_inspection="2024-04-25",
                historique_infractions=[]
            ),
            RestaurantData(
                id="REST_004", nom="Bar Sports Plus", theme="bar", taille="moyen",
                zone="montreal", adresse="321 Rue Saint-Denis, Montréal",
                score_risque=65.7, categorie_risque="eleve", probabilite_infraction=0.58,
                derniere_inspection="2024-01-10", prochaine_inspection="2024-02-10",
                historique_infractions=["2024-01-10", "2023-10-15"]
            ),
            RestaurantData(
                id="REST_005", nom="Hôtel Restaurant Prestige", theme="hotel", taille="grand",
                zone="gatineau", adresse="555 Boulevard Maloney, Gatineau",
                score_risque=89.3, categorie_risque="critique", probabilite_infraction=0.85,
                derniere_inspection="2024-01-05", prochaine_inspection="2024-01-20",
                historique_infractions=["2024-01-05", "2023-12-20", "2023-11-15", "2023-09-30"]
            )
        ]
        
        # Sauvegarde des données de démonstration
        for restaurant in demo_restaurants:
            self.db_manager.save_restaurant(restaurant)
        
        logger.info(f"Données de démonstration initialisées: {len(demo_restaurants)} restaurants")
    
    def predict_risk(self, restaurant_data: Dict[str, Any]) -> PredictionResult:
        """Effectue une prédiction de risque pour un restaurant."""
        try:
            # Calcul probabilité
            prob_result = self.probability_engine.calculate_infraction_probability(restaurant_data)
            
            # Génération score
            score_result = self.risk_scorer.compute_score(restaurant_data)
            
            # Catégorisation
            category_result = self.risk_categorizer.categorize(score_result['score_final'], restaurant_data)
            
            # Construction du résultat
            prediction = PredictionResult(
                restaurant_id=restaurant_data.get('id', 'unknown'),
                score_risque=score_result['score_final'],
                categorie_risque=category_result['categorie'],
                probabilite_infraction=prob_result['probabilite_infraction'],
                confiance=prob_result.get('niveau_confiance', 0.75),
                facteurs_risque=score_result['composantes'],
                recommandations=category_result.get('recommandations', []),
                timestamp=datetime.now().isoformat()
            )
            
            # Sauvegarde en historique
            self.db_manager.save_prediction(prediction)
            
            logger.info(f"Prédiction générée: {restaurant_data.get('nom', 'Restaurant')} - Score: {prediction.score_risque:.1f}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Erreur prédiction risque: {e}")
            # Retour prédiction par défaut en cas d'erreur
            return PredictionResult(
                restaurant_id=restaurant_data.get('id', 'unknown'),
                score_risque=50.0,
                categorie_risque='moyen',
                probabilite_infraction=0.5,
                confiance=0.5,
                facteurs_risque={'erreur': 1.0},
                recommandations=['Erreur de calcul - Vérifier les données'],
                timestamp=datetime.now().isoformat()
            )
    
    def get_historical_data(self, restaurant_id: Optional[str] = None, 
                          days: int = 30) -> List[Dict[str, Any]]:
        """Récupère les données historiques de prédictions."""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Construction de la requête
                if restaurant_id:
                    query = '''
                        SELECT * FROM predictions_history 
                        WHERE restaurant_id = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    '''
                    params = (restaurant_id, (datetime.now() - timedelta(days=days)).isoformat())
                else:
                    query = '''
                        SELECT * FROM predictions_history 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    '''
                    params = ((datetime.now() - timedelta(days=days)).isoformat(),)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Formatage des résultats
                historical_data = []
                for row in rows:
                    historical_data.append({
                        'id': row[0],
                        'restaurant_id': row[1],
                        'score_risque': row[2],
                        'categorie_risque': row[3],
                        'probabilite_infraction': row[4],
                        'confiance': row[5],
                        'facteurs_risque': json.loads(row[6]) if row[6] else {},
                        'recommandations': json.loads(row[7]) if row[7] else [],
                        'timestamp': row[8]
                    })
                
                logger.info(f"Données historiques récupérées: {len(historical_data)} entrées")
                return historical_data
                
        except Exception as e:
            logger.error(f"Erreur récupération données historiques: {e}")
            return []
    
    def get_trends_data(self, period: str = "month") -> Dict[str, Any]:
        """Calcule les tendances des risques."""
        try:
            # Définition des périodes
            if period == "week":
                days = 7
            elif period == "month":
                days = 30
            elif period == "quarter":
                days = 90
            else:
                days = 30
            
            # Récupération des données historiques
            historical_data = self.get_historical_data(days=days)
            
            if not historical_data:
                return self._get_default_trends()
            
            # Calcul des tendances
            total_predictions = len(historical_data)
            
            # Distribution par catégorie
            categories = {}
            scores_by_day = {}
            
            for entry in historical_data:
                # Distribution catégories
                cat = entry['categorie_risque']
                categories[cat] = categories.get(cat, 0) + 1
                
                # Scores par jour
                date = entry['timestamp'][:10]  # YYYY-MM-DD
                if date not in scores_by_day:
                    scores_by_day[date] = []
                scores_by_day[date].append(entry['score_risque'])
            
            # Calcul moyennes par jour
            daily_averages = {}
            for date, scores in scores_by_day.items():
                daily_averages[date] = sum(scores) / len(scores)
            
            # Tendance générale (régression linéaire simple)
            dates = sorted(daily_averages.keys())
            if len(dates) >= 2:
                first_avg = daily_averages[dates[0]]
                last_avg = daily_averages[dates[-1]]
                trend_direction = "hausse" if last_avg > first_avg else "baisse"
                trend_percentage = ((last_avg - first_avg) / first_avg) * 100
            else:
                trend_direction = "stable"
                trend_percentage = 0.0
            
            trends = {
                'period': period,
                'total_predictions': total_predictions,
                'distribution_categories': categories,
                'daily_averages': daily_averages,
                'trend_direction': trend_direction,
                'trend_percentage': round(trend_percentage, 2),
                'average_score': round(sum(entry['score_risque'] for entry in historical_data) / total_predictions, 2),
                'high_risk_count': sum(1 for entry in historical_data if entry['score_risque'] >= 70),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Tendances calculées pour {period}: {total_predictions} prédictions")
            return trends
            
        except Exception as e:
            logger.error(f"Erreur calcul tendances: {e}")
            return self._get_default_trends()
    
    def _get_default_trends(self) -> Dict[str, Any]:
        """Retourne des tendances par défaut en cas d'erreur."""
        return {
            'period': 'month',
            'total_predictions': 0,
            'distribution_categories': {'faible': 0, 'moyen': 0, 'eleve': 0, 'critique': 0},
            'daily_averages': {},
            'trend_direction': 'stable',
            'trend_percentage': 0.0,
            'average_score': 50.0,
            'high_risk_count': 0,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Génère un résumé pour le dashboard."""
        try:
            restaurants = self.db_manager.get_all_restaurants()
            
            if not restaurants:
                return self._get_default_summary()
            
            # Calculs statistiques
            total_restaurants = len(restaurants)
            scores = [r.score_risque for r in restaurants if r.score_risque is not None]
            
            if scores:
                average_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
            else:
                average_score = max_score = min_score = 0.0
            
            # Distribution par catégorie
            categories = {}
            for restaurant in restaurants:
                cat = restaurant.categorie_risque or 'inconnu'
                categories[cat] = categories.get(cat, 0) + 1
            
            # Restaurants à risque élevé
            high_risk = [r for r in restaurants if r.score_risque and r.score_risque >= 70]
            
            # Prochaines inspections
            upcoming_inspections = []
            for restaurant in restaurants:
                if restaurant.prochaine_inspection:
                    upcoming_inspections.append({
                        'restaurant_id': restaurant.id,
                        'nom': restaurant.nom,
                        'date': restaurant.prochaine_inspection,
                        'score_risque': restaurant.score_risque,
                        'categorie': restaurant.categorie_risque
                    })
            
            # Tri par date
            upcoming_inspections.sort(key=lambda x: x['date'])
            
            summary = {
                'total_restaurants': total_restaurants,
                'average_score': round(average_score, 2),
                'max_score': round(max_score, 2),
                'min_score': round(min_score, 2),
                'distribution_categories': categories,
                'high_risk_count': len(high_risk),
                'upcoming_inspections': upcoming_inspections[:10],  # Top 10
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Résumé dashboard généré: {total_restaurants} restaurants")
            return summary
            
        except Exception as e:
            logger.error(f"Erreur génération résumé dashboard: {e}")
            return self._get_default_summary()
    
    def _get_default_summary(self) -> Dict[str, Any]:
        """Retourne un résumé par défaut."""
        return {
            'total_restaurants': 0,
            'average_score': 0.0,
            'max_score': 0.0,
            'min_score': 0.0,
            'distribution_categories': {},
            'high_risk_count': 0,
            'upcoming_inspections': [],
            'last_updated': datetime.now().isoformat()
        }

def demo_dashboard_backend():
    """Démonstration du backend dashboard."""
    
    print("DÉMONSTRATION BACKEND DASHBOARD MAPAQ")
    print("="*45)
    
    # Initialisation
    dashboard = MapaqDashboardBackend()
    
    print("\n--- RÉSUMÉ DASHBOARD ---")
    summary = dashboard.get_dashboard_summary()
    print(f"Total restaurants: {summary['total_restaurants']}")
    print(f"Score moyen: {summary['average_score']}")
    print(f"Restaurants à risque élevé: {summary['high_risk_count']}")
    
    print(f"\nDistribution par catégorie:")
    for cat, count in summary['distribution_categories'].items():
        print(f"  {cat.capitalize()}: {count}")
    
    print(f"\n--- TEST PRÉDICTION ---")
    restaurant_test = {
        'id': 'TEST_001',
        'nom': 'Restaurant Test Dashboard',
        'theme': 'restaurant',
        'taille': 'moyen',
        'zone': 'montreal',
        'historique_infractions': ['2024-01-01']
    }
    
    prediction = dashboard.predict_risk(restaurant_test)
    print(f"Restaurant: {restaurant_test['nom']}")
    print(f"Score: {prediction.score_risque:.1f}/100")
    print(f"Catégorie: {prediction.categorie_risque.upper()}")
    print(f"Probabilité: {prediction.probabilite_infraction:.3f}")
    print(f"Confiance: {prediction.confiance:.3f}")
    
    print(f"\n--- DONNÉES HISTORIQUES ---")
    historical = dashboard.get_historical_data(days=7)
    print(f"Prédictions derniers 7 jours: {len(historical)}")
    
    print(f"\n--- TENDANCES ---")
    trends = dashboard.get_trends_data("month")
    print(f"Période: {trends['period']}")
    print(f"Total prédictions: {trends['total_predictions']}")
    print(f"Score moyen: {trends['average_score']}")
    print(f"Tendance: {trends['trend_direction']} ({trends['trend_percentage']:.1f}%)")
    
    return dashboard

if __name__ == "__main__":
    demo_dashboard_backend()
