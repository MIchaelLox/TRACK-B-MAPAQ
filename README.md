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

### Utilisation Rapide

```bash
# Démarrer le serveur Flask
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

---

## 🔄 Pipeline de Données ETL (Ajouté par Grace MANDIANGU)

### Pipeline Automatisé Complet

- Pipeline ETL pour traitement automatisé des données d'inspection MAPAQ.
  
  --> /data_pipeline.py
  
  **Étapes du Pipeline :**
  1. **Ingestion** - Chargement des données brutes (CSV, API, base de données)
  2. **Nettoyage** - Normalisation, suppression des doublons, gestion des valeurs manquantes
  3. **Enrichissement** - Géocodage, détection de thèmes, ajout de métadonnées
  4. **Modélisation** - Calcul des scores de risque et prédictions
  5. **Validation** - Contrôle qualité avec règles de validation
  6. **Sauvegarde** - Insertion/mise à jour dans la base de données SQLite
  
  **Fonctionnalités :**
  - Gestion d'erreurs avec retry automatique (3 tentatives)
  - Logging détaillé de chaque étape
  - Métriques d'exécution (durée, enregistrements traités)
  - Backup automatique de la base de données
  - Traitement par lots (batch processing)

### Scheduler d'Exécution Automatique

- Planificateur pour exécution périodique du pipeline.
  
  --> /pipeline_scheduler.py
  
  **Modes d'Exécution :**
  - **Quotidien** - Exécution à heure fixe (ex: 02:00)
  - **Horaire** - Exécution toutes les heures
  - **Intervalle** - Exécution à intervalle personnalisé (ex: 30 minutes)
  - **Immédiat** - Exécution unique sur demande
  
  **Utilisation :**
  ```bash
  python pipeline_scheduler.py
  # Puis choisir l'option souhaitée (1-4)
  ```

### Module de Validation des Données

- Validateur avec règles configurables pour contrôle qualité.
  
  --> /data_validator.py
  
  **Types de Validation :**
  - Champs obligatoires (nom, adresse, score)
  - Plages de valeurs (score: 0-100, probabilité: 0-1)
  - Énumérations (catégories de risque, tailles)
  - Formats de dates (YYYY-MM-DD)
  
  **Niveaux de Sévérité :**
  - **Erreur** - Bloque l'enregistrement
  - **Avertissement** - Signale mais accepte l'enregistrement
  
  **Rapport de Validation :**
  - Taux de validation
  - Résumé des erreurs par type
  - Liste des enregistrements invalides

### Interface CLI pour le Pipeline

- Script en ligne de commande pour lancer le pipeline facilement.
  
  --> /run_pipeline.py
  
  **Modes d'Utilisation :**
  
  ```bash
  # Mode interactif (avec questions)
  python run_pipeline.py
  
  # Mode CLI avec options
  python run_pipeline.py --source data/raw/inspections.csv --output mapaq.db
  
  # Avec génération de rapport
  python run_pipeline.py --report rapport_pipeline.json
  
  # Désactiver les backups
  python run_pipeline.py --no-backup
  ```
  
  **Options Disponibles :**
  - `--source` : Chemin du fichier source
  - `--output` : Chemin de la base de données
  - `--backup` / `--no-backup` : Activer/désactiver les backups
  - `--report` : Générer un rapport JSON
  - `--interactive` : Mode interactif

### Architecture du Pipeline

```
┌─────────────────┐
│  Données Brutes │ (CSV, API, DB)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Ingestion     │ → Chargement des données
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Nettoyage     │ → Normalisation, validation basique
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Enrichissement  │ → Géocodage, thèmes, métadonnées
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Modélisation   │ → Scores de risque, prédictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validation    │ → Contrôle qualité, règles métier
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Sauvegarde    │ → Base de données SQLite
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │ → Visualisation temps réel
└─────────────────┘
```

### Exécution Complète du Pipeline

**Étape 1 : Exécution Manuelle**
```bash
# Lancer le pipeline une fois
python run_pipeline.py

# Ou avec options spécifiques
python run_pipeline.py --source data/raw/mapaq_data.csv --report rapport.json
```

**Étape 2 : Automatisation avec Scheduler**
```bash
# Lancer le scheduler
python pipeline_scheduler.py

# Choisir l'option:
# 1 = Quotidien à 02:00
# 2 = Toutes les heures
# 3 = Toutes les 30 minutes
# 4 = Exécution immédiate
```

**Étape 3 : Visualisation**
```bash
# Démarrer le dashboard pour voir les résultats
python app_server.py

# Ouvrir http://127.0.0.1:5000
```

### Logs et Monitoring

Le pipeline génère automatiquement :
- **pipeline.log** - Logs détaillés de chaque exécution
- **data/backups/** - Backups de la base de données
- **Rapports JSON** - Métriques et statistiques d'exécution

### Gestion des Erreurs

Le pipeline inclut :
- ✅ Retry automatique (3 tentatives par étape)
- ✅ Rollback en cas d'erreur de sauvegarde
- ✅ Logs détaillés pour debugging
- ✅ Continuation partielle (traite ce qui est valide)
- ✅ Notifications d'erreurs critiques

### Configuration

Le pipeline utilise des valeurs par défaut mais peut être configuré :

```python
from data_pipeline import PipelineConfig

config = PipelineConfig(
    source_data_path="data/raw/inspections.csv",
    output_db_path="mapaq_dashboard.db",
    backup_enabled=True,
    max_retries=3,
    batch_size=100
)
```
