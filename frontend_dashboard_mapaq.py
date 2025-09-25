"""
Frontend Dashboard MAPAQ - Interface Utilisateur Moderne
Dashboard frontend avec composants React/Vue.js style (Heures 97-100)

Ce module implémente une interface utilisateur moderne pour le dashboard MAPAQ
avec composants graphiques, tableaux interactifs, et intégration API REST.

Composants principaux:
- Dashboard principal avec métriques
- Graphiques et visualisations
- Tableaux interactifs
- Filtres et recherche
- Modales de détails

Author: Mouhamed Thiaw
Date: 2025-01-14
Heures: 97-100 (Semaine 3)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Simulation d'un framework frontend (React/Vue.js style)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests non disponible - Mode simulation activé")

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION FRONTEND ==========

@dataclass
class FrontendConfig:
    """Configuration du frontend dashboard."""
    
    # API Backend
    api_base_url: str = "http://localhost:8080/api/v1"
    
    # Interface utilisateur
    theme: str = "modern"
    language: str = "fr"
    
    # Pagination
    default_page_size: int = 10
    max_page_size: int = 100
    
    # Refresh automatique
    auto_refresh_interval: int = 30  # secondes
    
    # Graphiques
    chart_colors: List[str] = None
    
    def __post_init__(self):
        if self.chart_colors is None:
            self.chart_colors = [
                "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
                "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"
            ]

# ========== COMPOSANTS DE BASE ==========

class Component:
    """Classe de base pour tous les composants frontend."""
    
    def __init__(self, component_id: str = None, css_classes: List[str] = None):
        self.component_id = component_id or f"comp_{id(self)}"
        self.css_classes = css_classes or []
        self.children = []
        self.props = {}
    
    def add_child(self, child):
        """Ajoute un composant enfant."""
        self.children.append(child)
        return self
    
    def set_prop(self, key: str, value: Any):
        """Définit une propriété du composant."""
        self.props[key] = value
        return self
    
    def render(self) -> str:
        """Rendu HTML du composant."""
        return f"<div id='{self.component_id}' class='{' '.join(self.css_classes)}'></div>"

class Card(Component):
    """Composant carte avec titre et contenu."""
    
    def __init__(self, title: str = "", content: str = "", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
        self.css_classes.extend(["card", "shadow-sm"])
    
    def render(self) -> str:
        return f"""
        <div id="{self.component_id}" class="{' '.join(self.css_classes)}">
            <div class="card-header">
                <h5 class="card-title">{self.title}</h5>
            </div>
            <div class="card-body">
                {self.content}
                {''.join([child.render() for child in self.children])}
            </div>
        </div>
        """

class StatCard(Card):
    """Carte de statistique avec valeur et tendance."""
    
    def __init__(self, title: str, value: str, change: str = "", 
                 trend: str = "neutral", icon: str = "", **kwargs):
        super().__init__(title=title, **kwargs)
        self.value = value
        self.change = change
        self.trend = trend  # up, down, neutral
        self.icon = icon
        self.css_classes.append("stat-card")
    
    def render(self) -> str:
        trend_class = f"trend-{self.trend}"
        trend_icon = {"up": "↗", "down": "↘", "neutral": "→"}.get(self.trend, "→")
        
        return f"""
        <div id="{self.component_id}" class="{' '.join(self.css_classes)}">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h6 class="card-subtitle text-muted">{self.title}</h6>
                        <h3 class="card-title">{self.value}</h3>
                        {f'<small class="{trend_class}">{trend_icon} {self.change}</small>' if self.change else ''}
                    </div>
                    {f'<div class="stat-icon">{self.icon}</div>' if self.icon else ''}
                </div>
            </div>
        </div>
        """

class Chart(Component):
    """Composant graphique générique."""
    
    def __init__(self, chart_type: str = "line", data: Dict = None, 
                 options: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.chart_type = chart_type
        self.data = data or {}
        self.options = options or {}
        self.css_classes.append("chart-container")
    
    def render(self) -> str:
        return f"""
        <div id="{self.component_id}" class="{' '.join(self.css_classes)}">
            <canvas id="{self.component_id}_canvas"></canvas>
            <script>
                // Configuration du graphique {self.chart_type}
                const ctx_{self.component_id} = document.getElementById('{self.component_id}_canvas').getContext('2d');
                const chart_{self.component_id} = new Chart(ctx_{self.component_id}, {{
                    type: '{self.chart_type}',
                    data: {json.dumps(self.data)},
                    options: {json.dumps(self.options)}
                }});
            </script>
        </div>
        """

class Table(Component):
    """Composant tableau interactif."""
    
    def __init__(self, columns: List[Dict], data: List[Dict] = None, 
                 sortable: bool = True, filterable: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.columns = columns
        self.data = data or []
        self.sortable = sortable
        self.filterable = filterable
        self.css_classes.extend(["table-responsive", "interactive-table"])
    
    def render(self) -> str:
        # En-têtes
        headers = ""
        for col in self.columns:
            sort_attr = 'data-sortable="true"' if self.sortable else ''
            headers += f'<th {sort_attr}>{col.get("title", col.get("key", ""))}</th>'
        
        # Lignes de données
        rows = ""
        for row_data in self.data:
            row = "<tr>"
            for col in self.columns:
                key = col.get("key", "")
                value = row_data.get(key, "")
                row += f"<td>{value}</td>"
            row += "</tr>"
            rows += row
        
        # Filtre de recherche
        search_input = ""
        if self.filterable:
            search_input = f"""
            <div class="table-search mb-3">
                <input type="text" class="form-control" placeholder="Rechercher..." 
                       onkeyup="filterTable('{self.component_id}_table', this.value)">
            </div>
            """
        
        return f"""
        <div id="{self.component_id}" class="{' '.join(self.css_classes)}">
            {search_input}
            <table id="{self.component_id}_table" class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>{headers}</tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

# ========== CLIENT API ==========

class APIClient:
    """Client pour communiquer avec l'API backend MAPAQ."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Effectue une requête HTTP."""
        if not REQUESTS_AVAILABLE:
            return self._simulate_request(method, endpoint, **kwargs)
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erreur API {method} {endpoint}: {e}")
            return {"success": False, "error": str(e)}
    
    def _simulate_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Simule une requête API pour les tests."""
        logger.info(f"Simulation API {method} {endpoint}")
        
        # Données simulées selon l'endpoint
        if "/health" in endpoint:
            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
            }
        elif "/dashboard" in endpoint:
            return {
                "success": True,
                "data": {
                    "total_restaurants": 25,
                    "average_score": 58.3,
                    "high_risk_count": 8,
                    "distribution_categories": {
                        "critique": 3,
                        "eleve": 5,
                        "moyen": 12,
                        "faible": 5
                    }
                }
            }
        elif "/historical" in endpoint:
            return {
                "success": True,
                "data": {
                    "historical_data": [
                        {
                            "restaurant_id": "REST_001",
                            "nom": "Restaurant Test",
                            "score_risque": 65.2,
                            "categorie_risque": "eleve",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            }
        else:
            return {"success": True, "data": {}}
    
    def get_health(self) -> Dict:
        """Vérifie la santé de l'API."""
        return self._make_request("GET", "/health")
    
    def get_dashboard_summary(self) -> Dict:
        """Récupère le résumé du dashboard."""
        return self._make_request("GET", "/dashboard")
    
    def get_historical_data(self, days: int = 30, restaurant_id: str = None) -> Dict:
        """Récupère les données historiques."""
        params = {"days": days}
        if restaurant_id:
            params["restaurant_id"] = restaurant_id
        return self._make_request("GET", "/historical", params=params)
    
    def get_trends(self, period: str = "month") -> Dict:
        """Récupère les tendances."""
        return self._make_request("GET", "/trends", params={"period": period})
    
    def predict_risk(self, restaurant_data: Dict) -> Dict:
        """Effectue une prédiction de risque."""
        return self._make_request("POST", "/predict", json=restaurant_data)

# ========== DASHBOARD PRINCIPAL ==========

class MapaqDashboard:
    """
    Dashboard principal MAPAQ avec interface moderne.
    
    Fonctionnalités:
    - Vue d'ensemble avec métriques clés
    - Graphiques de tendances
    - Tableau des restaurants
    - Filtres et recherche
    - Prédictions en temps réel
    """
    
    def __init__(self, config: FrontendConfig = None):
        self.config = config or FrontendConfig()
        self.api_client = APIClient(self.config.api_base_url)
        self.components = {}
        
        logger.info("Dashboard MAPAQ initialisé")
    
    def create_overview_section(self) -> str:
        """Crée la section vue d'ensemble avec métriques."""
        # Récupération des données
        dashboard_data = self.api_client.get_dashboard_summary()
        
        if not dashboard_data.get("success"):
            return "<div class='alert alert-danger'>Erreur chargement données</div>"
        
        data = dashboard_data.get("data", {})
        
        # Cartes de statistiques
        total_card = StatCard(
            title="Total Restaurants",
            value=str(data.get("total_restaurants", 0)),
            change="+5 ce mois",
            trend="up",
            icon="🏪",
            component_id="stat_total"
        )
        
        score_card = StatCard(
            title="Score Moyen",
            value=f"{data.get('average_score', 0):.1f}/100",
            change="-2.3 points",
            trend="down",
            icon="📊",
            component_id="stat_score"
        )
        
        risk_card = StatCard(
            title="Risque Élevé",
            value=str(data.get("high_risk_count", 0)),
            change="+2 cette semaine",
            trend="up",
            icon="⚠️",
            component_id="stat_risk"
        )
        
        distribution = data.get("distribution_categories", {})
        critical_count = distribution.get("critique", 0)
        
        critical_card = StatCard(
            title="Critique",
            value=str(critical_count),
            change="Inspection urgente",
            trend="neutral",
            icon="🚨",
            component_id="stat_critical"
        )
        
        return f"""
        <div class="row mb-4">
            <div class="col-md-3">{total_card.render()}</div>
            <div class="col-md-3">{score_card.render()}</div>
            <div class="col-md-3">{risk_card.render()}</div>
            <div class="col-md-3">{critical_card.render()}</div>
        </div>
        """
    
    def create_charts_section(self) -> str:
        """Crée la section graphiques."""
        # Données pour graphique de distribution
        dashboard_data = self.api_client.get_dashboard_summary()
        distribution = dashboard_data.get("data", {}).get("distribution_categories", {})
        
        # Graphique en secteurs - Distribution des risques
        pie_data = {
            "labels": ["Critique", "Élevé", "Moyen", "Faible"],
            "datasets": [{
                "data": [
                    distribution.get("critique", 0),
                    distribution.get("eleve", 0),
                    distribution.get("moyen", 0),
                    distribution.get("faible", 0)
                ],
                "backgroundColor": self.config.chart_colors[:4]
            }]
        }
        
        pie_chart = Chart(
            chart_type="pie",
            data=pie_data,
            options={
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Distribution des Catégories de Risque"
                    }
                }
            },
            component_id="risk_distribution_chart"
        )
        
        # Graphique linéaire - Tendances
        trends_data = self.api_client.get_trends()
        
        line_data = {
            "labels": ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun"],
            "datasets": [{
                "label": "Score Moyen",
                "data": [58, 62, 55, 60, 58, 63],
                "borderColor": self.config.chart_colors[0],
                "tension": 0.1
            }]
        }
        
        line_chart = Chart(
            chart_type="line",
            data=line_data,
            options={
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Évolution des Scores de Risque"
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "max": 100
                    }
                }
            },
            component_id="trends_chart"
        )
        
        return f"""
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        {pie_chart.render()}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        {line_chart.render()}
                    </div>
                </div>
            </div>
        </div>
        """
    
    def create_restaurants_table(self) -> str:
        """Crée le tableau des restaurants."""
        # Récupération des données historiques
        historical_data = self.api_client.get_historical_data(days=30)
        
        restaurants_data = []
        if historical_data.get("success"):
            restaurants_data = historical_data.get("data", {}).get("historical_data", [])
        
        # Données simulées si pas de données réelles
        if not restaurants_data:
            restaurants_data = [
                {
                    "nom": "Restaurant Le Gourmet",
                    "zone": "Montréal",
                    "score_risque": 45.2,
                    "categorie_risque": "Moyen",
                    "derniere_inspection": "2024-01-20"
                },
                {
                    "nom": "Fast Food Central",
                    "zone": "Québec",
                    "score_risque": 78.5,
                    "categorie_risque": "Élevé",
                    "derniere_inspection": "2024-01-15"
                },
                {
                    "nom": "Café du Coin",
                    "zone": "Laval",
                    "score_risque": 22.8,
                    "categorie_risque": "Faible",
                    "derniere_inspection": "2024-01-25"
                }
            ]
        
        # Configuration des colonnes
        columns = [
            {"key": "nom", "title": "Restaurant"},
            {"key": "zone", "title": "Zone"},
            {"key": "score_risque", "title": "Score"},
            {"key": "categorie_risque", "title": "Catégorie"},
            {"key": "derniere_inspection", "title": "Dernière Inspection"}
        ]
        
        restaurants_table = Table(
            columns=columns,
            data=restaurants_data,
            sortable=True,
            filterable=True,
            component_id="restaurants_table"
        )
        
        return f"""
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title">Liste des Restaurants</h5>
                        <button class="btn btn-primary btn-sm float-end" onclick="refreshTable()">
                            🔄 Actualiser
                        </button>
                    </div>
                    <div class="card-body">
                        {restaurants_table.render()}
                    </div>
                </div>
            </div>
        </div>
        """
    
    def render_full_dashboard(self) -> str:
        """Rendu complet du dashboard."""
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard MAPAQ - Prédiction Risques Sanitaires</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                .stat-card {{ border-left: 4px solid #007bff; }}
                .trend-up {{ color: #28a745; }}
                .trend-down {{ color: #dc3545; }}
                .trend-neutral {{ color: #6c757d; }}
                .stat-icon {{ font-size: 2rem; opacity: 0.7; }}
                .interactive-table {{ max-height: 400px; overflow-y: auto; }}
                .chart-container {{ position: relative; height: 300px; }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <header class="py-3 mb-4 border-bottom">
                    <h1 class="h3">🏥 Dashboard MAPAQ - Prédiction Risques Sanitaires</h1>
                    <p class="text-muted">Surveillance et analyse prédictive des restaurants</p>
                </header>
                
                {self.create_overview_section()}
                {self.create_charts_section()}
                {self.create_restaurants_table()}
            </div>
            
            <script>
                // Fonctions JavaScript pour l'interactivité
                function filterTable(tableId, searchValue) {{
                    const table = document.getElementById(tableId);
                    const rows = table.getElementsByTagName('tr');
                    
                    for (let i = 1; i < rows.length; i++) {{
                        const row = rows[i];
                        const cells = row.getElementsByTagName('td');
                        let found = false;
                        
                        for (let j = 0; j < cells.length; j++) {{
                            if (cells[j].textContent.toLowerCase().includes(searchValue.toLowerCase())) {{
                                found = true;
                                break;
                            }}
                        }}
                        
                        row.style.display = found ? '' : 'none';
                    }}
                }}
                
                function refreshTable() {{
                    location.reload();
                }}
                
                // Auto-refresh toutes les 30 secondes
                setInterval(() => {{
                    console.log('Auto-refresh dashboard...');
                    // Ici on pourrait faire des appels AJAX pour mettre à jour les données
                }}, {self.config.auto_refresh_interval * 1000});
            </script>
        </body>
        </html>
        """

def main():
    """Point d'entrée principal pour les tests."""
    logger.info("=== FRONTEND DASHBOARD MAPAQ ===")
    logger.info("Heures 97-100: Interface utilisateur moderne")
    
    # Création du dashboard
    dashboard = MapaqDashboard()
    
    # Test des composants
    logger.info("Test des composants frontend...")
    
    # Test API client
    health = dashboard.api_client.get_health()
    logger.info(f"Santé API: {health.get('success', False)}")
    
    # Génération du HTML complet
    html_content = dashboard.render_full_dashboard()
    
    # Sauvegarde du fichier HTML
    output_file = "mapaq_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✅ Dashboard généré: {output_file}")
    logger.info("🌐 Ouvrez le fichier dans un navigateur pour voir le résultat")

if __name__ == "__main__":
    main()
