
"""
Module de Cartographie Interactive MAPAQ - geo_map.py
Carte interactive avec marqueurs restaurants et clustering par risque

Auteur: Mouhamed Thiaw
Date: 2025-01-25
Heures: 105-108 (Mercredi - Développement geo_map.py)
Fonctionnalités:
- Carte interactive (Leaflet/Mapbox)
- Marqueurs restaurants avec popup d'informations
- Clustering par niveau de risque
- Heatmap des risques
- Filtres temporels et géographiques
- Responsive design
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import os
import sqlite3
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RestaurantMarker:
    """Structure de données pour un marqueur de restaurant."""
    id: str
    nom: str
    latitude: float
    longitude: float
    adresse: str
    theme: str
    score_risque: float
    categorie_risque: str
    probabilite_infraction: float
    derniere_inspection: str
    nombre_infractions: int
    popup_info: Dict[str, Any]

@dataclass
class MapConfig:
    """Configuration de la carte interactive."""
    center_lat: float = 45.5017  # Montréal
    center_lng: float = -73.5673
    zoom_level: int = 11
    min_zoom: int = 8
    max_zoom: int = 18
    tile_layer: str = "OpenStreetMap"
    cluster_distance: int = 50
    heatmap_radius: int = 25

class GeoMapGenerator:
    """Générateur de cartes interactives pour les restaurants MAPAQ."""
    
    def __init__(self, config: Optional[MapConfig] = None):
        """Initialise le générateur de cartes."""
        self.config = config or MapConfig()
        self.restaurants_data = []
        self.risk_clusters = {
            'Faible': [],
            'Modéré': [],
            'Élevé': [],
            'Critique': []
        }
        
        # Configuration des couleurs par risque
        self.risk_colors = {
            'Faible': '#28a745',      # Vert
            'Modéré': '#ffc107',      # Jaune
            'Élevé': '#fd7e14',       # Orange
            'Critique': '#dc3545'     # Rouge
        }
        
        # Configuration des icônes
        self.risk_icons = {
            'Faible': 'check-circle',
            'Modéré': 'exclamation-triangle',
            'Élevé': 'exclamation-circle',
            'Critique': 'times-circle'
        }
        
        logger.info("Générateur de cartes MAPAQ initialisé")
    
    def load_restaurant_data(self, data_source: Any) -> bool:
        """Charge les données des restaurants depuis diverses sources."""
        try:
            if isinstance(data_source, str):
                # Chargement depuis fichier JSON
                with open(data_source, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
            elif isinstance(data_source, list):
                # Données directes
                raw_data = data_source
            else:
                # Base de données ou autre source
                raw_data = self._load_from_database(data_source)
            
            # Conversion en marqueurs
            self.restaurants_data = []
            for restaurant in raw_data:
                marker = self._create_restaurant_marker(restaurant)
                if marker:
                    self.restaurants_data.append(marker)
                    # Ajout au cluster approprié
                    risk_category = marker.categorie_risque
                    if risk_category in self.risk_clusters:
                        self.risk_clusters[risk_category].append(marker)
            
            logger.info(f"Chargé {len(self.restaurants_data)} restaurants sur la carte")
            return True
            
        except Exception as e:
            logger.error(f"Erreur chargement données restaurants: {e}")
            # Génération de données de démonstration
            self._generate_demo_data()
            return False
    
    def _create_restaurant_marker(self, restaurant_data: Dict[str, Any]) -> Optional[RestaurantMarker]:
        """Crée un marqueur de restaurant à partir des données."""
        try:
            # Validation des coordonnées
            lat = float(restaurant_data.get('latitude', 0))
            lng = float(restaurant_data.get('longitude', 0))
            
            if lat == 0 or lng == 0:
                return None
            
            # Création du popup d'informations
            popup_info = {
                'nom': restaurant_data.get('nom', 'Restaurant Inconnu'),
                'adresse': restaurant_data.get('adresse', 'Adresse non disponible'),
                'theme': restaurant_data.get('theme', 'Non classifié'),
                'score_risque': restaurant_data.get('score_risque', 0.0),
                'categorie_risque': restaurant_data.get('categorie_risque', 'Modéré'),
                'probabilite_infraction': restaurant_data.get('probabilite_infraction', 0.0),
                'derniere_inspection': restaurant_data.get('derniere_inspection', 'Inconnue'),
                'nombre_infractions': restaurant_data.get('nombre_infractions', 0),
                'details_infractions': restaurant_data.get('details_infractions', [])
            }
            
            return RestaurantMarker(
                id=restaurant_data.get('id', f"rest_{len(self.restaurants_data)}"),
                nom=popup_info['nom'],
                latitude=lat,
                longitude=lng,
                adresse=popup_info['adresse'],
                theme=popup_info['theme'],
                score_risque=popup_info['score_risque'],
                categorie_risque=popup_info['categorie_risque'],
                probabilite_infraction=popup_info['probabilite_infraction'],
                derniere_inspection=popup_info['derniere_inspection'],
                nombre_infractions=popup_info['nombre_infractions'],
                popup_info=popup_info
            )
            
        except Exception as e:
            logger.error(f"Erreur création marqueur restaurant: {e}")
            return None
    
    def _generate_demo_data(self):
        """Génère des données de démonstration pour Montréal."""
        demo_restaurants = [
            {
                'id': 'demo_1',
                'nom': 'Restaurant Chez Mario',
                'latitude': 45.5088,
                'longitude': -73.5878,
                'adresse': '123 Rue Saint-Denis, Montréal',
                'theme': 'Italien',
                'score_risque': 0.25,
                'categorie_risque': 'Faible',
                'probabilite_infraction': 0.15,
                'derniere_inspection': '2024-12-15',
                'nombre_infractions': 0
            },
            {
                'id': 'demo_2',
                'nom': 'Sushi Express',
                'latitude': 45.5017,
                'longitude': -73.5673,
                'adresse': '456 Boulevard Saint-Laurent, Montréal',
                'theme': 'Asiatique',
                'score_risque': 0.65,
                'categorie_risque': 'Modéré',
                'probabilite_infraction': 0.45,
                'derniere_inspection': '2024-11-20',
                'nombre_infractions': 2
            },
            {
                'id': 'demo_3',
                'nom': 'BBQ Palace',
                'latitude': 45.4995,
                'longitude': -73.5848,
                'adresse': '789 Rue Sainte-Catherine, Montréal',
                'theme': 'Américain',
                'score_risque': 0.85,
                'categorie_risque': 'Élevé',
                'probabilite_infraction': 0.75,
                'derniere_inspection': '2024-10-10',
                'nombre_infractions': 5
            },
            {
                'id': 'demo_4',
                'nom': 'Fast Burger',
                'latitude': 45.5150,
                'longitude': -73.5550,
                'adresse': '321 Avenue du Parc, Montréal',
                'theme': 'Fast Food',
                'score_risque': 0.95,
                'categorie_risque': 'Critique',
                'probabilite_infraction': 0.90,
                'derniere_inspection': '2024-09-05',
                'nombre_infractions': 8
            }
        ]
        
        self.restaurants_data = []
        for restaurant in demo_restaurants:
            marker = self._create_restaurant_marker(restaurant)
            if marker:
                self.restaurants_data.append(marker)
                self.risk_clusters[marker.categorie_risque].append(marker)
        
        logger.info("Données de démonstration générées")
    
    def generate_leaflet_map(self, output_file: str = "mapaq_interactive_map.html") -> str:
        """Génère une carte interactive Leaflet complète."""
        try:
            # Template HTML avec Leaflet
            html_template = self._get_leaflet_template()
            
            # Génération des données JavaScript
            markers_js = self._generate_markers_javascript()
            clusters_js = self._generate_clusters_javascript()
            heatmap_js = self._generate_heatmap_javascript()
            
            # Remplacement des placeholders
            html_content = html_template.replace('{{MARKERS_DATA}}', markers_js)
            html_content = html_content.replace('{{CLUSTERS_DATA}}', clusters_js)
            html_content = html_content.replace('{{HEATMAP_DATA}}', heatmap_js)
            html_content = html_content.replace('{{CENTER_LAT}}', str(self.config.center_lat))
            html_content = html_content.replace('{{CENTER_LNG}}', str(self.config.center_lng))
            html_content = html_content.replace('{{ZOOM_LEVEL}}', str(self.config.zoom_level))
            
            # Sauvegarde du fichier
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Carte interactive générée: {output_path.absolute()}")
            return str(output_path.absolute())
            
        except Exception as e:
            logger.error(f"Erreur génération carte Leaflet: {e}")
            return ""
    
    def _generate_markers_javascript(self) -> str:
        """Génère le JavaScript pour les marqueurs."""
        markers_data = []
        
        for restaurant in self.restaurants_data:
            marker_data = {
                'id': restaurant.id,
                'lat': restaurant.latitude,
                'lng': restaurant.longitude,
                'nom': restaurant.nom,
                'adresse': restaurant.adresse,
                'theme': restaurant.theme,
                'score_risque': restaurant.score_risque,
                'categorie_risque': restaurant.categorie_risque,
                'probabilite_infraction': restaurant.probabilite_infraction,
                'color': self.risk_colors[restaurant.categorie_risque],
                'icon': self.risk_icons[restaurant.categorie_risque],
                'popup_html': self._generate_popup_html(restaurant)
            }
            markers_data.append(marker_data)
        
        return json.dumps(markers_data, ensure_ascii=False, indent=2)
    
    def _generate_clusters_javascript(self) -> str:
        """Génère le JavaScript pour les clusters par risque."""
        clusters_data = {}
        
        for risk_level, restaurants in self.risk_clusters.items():
            if restaurants:
                clusters_data[risk_level] = {
                    'count': len(restaurants),
                    'color': self.risk_colors[risk_level],
                    'restaurants': [
                        {
                            'id': r.id,
                            'lat': r.latitude,
                            'lng': r.longitude,
                            'nom': r.nom,
                            'score_risque': r.score_risque
                        }
                        for r in restaurants
                    ]
                }
        
        return json.dumps(clusters_data, ensure_ascii=False, indent=2)
    
    def _generate_heatmap_javascript(self) -> str:
        """Génère le JavaScript pour la heatmap des risques."""
        heatmap_data = []
        
        for restaurant in self.restaurants_data:
            # Intensité basée sur le score de risque
            intensity = restaurant.score_risque
            heatmap_data.append([
                restaurant.latitude,
                restaurant.longitude,
                intensity
            ])
        
        return json.dumps(heatmap_data, ensure_ascii=False, indent=2)
    
    def _generate_popup_html(self, restaurant: RestaurantMarker) -> str:
        """Génère le HTML pour le popup d'un restaurant."""
        risk_color = self.risk_colors[restaurant.categorie_risque]
        
        popup_html = f"""
        <div class="restaurant-popup">
            <h3 style="color: {risk_color}; margin: 0 0 10px 0;">
                <i class="fas fa-{self.risk_icons[restaurant.categorie_risque]}"></i>
                {restaurant.nom}
            </h3>
            <div class="popup-content">
                <p><strong>Adresse:</strong> {restaurant.adresse}</p>
                <p><strong>Thème:</strong> {restaurant.theme}</p>
                <p><strong>Catégorie de risque:</strong> 
                   <span style="color: {risk_color}; font-weight: bold;">
                       {restaurant.categorie_risque}
                   </span>
                </p>
                <p><strong>Score de risque:</strong> {restaurant.score_risque:.2f}/1.00</p>
                <p><strong>Probabilité d'infraction:</strong> {restaurant.probabilite_infraction:.1%}</p>
                <p><strong>Dernière inspection:</strong> {restaurant.derniere_inspection}</p>
                <p><strong>Nombre d'infractions:</strong> {restaurant.nombre_infractions}</p>
            </div>
            <div class="popup-actions">
                <button onclick="showRestaurantDetails('{restaurant.id}')" 
                        class="btn btn-info btn-sm">
                    Détails complets
                </button>
                <button onclick="scheduleInspection('{restaurant.id}')" 
                        class="btn btn-warning btn-sm">
                    Programmer inspection
                </button>
            </div>
        </div>
        """
        
        return popup_html.strip()
    
    def _get_leaflet_template(self) -> str:
        """Retourne le template HTML Leaflet complet."""
        return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carte Interactive MAPAQ - Risques Sanitaires</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        #map { height: 100vh; width: 100%; }
        .map-controls { position: absolute; top: 10px; right: 10px; z-index: 1000; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 300px; }
        .restaurant-popup { min-width: 250px; font-size: 14px; }
        .popup-content p { margin: 5px 0; }
        .popup-actions { margin-top: 10px; text-align: center; }
        .popup-actions button { margin: 2px; }
        .legend { position: absolute; bottom: 20px; left: 20px; z-index: 1000; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .legend-item { display: flex; align-items: center; margin: 5px 0; }
        .legend-color { width: 20px; height: 20px; border-radius: 50%; margin-right: 10px; }
        .stats-panel { position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-width: 200px; }
        @media (max-width: 768px) { .map-controls, .stats-panel { position: relative; width: 100%; margin: 10px 0; } #map { height: 70vh; } }
    </style>
</head>
<body>
    <!-- Panneau de statistiques -->
    <div class="stats-panel">
        <h5><i class="fas fa-chart-bar"></i> Statistiques</h5>
        <div id="stats-content">
            <p><strong>Total restaurants:</strong> <span id="total-count">0</span></p>
            <p><strong>Risque critique:</strong> <span id="critical-count">0</span></p>
            <p><strong>Risque élevé:</strong> <span id="high-count">0</span></p>
            <p><strong>Risque modéré:</strong> <span id="medium-count">0</span></p>
            <p><strong>Risque faible:</strong> <span id="low-count">0</span></p>
        </div>
    </div>
    
    <!-- Contrôles de la carte -->
    <div class="map-controls">
        <h5><i class="fas fa-sliders-h"></i> Contrôles</h5>
        <div class="mb-3">
            <label class="form-label">Affichage:</label>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="show-markers" checked>
                <label class="form-check-label" for="show-markers">Marqueurs</label>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="show-clusters" checked>
                <label class="form-check-label" for="show-clusters">Clusters</label>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="show-heatmap">
                <label class="form-check-label" for="show-heatmap">Heatmap</label>
            </div>
        </div>
        <div class="mb-3">
            <label for="risk-filter" class="form-label">Filtrer par risque:</label>
            <select class="form-select" id="risk-filter">
                <option value="all">Tous les niveaux</option>
                <option value="Critique">Critique uniquement</option>
                <option value="Élevé">Élevé uniquement</option>
                <option value="Modéré">Modéré uniquement</option>
                <option value="Faible">Faible uniquement</option>
            </select>
        </div>
        <button class="btn btn-primary btn-sm" onclick="resetMap()">
            <i class="fas fa-home"></i> Réinitialiser
        </button>
    </div>
    
    <!-- Carte principale -->
    <div id="map"></div>
    
    <!-- Légende -->
    <div class="legend">
        <h6><i class="fas fa-info-circle"></i> Niveaux de risque</h6>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #dc3545;"></div>
            <span>Critique (≥ 0.8)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #fd7e14;"></div>
            <span>Élevé (0.6 - 0.8)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #ffc107;"></div>
            <span>Modéré (0.3 - 0.6)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #28a745;"></div>
            <span>Faible (< 0.3)</span>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Données des restaurants
        const markersData = {{MARKERS_DATA}};
        const clustersData = {{CLUSTERS_DATA}};
        const heatmapData = {{HEATMAP_DATA}};
        
        // Configuration de la carte
        const mapConfig = {
            center: [{{CENTER_LAT}}, {{CENTER_LNG}}],
            zoom: {{ZOOM_LEVEL}},
            minZoom: 8,
            maxZoom: 18
        };
        
        // Initialisation de la carte
        const map = L.map('map').setView(mapConfig.center, mapConfig.zoom);
        
        // Couche de tuiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors | MAPAQ Track-B',
            minZoom: mapConfig.minZoom,
            maxZoom: mapConfig.maxZoom
        }).addTo(map);
        
        // Groupes de couches
        const markersGroup = L.markerClusterGroup({
            chunkedLoading: true,
            maxClusterRadius: 50
        });
        const heatmapGroup = L.layerGroup();
        
        // Variables globales
        let allMarkers = [];
        let currentFilter = 'all';
        
        // Initialisation
        initializeMap();
        updateStatistics();
        
        function initializeMap() {
            // Création des marqueurs
            markersData.forEach(restaurant => {
                const marker = createRestaurantMarker(restaurant);
                allMarkers.push({marker: marker, data: restaurant});
                markersGroup.addLayer(marker);
            });
            
            // Ajout des groupes à la carte
            map.addLayer(markersGroup);
            
            // Création de la heatmap
            if (heatmapData.length > 0) {
                const heatLayer = L.heatLayer(heatmapData, {
                    radius: 25,
                    blur: 15,
                    maxZoom: 17,
                    gradient: {
                        0.0: '#28a745',
                        0.3: '#ffc107', 
                        0.6: '#fd7e14',
                        0.8: '#dc3545'
                    }
                });
                heatmapGroup.addLayer(heatLayer);
            }
        }
        
        function createRestaurantMarker(restaurant) {
            // Icône personnalisée basée sur le risque
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="
                    background-color: ${restaurant.color};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                ">
                    <i class="fas fa-${restaurant.icon}"></i>
                </div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15],
                popupAnchor: [0, -15]
            });
            
            const marker = L.marker([restaurant.lat, restaurant.lng], {icon: icon});
            marker.bindPopup(restaurant.popup_html, {
                maxWidth: 350,
                className: 'custom-popup'
            });
            
            return marker;
        }
        
        function updateStatistics() {
            const stats = {
                total: markersData.length,
                critical: markersData.filter(r => r.categorie_risque === 'Critique').length,
                high: markersData.filter(r => r.categorie_risque === 'Élevé').length,
                medium: markersData.filter(r => r.categorie_risque === 'Modéré').length,
                low: markersData.filter(r => r.categorie_risque === 'Faible').length
            };
            
            document.getElementById('total-count').textContent = stats.total;
            document.getElementById('critical-count').textContent = stats.critical;
            document.getElementById('high-count').textContent = stats.high;
            document.getElementById('medium-count').textContent = stats.medium;
            document.getElementById('low-count').textContent = stats.low;
        }
        
        // Gestionnaires d'événements
        document.getElementById('show-markers').addEventListener('change', function(e) {
            if (e.target.checked) {
                map.addLayer(markersGroup);
            } else {
                map.removeLayer(markersGroup);
            }
        });
        
        document.getElementById('show-clusters').addEventListener('change', function(e) {
            // Toggle clustering
            if (e.target.checked) {
                markersGroup.options.disableClusteringAtZoom = null;
            } else {
                markersGroup.options.disableClusteringAtZoom = 1;
            }
            markersGroup.refreshClusters();
        });
        
        document.getElementById('show-heatmap').addEventListener('change', function(e) {
            if (e.target.checked) {
                map.addLayer(heatmapGroup);
            } else {
                map.removeLayer(heatmapGroup);
            }
        });
        
        document.getElementById('risk-filter').addEventListener('change', function(e) {
            currentFilter = e.target.value;
            filterMarkers();
        });
        
        function filterMarkers() {
            markersGroup.clearLayers();
            
            const filteredMarkers = allMarkers.filter(item => {
                if (currentFilter === 'all') return true;
                return item.data.categorie_risque === currentFilter;
            });
            
            filteredMarkers.forEach(item => {
                markersGroup.addLayer(item.marker);
            });
        }
        
        function resetMap() {
            map.setView(mapConfig.center, mapConfig.zoom);
            document.getElementById('risk-filter').value = 'all';
            currentFilter = 'all';
            filterMarkers();
        }
        
        // Fonctions pour les popups
        function showRestaurantDetails(restaurantId) {
            const restaurant = markersData.find(r => r.id === restaurantId);
            if (restaurant) {
                alert(`Détails complets pour: ${restaurant.nom}\\n\\nCette fonctionnalité sera intégrée au dashboard principal.`);
            }
        }
        
        function scheduleInspection(restaurantId) {
            const restaurant = markersData.find(r => r.id === restaurantId);
            if (restaurant) {
                alert(`Programmer une inspection pour: ${restaurant.nom}\\n\\nCette fonctionnalité sera intégrée au système de gestion.`);
            }
        }
    </script>
</body>
</html>
        """

# ========== CLASSE LEGACY POUR COMPATIBILITÉ ==========

class GeoMap:
    """Classe legacy pour compatibilité avec l'ancien code."""
    
    def __init__(self, geocoded_data):
        """Initialise avec les données géocodées."""
        self.geocoded_data = geocoded_data
        self.generator = GeoMapGenerator()
        
        # Chargement des données si disponibles
        if geocoded_data:
            self.generator.load_restaurant_data(geocoded_data)
    
    def render_map(self, output_file: str = "mapaq_legacy_map.html") -> str:
        """Génère une carte avec l'interface legacy."""
        return self.generator.generate_leaflet_map(output_file)

# ========== FONCTIONS UTILITAIRES ==========

def create_demo_map(output_file: str = "mapaq_demo_map.html") -> str:
    """Crée une carte de démonstration avec des données simulées."""
    generator = GeoMapGenerator()
    generator._generate_demo_data()
    return generator.generate_leaflet_map(output_file)

def demo_geo_map():
    """Démonstration du module de cartographie MAPAQ."""
    print("=== DÉMONSTRATION GEO_MAP.PY ===")
    print("Génération d'une carte interactive MAPAQ...")
    
    try:
        # Création du générateur
        generator = GeoMapGenerator()
        
        # Génération de données de démonstration
        generator._generate_demo_data()
        
        # Génération de la carte
        map_file = generator.generate_leaflet_map("demo_mapaq_interactive_map.html")
        
        print(f"✅ Carte interactive générée: {map_file}")
        print("\nFonctionnalités disponibles:")
        print("- Marqueurs colorés par niveau de risque")
        print("- Clustering automatique des restaurants")
        print("- Heatmap des risques")
        print("- Filtres par catégorie de risque")
        print("- Popups informatifs avec détails restaurants")
        print("- Interface responsive (mobile/desktop)")
        
        print(f"\n📊 Statistiques:")
        print(f"- Total restaurants: {len(generator.restaurants_data)}")
        for risk_level, restaurants in generator.risk_clusters.items():
            print(f"- {risk_level}: {len(restaurants)} restaurants")
        
        return map_file
        
    except Exception as e:
        logger.error(f"Erreur démonstration geo_map: {e}")
        return ""

if __name__ == "__main__":
    demo_geo_map()
