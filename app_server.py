"""
Serveur Flask pour Dashboard MAPAQ Interactif
Application web complète avec API REST et interface interactive

Auteur: Cascade AI Assistant
Date: 2025-11-14
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify, send_from_directory
import os
import random

# Import du backend dashboard
try:
    from dashboard import MapaqDashboardBackend, RestaurantData
except ImportError:
    print("⚠️ Module dashboard non trouvé - Mode simulation activé")
    MapaqDashboardBackend = None
    RestaurantData = None

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation Flask
app = Flask(__name__, static_folder='.')

# CORS manuel (sans flask-cors)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

app.config['SECRET_KEY'] = 'dev-secret-key-mapaq-2025'

# Initialisation backend
dashboard_backend = None
if MapaqDashboardBackend:
    try:
        dashboard_backend = MapaqDashboardBackend()
    except Exception as e:
        logger.error(f"Erreur initialisation backend: {e}")
        print(f"⚠️ Backend non initialisé: {e}")

# ========== GÉNÉRATION DE DONNÉES DÉMO ==========

def generate_demo_data():
    """Génère des données de démonstration pour le dashboard."""
    
    restaurants_demo = [
        {
            'id': 'REST_001',
            'nom': 'La Trattoria Bella',
            'theme': 'italien',
            'taille': 'moyen',
            'zone': 'Plateau Mont-Royal',
            'adresse': '3456 Rue Saint-Denis, Montréal',
            'score_risque': 85.5,
            'categorie_risque': 'critique',
            'probabilite_infraction': 0.82,
            'derniere_inspection': '2024-10-15',
            'prochaine_inspection': '2024-12-01',
            'historique_infractions': ['2024-08-10', '2024-06-15', '2024-03-20']
        },
        {
            'id': 'REST_002',
            'nom': 'Sushi Express',
            'theme': 'asiatique',
            'taille': 'petit',
            'zone': 'Centre-ville',
            'adresse': '1234 Rue Sainte-Catherine, Montréal',
            'score_risque': 72.3,
            'categorie_risque': 'eleve',
            'probabilite_infraction': 0.68,
            'derniere_inspection': '2024-11-01',
            'prochaine_inspection': '2025-01-15',
            'historique_infractions': ['2024-09-05', '2024-05-12']
        },
        {
            'id': 'REST_003',
            'nom': 'Le Bistro Français',
            'theme': 'francais',
            'taille': 'moyen',
            'zone': 'Vieux-Montréal',
            'adresse': '789 Rue Notre-Dame, Montréal',
            'score_risque': 45.2,
            'categorie_risque': 'moyen',
            'probabilite_infraction': 0.42,
            'derniere_inspection': '2024-10-20',
            'prochaine_inspection': '2025-02-10',
            'historique_infractions': ['2024-04-18']
        },
        {
            'id': 'REST_004',
            'nom': 'Burger Palace',
            'theme': 'americain',
            'taille': 'grand',
            'zone': 'Westmount',
            'adresse': '5678 Avenue Greene, Westmount',
            'score_risque': 28.7,
            'categorie_risque': 'faible',
            'probabilite_infraction': 0.25,
            'derniere_inspection': '2024-11-05',
            'prochaine_inspection': '2025-03-15',
            'historique_infractions': []
        },
        {
            'id': 'REST_005',
            'nom': 'Café Artisan',
            'theme': 'cafe',
            'taille': 'petit',
            'zone': 'Mile End',
            'adresse': '2345 Avenue du Parc, Montréal',
            'score_risque': 35.8,
            'categorie_risque': 'faible',
            'probabilite_infraction': 0.32,
            'derniere_inspection': '2024-10-28',
            'prochaine_inspection': '2025-02-28',
            'historique_infractions': []
        },
        {
            'id': 'REST_006',
            'nom': 'Thai Spice',
            'theme': 'asiatique',
            'taille': 'moyen',
            'zone': 'Rosemont',
            'adresse': '4567 Rue Beaubien, Montréal',
            'score_risque': 78.9,
            'categorie_risque': 'eleve',
            'probabilite_infraction': 0.75,
            'derniere_inspection': '2024-09-15',
            'prochaine_inspection': '2024-12-15',
            'historique_infractions': ['2024-07-20', '2024-04-10']
        },
        {
            'id': 'REST_007',
            'nom': 'Pizzeria Napoli',
            'theme': 'italien',
            'taille': 'petit',
            'zone': 'Verdun',
            'adresse': '6789 Rue Wellington, Verdun',
            'score_risque': 52.4,
            'categorie_risque': 'moyen',
            'probabilite_infraction': 0.48,
            'derniere_inspection': '2024-10-10',
            'prochaine_inspection': '2025-01-20',
            'historique_infractions': ['2024-06-05']
        },
        {
            'id': 'REST_008',
            'nom': 'Le Grill BBQ',
            'theme': 'americain',
            'taille': 'grand',
            'zone': 'Laval',
            'adresse': '8901 Boulevard Saint-Martin, Laval',
            'score_risque': 91.2,
            'categorie_risque': 'critique',
            'probabilite_infraction': 0.89,
            'derniere_inspection': '2024-09-01',
            'prochaine_inspection': '2024-11-20',
            'historique_infractions': ['2024-08-15', '2024-06-20', '2024-04-05', '2024-01-10']
        },
        {
            'id': 'REST_009',
            'nom': 'Boulangerie Artisanale',
            'theme': 'boulangerie',
            'taille': 'petit',
            'zone': 'Outremont',
            'adresse': '1234 Avenue Laurier, Outremont',
            'score_risque': 22.5,
            'categorie_risque': 'faible',
            'probabilite_infraction': 0.18,
            'derniere_inspection': '2024-11-08',
            'prochaine_inspection': '2025-04-01',
            'historique_infractions': []
        },
        {
            'id': 'REST_010',
            'nom': 'Ramen House',
            'theme': 'asiatique',
            'taille': 'moyen',
            'zone': 'Chinatown',
            'adresse': '5678 Boulevard Saint-Laurent, Montréal',
            'score_risque': 88.7,
            'categorie_risque': 'critique',
            'probabilite_infraction': 0.85,
            'derniere_inspection': '2024-08-25',
            'prochaine_inspection': '2024-11-25',
            'historique_infractions': ['2024-07-10', '2024-05-15', '2024-02-20']
        },
        {
            'id': 'REST_011',
            'nom': 'Steakhouse Premium',
            'theme': 'americain',
            'taille': 'grand',
            'zone': 'Downtown',
            'adresse': '9012 Rue Peel, Montréal',
            'score_risque': 38.9,
            'categorie_risque': 'faible',
            'probabilite_infraction': 0.35,
            'derniere_inspection': '2024-10-30',
            'prochaine_inspection': '2025-02-15',
            'historique_infractions': []
        },
        {
            'id': 'REST_012',
            'nom': 'Taco Fiesta',
            'theme': 'mexicain',
            'taille': 'moyen',
            'zone': 'Hochelaga',
            'adresse': '3456 Rue Ontario, Montréal',
            'score_risque': 65.3,
            'categorie_risque': 'moyen',
            'probabilite_infraction': 0.62,
            'derniere_inspection': '2024-09-20',
            'prochaine_inspection': '2024-12-20',
            'historique_infractions': ['2024-06-30', '2024-03-15']
        },
        {
            'id': 'REST_013',
            'nom': 'Pâtisserie Délice',
            'theme': 'boulangerie',
            'taille': 'petit',
            'zone': 'Westmount',
            'adresse': '7890 Rue Sherbrooke, Westmount',
            'score_risque': 19.8,
            'categorie_risque': 'faible',
            'probabilite_infraction': 0.15,
            'derniere_inspection': '2024-11-10',
            'prochaine_inspection': '2025-04-10',
            'historique_infractions': []
        },
        {
            'id': 'REST_014',
            'nom': 'Indian Curry Palace',
            'theme': 'indien',
            'taille': 'moyen',
            'zone': 'Côte-des-Neiges',
            'adresse': '4567 Chemin de la Côte-des-Neiges, Montréal',
            'score_risque': 58.6,
            'categorie_risque': 'moyen',
            'probabilite_infraction': 0.55,
            'derniere_inspection': '2024-10-05',
            'prochaine_inspection': '2025-01-05',
            'historique_infractions': ['2024-07-15']
        },
        {
            'id': 'REST_015',
            'nom': 'Greek Taverna',
            'theme': 'grec',
            'taille': 'moyen',
            'zone': 'Parc-Extension',
            'adresse': '6789 Avenue du Parc, Montréal',
            'score_risque': 42.1,
            'categorie_risque': 'moyen',
            'probabilite_infraction': 0.38,
            'derniere_inspection': '2024-10-25',
            'prochaine_inspection': '2025-02-01',
            'historique_infractions': []
        }
    ]
    
    # Sauvegarder dans la base de données
    if dashboard_backend and RestaurantData:
        for resto_data in restaurants_demo:
            restaurant = RestaurantData(
                id=resto_data['id'],
                nom=resto_data['nom'],
                theme=resto_data['theme'],
                taille=resto_data['taille'],
                zone=resto_data['zone'],
                adresse=resto_data['adresse'],
                score_risque=resto_data['score_risque'],
                categorie_risque=resto_data['categorie_risque'],
                probabilite_infraction=resto_data['probabilite_infraction'],
                derniere_inspection=resto_data['derniere_inspection'],
                prochaine_inspection=resto_data['prochaine_inspection'],
                historique_infractions=resto_data['historique_infractions']
            )
            dashboard_backend.db_manager.save_restaurant(restaurant)
        
        logger.info(f"✅ {len(restaurants_demo)} restaurants de démonstration générés")
    else:
        logger.warning("⚠️ Backend non disponible - données de démo non générées")
    
    return restaurants_demo

# Générer les données au démarrage
demo_restaurants = generate_demo_data()

# ========== ROUTES API ==========

@app.route('/')
def index():
    """Page d'accueil - redirige vers le dashboard."""
    return send_from_directory('.', 'mapaq_dashboard_interactive.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérification de santé du serveur."""
    return jsonify({
        'status': 'healthy',
        'service': 'MAPAQ Dashboard API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/dashboard', methods=['GET'])
def get_dashboard_data():
    """Récupère toutes les données du dashboard."""
    try:
        if dashboard_backend:
            summary = dashboard_backend.get_dashboard_summary()
            restaurants = dashboard_backend.db_manager.get_all_restaurants()
            restaurants_list = restaurants
        else:
            # Utiliser les données démo
            restaurants_list = demo_restaurants
        
        # Calcul des statistiques en temps réel
        total = len(restaurants_list)
        if dashboard_backend:
            scores = [r.score_risque for r in restaurants_list if r.score_risque]
        else:
            scores = [r['score_risque'] for r in restaurants_list]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Distribution par catégorie
        categories = {'critique': 0, 'eleve': 0, 'moyen': 0, 'faible': 0}
        for r in restaurants_list:
            cat = r.categorie_risque if dashboard_backend else r['categorie_risque']
            if cat in categories:
                categories[cat] += 1
        
        # Tendances (simulation)
        last_week_avg = avg_score - random.uniform(-5, 5)
        trend = avg_score - last_week_avg
        
        response = {
            'stats': {
                'total_restaurants': total,
                'score_moyen': round(avg_score, 1),
                'risque_eleve': categories['eleve'],
                'critique': categories['critique'],
                'trend': round(trend, 1)
            },
            'distribution': categories,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Erreur récupération dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/restaurants', methods=['GET'])
def get_restaurants():
    """Récupère la liste des restaurants avec filtres optionnels."""
    try:
        # Paramètres de filtrage
        categorie = request.args.get('categorie', None)
        zone = request.args.get('zone', None)
        search = request.args.get('search', '').lower()
        sort_by = request.args.get('sort_by', 'score_risque')
        order = request.args.get('order', 'desc')
        
        # Récupération des restaurants
        if dashboard_backend:
            restaurants = dashboard_backend.db_manager.get_all_restaurants()
        else:
            restaurants = demo_restaurants
        
        # Filtrage
        filtered = []
        for r in restaurants:
            # Accès aux attributs selon le type (objet ou dict)
            if dashboard_backend:
                r_id, r_nom, r_theme, r_taille, r_zone, r_adresse = r.id, r.nom, r.theme, r.taille, r.zone, r.adresse
                r_score, r_cat, r_prob = r.score_risque, r.categorie_risque, r.probabilite_infraction
                r_derniere, r_prochaine, r_hist = r.derniere_inspection, r.prochaine_inspection, r.historique_infractions
            else:
                r_id, r_nom, r_theme, r_taille, r_zone, r_adresse = r['id'], r['nom'], r['theme'], r['taille'], r['zone'], r['adresse']
                r_score, r_cat, r_prob = r['score_risque'], r['categorie_risque'], r['probabilite_infraction']
                r_derniere, r_prochaine, r_hist = r['derniere_inspection'], r['prochaine_inspection'], r['historique_infractions']
            
            # Filtre par catégorie
            if categorie and r_cat != categorie:
                continue
            
            # Filtre par zone
            if zone and r_zone != zone:
                continue
            
            # Recherche textuelle
            if search:
                searchable = f"{r_nom} {r_zone} {r_theme} {r_adresse}".lower()
                if search not in searchable:
                    continue
            
            filtered.append({
                'id': r_id,
                'nom': r_nom,
                'theme': r_theme,
                'taille': r_taille,
                'zone': r_zone,
                'adresse': r_adresse,
                'score_risque': round(r_score, 1) if r_score else 0,
                'categorie_risque': r_cat,
                'probabilite_infraction': round(r_prob, 2) if r_prob else 0,
                'derniere_inspection': r_derniere,
                'prochaine_inspection': r_prochaine,
                'nb_infractions': len(r_hist)
            })
        
        # Tri
        reverse = (order == 'desc')
        if sort_by == 'score_risque':
            filtered.sort(key=lambda x: x['score_risque'], reverse=reverse)
        elif sort_by == 'nom':
            filtered.sort(key=lambda x: x['nom'], reverse=reverse)
        elif sort_by == 'derniere_inspection':
            filtered.sort(key=lambda x: x['derniere_inspection'] or '', reverse=reverse)
        
        return jsonify({
            'restaurants': filtered,
            'total': len(filtered),
            'filters_applied': {
                'categorie': categorie,
                'zone': zone,
                'search': search
            }
        })
    
    except Exception as e:
        logger.error(f"Erreur récupération restaurants: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/restaurant/<restaurant_id>', methods=['GET'])
def get_restaurant_details(restaurant_id):
    """Récupère les détails complets d'un restaurant."""
    try:
        restaurant = dashboard_backend.db_manager.get_restaurant(restaurant_id)
        
        if not restaurant:
            return jsonify({'error': 'Restaurant non trouvé'}), 404
        
        # Récupération de l'historique des prédictions
        historical = dashboard_backend.get_historical_data(restaurant_id=restaurant_id, days=90)
        
        response = {
            'id': restaurant.id,
            'nom': restaurant.nom,
            'theme': restaurant.theme,
            'taille': restaurant.taille,
            'zone': restaurant.zone,
            'adresse': restaurant.adresse,
            'score_risque': round(restaurant.score_risque, 1) if restaurant.score_risque else 0,
            'categorie_risque': restaurant.categorie_risque,
            'probabilite_infraction': round(restaurant.probabilite_infraction, 3) if restaurant.probabilite_infraction else 0,
            'derniere_inspection': restaurant.derniere_inspection,
            'prochaine_inspection': restaurant.prochaine_inspection,
            'historique_infractions': restaurant.historique_infractions,
            'historique_predictions': historical[:10],  # 10 dernières
            'recommandations': generate_recommendations(restaurant)
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Erreur récupération détails restaurant: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/charts/distribution', methods=['GET'])
def get_distribution_chart():
    """Données pour le graphique de distribution."""
    try:
        restaurants = dashboard_backend.db_manager.get_all_restaurants()
        
        categories = {'critique': 0, 'eleve': 0, 'moyen': 0, 'faible': 0}
        for r in restaurants:
            if r.categorie_risque in categories:
                categories[r.categorie_risque] += 1
        
        return jsonify({
            'labels': ['Critique', 'Élevé', 'Moyen', 'Faible'],
            'data': [categories['critique'], categories['eleve'], categories['moyen'], categories['faible']],
            'backgroundColor': ['#FF6B6B', '#FFA500', '#FFD700', '#96CEB4']
        })
    
    except Exception as e:
        logger.error(f"Erreur génération graphique distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/charts/trends', methods=['GET'])
def get_trends_chart():
    """Données pour le graphique de tendances."""
    try:
        period = request.args.get('period', 'month')
        
        # Génération de données de tendances (simulation)
        if period == 'week':
            labels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
            base_score = 58
        elif period == 'month':
            labels = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
            base_score = 58
        else:  # year
            labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
            base_score = 58
        
        # Génération de données avec variation
        data = [base_score + random.uniform(-8, 8) for _ in labels]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'Score Moyen de Risque',
                'data': [round(d, 1) for d in data],
                'borderColor': '#FF6B6B',
                'backgroundColor': 'rgba(255, 107, 107, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        })
    
    except Exception as e:
        logger.error(f"Erreur génération graphique tendances: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/zones', methods=['GET'])
def get_zones():
    """Récupère la liste des zones disponibles."""
    try:
        restaurants = dashboard_backend.db_manager.get_all_restaurants()
        zones = list(set(r.zone for r in restaurants if r.zone))
        zones.sort()
        
        return jsonify({'zones': zones})
    
    except Exception as e:
        logger.error(f"Erreur récupération zones: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/predict', methods=['POST'])
def predict_risk():
    """Prédiction de risque pour un restaurant."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        
        # Prédiction
        prediction = dashboard_backend.predict_risk(data)
        
        response = {
            'restaurant_id': prediction.restaurant_id,
            'score_risque': round(prediction.score_risque, 1),
            'categorie_risque': prediction.categorie_risque,
            'probabilite_infraction': round(prediction.probabilite_infraction, 3),
            'confiance': round(prediction.confiance, 3),
            'facteurs_risque': prediction.facteurs_risque,
            'recommandations': prediction.recommandations,
            'timestamp': prediction.timestamp
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Erreur prédiction: {e}")
        return jsonify({'error': str(e)}), 500

# ========== FONCTIONS UTILITAIRES ==========

def generate_recommendations(restaurant: RestaurantData) -> List[str]:
    """Génère des recommandations basées sur le profil de risque."""
    recommendations = []
    
    if restaurant.score_risque >= 80:
        recommendations.append("🚨 Inspection urgente recommandée dans les 7 jours")
        recommendations.append("⚠️ Surveillance renforcée nécessaire")
        recommendations.append("📋 Audit complet des procédures sanitaires")
    elif restaurant.score_risque >= 60:
        recommendations.append("⚠️ Inspection prioritaire dans les 30 jours")
        recommendations.append("📊 Révision des pratiques d'hygiène")
        recommendations.append("👨‍🏫 Formation du personnel recommandée")
    elif restaurant.score_risque >= 40:
        recommendations.append("📅 Inspection de routine dans les 60 jours")
        recommendations.append("✅ Maintenir les bonnes pratiques actuelles")
    else:
        recommendations.append("✅ Excellent profil de conformité")
        recommendations.append("📅 Inspection de routine dans les 90 jours")
        recommendations.append("🏆 Peut servir de modèle pour d'autres établissements")
    
    if len(restaurant.historique_infractions) > 2:
        recommendations.append("📈 Historique d'infractions élevé - suivi rapproché")
    
    return recommendations

# ========== DÉMARRAGE SERVEUR ==========

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SERVEUR DASHBOARD MAPAQ INTERACTIF")
    print("="*60)
    print(f"📍 URL: http://127.0.0.1:5000")
    print(f"📊 Dashboard: http://127.0.0.1:5000/")
    print(f"🔌 API Health: http://127.0.0.1:5000/api/health")
    print(f"📈 API Endpoints disponibles:")
    print(f"   - GET  /api/v1/dashboard")
    print(f"   - GET  /api/v1/restaurants")
    print(f"   - GET  /api/v1/restaurant/<id>")
    print(f"   - GET  /api/v1/charts/distribution")
    print(f"   - GET  /api/v1/charts/trends")
    print(f"   - POST /api/v1/predict")
    print("="*60 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
