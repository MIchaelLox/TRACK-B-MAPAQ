# Track B – MAPAQ Predictive Health Model

Goal: Predict restaurant risk profiles based on public inspection datasets + derived variables.

Dataset Preparation

- Collect MAPAQ inspection data.
  
  --> /data_ingest.py

- Clean the dataset (remove nulls, unify column formats, encode categorical variables).
  
  --> /data_cleaner.py

Dictionaries

- Addresses Dictionary: Normalize addresses → enable geocoding for map display.
  
  --> /address_dict.py

- Themes Dictionary: Build keyword-based classification system (e.g., “Sushi,” “Trattoria,” “BBQ”) to infer cuisine type.
  
  --> /theme_dict.py

Probability Model

- Implement baseline model (logistic regression or Naïve Bayes).
  
  --> /model_baseline.py

- Calculate conditional probabilities for infractions given variables (theme, size, past history).
  
  --> /probability_engine.py

Rule Adaptation

- Add logic to adjust probabilities when regulations change (store effective dates in DB, apply time-based weights).
  
  --> /rule_adapter.py

Risk Profiling

- Generate risk score per restaurant.
  
  --> /risk_score.py

- Categorize into Low / Medium / High risk.
  
  --> /risk_categorizer.py

Visualization

- Build dashboard showing probabilities and trends.
  
  --> /dashboard.py (Flask/Django + frontend framework)

- Map restaurants (using geocoded addresses).
  
  --> /geo_map.py

---

## 🚀 Dashboard Interactif (Ajouté par Grace MANDIANGU)

### Serveur API REST

- Serveur Flask avec endpoints API complets pour le dashboard interactif.
  
  --> /app_server.py
  
  **Fonctionnalités :**
  - 8 endpoints API REST (dashboard, restaurants, charts, prédictions)
  - 15 restaurants de démonstration générés automatiquement
  - Support CORS intégré
  - Gestion d'erreurs robuste
  - Compatible avec ou sans base de données

### Interface Web Interactive

- Dashboard web moderne avec actualisation en temps réel.
  
  --> /mapaq_dashboard.html
  
  **Fonctionnalités :**
  - Statistiques en temps réel (4 cartes animées)
  - Graphiques interactifs (Chart.js) : distribution et tendances
  - Tableau dynamique avec recherche et tri
  - Actualisation automatique toutes les 30 secondes
  - Design responsive et moderne
  - Appels AJAX pour chargement des données

### Script de Démarrage

- Script batch pour lancer facilement le dashboard.
  
  --> /lancer_dashboard_interactif.bat

### Documentation

- Guide complet d'utilisation du dashboard interactif.
  
  --> /README_DASHBOARD_INTERACTIF.md
  
  **Contenu :**
  - Instructions d'installation
  - Documentation API complète
  - Guide de dépannage
  - Instructions de déploiement

### Utilisation Rapide

```bash
# Méthode 1 : Double-cliquer sur
lancer_dashboard_interactif.bat

# Méthode 2 : Ligne de commande
python app_server.py

# Puis ouvrir dans le navigateur
http://127.0.0.1:5000
```

### API Endpoints Disponibles

- `GET /api/v1/dashboard` - Statistiques globales
- `GET /api/v1/restaurants` - Liste des restaurants (avec filtres)
- `GET /api/v1/restaurant/{id}` - Détails d'un restaurant
- `GET /api/v1/charts/distribution` - Données graphique distribution
- `GET /api/v1/charts/trends` - Données graphique tendances
- `GET /api/v1/zones` - Liste des zones disponibles
- `POST /api/v1/predict` - Prédiction de risque
- `GET /api/health` - Health check du serveur
