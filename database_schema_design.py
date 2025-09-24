"""
Database Schema Design - MAPAQ Dashboard
Conception de la base de données pour le dashboard MAPAQ (Heures 89-92)

Ce module définit la conception complète de la base de données dashboard MAPAQ
avec schémas optimisés, indexation avancée, et gestion des performances.

Composants principaux:
- Schémas de tables optimisés
- Indexation et contraintes
- Procédures de maintenance
- Tests de performance
- Migration et archivage

Author: Mouhamed Thiaw
Date: 2025-01-14
Heures: 89-92 (Semaine 3)
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import os

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION BASE DE DONNÉES ==========

@dataclass
class DatabaseConfig:
    """Configuration de la base de données dashboard."""
    
    # Paramètres de base
    db_name: str = "mapaq_dashboard_v2.db"
    backup_dir: str = "backups"
    max_connections: int = 10
    
    # Paramètres de performance
    cache_size: int = 10000  # Pages en cache
    journal_mode: str = "WAL"  # Write-Ahead Logging
    synchronous: str = "NORMAL"
    temp_store: str = "MEMORY"
    
    # Paramètres d'archivage
    archive_days: int = 365  # Jours avant archivage
    cleanup_days: int = 30   # Jours avant suppression logs
    
    # Limites
    max_predictions_per_day: int = 10000
    max_restaurants: int = 50000

# ========== SCHÉMAS DE TABLES ==========

class DatabaseSchemaDesigner:
    """
    Concepteur de schémas de base de données pour le dashboard MAPAQ.
    
    Gère la création, l'optimisation et la maintenance des schémas.
    """
    
    def __init__(self, config: DatabaseConfig = None):
        """
        Initialise le concepteur de schémas.
        
        Args:
            config: Configuration de la base de données
        """
        self.config = config or DatabaseConfig()
        self.db_path = self.config.db_name
        self.connection = None
        
        # Schémas SQL
        self.table_schemas = self._define_table_schemas()
        self.indexes = self._define_indexes()
        self.triggers = self._define_triggers()
        self.views = self._define_views()
        
        logger.info(f"Concepteur de schémas initialisé: {self.db_path}")
    
    def _define_table_schemas(self) -> Dict[str, str]:
        """Définit les schémas de toutes les tables."""
        
        schemas = {}
        
        # Table principale des restaurants
        schemas['restaurants'] = """
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            theme TEXT NOT NULL,
            taille TEXT NOT NULL CHECK (taille IN ('Petite', 'Moyenne', 'Grande')),
            zone TEXT NOT NULL,
            adresse TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            telephone TEXT,
            email TEXT,
            site_web TEXT,
            date_ouverture DATE,
            statut TEXT DEFAULT 'Actif' CHECK (statut IN ('Actif', 'Fermé', 'Suspendu')),
            score_risque_actuel REAL DEFAULT 0.0,
            categorie_risque_actuelle TEXT DEFAULT 'Non évalué',
            derniere_inspection DATE,
            prochaine_inspection DATE,
            nombre_infractions_total INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Table des prédictions de risque
        schemas['predictions'] = """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id TEXT NOT NULL,
            score_risque REAL NOT NULL,
            categorie_risque TEXT NOT NULL,
            probabilite_infraction REAL NOT NULL,
            confiance REAL NOT NULL,
            modele_version TEXT NOT NULL DEFAULT '1.0.0',
            facteurs_risque TEXT, -- JSON des facteurs
            recommandations TEXT, -- JSON des recommandations
            contexte_prediction TEXT, -- JSON du contexte
            duree_calcul_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
        )
        """
        
        # Table de l'historique des inspections
        schemas['inspections'] = """
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id TEXT NOT NULL,
            date_inspection DATE NOT NULL,
            type_inspection TEXT NOT NULL CHECK (type_inspection IN ('Routine', 'Plainte', 'Suivi', 'Urgence')),
            inspecteur TEXT,
            score_obtenu REAL,
            nombre_infractions INTEGER DEFAULT 0,
            infractions_details TEXT, -- JSON des infractions
            mesures_correctives TEXT, -- JSON des mesures
            statut TEXT DEFAULT 'Complétée' CHECK (statut IN ('Programmée', 'En cours', 'Complétée', 'Annulée')),
            rapport_complet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
        )
        """
        
        # Table des infractions détaillées
        schemas['infractions'] = """
        CREATE TABLE IF NOT EXISTS infractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id INTEGER NOT NULL,
            restaurant_id TEXT NOT NULL,
            code_infraction TEXT NOT NULL,
            description TEXT NOT NULL,
            gravite TEXT NOT NULL CHECK (gravite IN ('Mineure', 'Majeure', 'Critique')),
            categorie TEXT NOT NULL,
            points_deduits REAL DEFAULT 0.0,
            mesure_corrective TEXT,
            delai_correction INTEGER, -- Jours
            statut_correction TEXT DEFAULT 'En attente' CHECK (statut_correction IN ('En attente', 'Corrigée', 'Non corrigée')),
            date_correction DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (inspection_id) REFERENCES inspections (id) ON DELETE CASCADE,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
        )
        """
        
        # Table des métriques système
        schemas['system_metrics'] = """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT,
            metric_category TEXT NOT NULL,
            metadata TEXT, -- JSON des métadonnées
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Table des logs d'audit
        schemas['audit_logs'] = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id TEXT NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
            old_values TEXT, -- JSON des anciennes valeurs
            new_values TEXT, -- JSON des nouvelles valeurs
            user_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Table de configuration
        schemas['configuration'] = """
        CREATE TABLE IF NOT EXISTS configuration (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'General',
            is_sensitive BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        return schemas
    
    def _define_indexes(self) -> List[str]:
        """Définit tous les index pour optimiser les performances."""
        
        indexes = [
            # Index sur restaurants
            "CREATE INDEX IF NOT EXISTS idx_restaurants_zone ON restaurants (zone)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_theme ON restaurants (theme)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_taille ON restaurants (taille)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_score ON restaurants (score_risque_actuel)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_categorie ON restaurants (categorie_risque_actuelle)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_prochaine_inspection ON restaurants (prochaine_inspection)",
            "CREATE INDEX IF NOT EXISTS idx_restaurants_statut ON restaurants (statut)",
            
            # Index sur prédictions
            "CREATE INDEX IF NOT EXISTS idx_predictions_restaurant ON predictions (restaurant_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_score ON predictions (score_risque)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_categorie ON predictions (categorie_risque)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_restaurant_date ON predictions (restaurant_id, created_at)",
            
            # Index sur inspections
            "CREATE INDEX IF NOT EXISTS idx_inspections_restaurant ON inspections (restaurant_id)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections (date_inspection)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_type ON inspections (type_inspection)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_statut ON inspections (statut)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_restaurant_date ON inspections (restaurant_id, date_inspection)",
            
            # Index sur infractions
            "CREATE INDEX IF NOT EXISTS idx_infractions_inspection ON infractions (inspection_id)",
            "CREATE INDEX IF NOT EXISTS idx_infractions_restaurant ON infractions (restaurant_id)",
            "CREATE INDEX IF NOT EXISTS idx_infractions_code ON infractions (code_infraction)",
            "CREATE INDEX IF NOT EXISTS idx_infractions_gravite ON infractions (gravite)",
            "CREATE INDEX IF NOT EXISTS idx_infractions_statut ON infractions (statut_correction)",
            
            # Index sur métriques
            "CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics (metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_category ON system_metrics (metric_category)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_date ON system_metrics (recorded_at)",
            
            # Index sur audit
            "CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_logs (table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_logs (record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs (action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_logs (created_at)",
            
            # Index composites pour requêtes complexes
            "CREATE INDEX IF NOT EXISTS idx_restaurants_zone_theme ON restaurants (zone, theme)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_score_date ON predictions (score_risque, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_inspections_restaurant_type_date ON inspections (restaurant_id, type_inspection, date_inspection)"
        ]
        
        return indexes
    
    def _define_triggers(self) -> List[str]:
        """Définit les triggers pour maintenir l'intégrité des données."""
        
        triggers = [
            # Trigger pour mettre à jour updated_at sur restaurants
            """
            CREATE TRIGGER IF NOT EXISTS update_restaurants_timestamp 
            AFTER UPDATE ON restaurants
            BEGIN
                UPDATE restaurants SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Trigger pour audit des modifications restaurants
            """
            CREATE TRIGGER IF NOT EXISTS audit_restaurants_update
            AFTER UPDATE ON restaurants
            BEGIN
                INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values)
                VALUES ('restaurants', NEW.id, 'UPDATE', 
                       json_object('nom', OLD.nom, 'score_risque_actuel', OLD.score_risque_actuel),
                       json_object('nom', NEW.nom, 'score_risque_actuel', NEW.score_risque_actuel));
            END
            """,
            
            # Trigger pour mettre à jour le score actuel du restaurant
            """
            CREATE TRIGGER IF NOT EXISTS update_restaurant_score
            AFTER INSERT ON predictions
            BEGIN
                UPDATE restaurants 
                SET score_risque_actuel = NEW.score_risque,
                    categorie_risque_actuelle = NEW.categorie_risque,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.restaurant_id;
            END
            """,
            
            # Trigger pour compter les infractions
            """
            CREATE TRIGGER IF NOT EXISTS count_infractions
            AFTER INSERT ON infractions
            BEGIN
                UPDATE restaurants 
                SET nombre_infractions_total = (
                    SELECT COUNT(*) FROM infractions WHERE restaurant_id = NEW.restaurant_id
                )
                WHERE id = NEW.restaurant_id;
            END
            """
        ]
        
        return triggers
    
    def _define_views(self) -> Dict[str, str]:
        """Définit les vues pour simplifier les requêtes complexes."""
        
        views = {}
        
        # Vue des restaurants avec leurs dernières prédictions
        views['restaurants_with_predictions'] = """
        CREATE VIEW IF NOT EXISTS restaurants_with_predictions AS
        SELECT 
            r.*,
            p.score_risque as derniere_prediction_score,
            p.probabilite_infraction as derniere_prediction_probabilite,
            p.confiance as derniere_prediction_confiance,
            p.created_at as derniere_prediction_date
        FROM restaurants r
        LEFT JOIN predictions p ON r.id = p.restaurant_id
        WHERE p.id = (
            SELECT MAX(id) FROM predictions WHERE restaurant_id = r.id
        ) OR p.id IS NULL
        """
        
        # Vue des statistiques par zone
        views['stats_by_zone'] = """
        CREATE VIEW IF NOT EXISTS stats_by_zone AS
        SELECT 
            zone,
            COUNT(*) as total_restaurants,
            AVG(score_risque_actuel) as score_moyen,
            COUNT(CASE WHEN categorie_risque_actuelle = 'Critique' THEN 1 END) as critique_count,
            COUNT(CASE WHEN categorie_risque_actuelle = 'Eleve' THEN 1 END) as eleve_count,
            COUNT(CASE WHEN categorie_risque_actuelle = 'Moyen' THEN 1 END) as moyen_count,
            COUNT(CASE WHEN categorie_risque_actuelle = 'Faible' THEN 1 END) as faible_count
        FROM restaurants
        WHERE statut = 'Actif'
        GROUP BY zone
        """
        
        # Vue des tendances mensuelles
        views['monthly_trends'] = """
        CREATE VIEW IF NOT EXISTS monthly_trends AS
        SELECT 
            strftime('%Y-%m', created_at) as mois,
            COUNT(*) as total_predictions,
            AVG(score_risque) as score_moyen,
            AVG(probabilite_infraction) as probabilite_moyenne,
            COUNT(CASE WHEN categorie_risque = 'Critique' THEN 1 END) as critique_count,
            COUNT(CASE WHEN categorie_risque = 'Eleve' THEN 1 END) as eleve_count
        FROM predictions
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY mois DESC
        """
        
        return views

    def create_database(self) -> bool:
        """
        Crée la base de données avec tous les schémas.
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Création du répertoire de sauvegarde
            os.makedirs(self.config.backup_dir, exist_ok=True)
            
            # Connexion à la base de données
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Configuration des performances
            self._configure_performance()
            
            # Création des tables
            logger.info("Création des tables...")
            for table_name, schema in self.table_schemas.items():
                self.connection.execute(schema)
                logger.info(f"Table créée: {table_name}")
            
            # Création des index
            logger.info("Création des index...")
            for index in self.indexes:
                self.connection.execute(index)
            
            # Création des triggers
            logger.info("Création des triggers...")
            for trigger in self.triggers:
                self.connection.execute(trigger)
            
            # Création des vues
            logger.info("Création des vues...")
            for view_name, view_sql in self.views.items():
                self.connection.execute(view_sql)
                logger.info(f"Vue créée: {view_name}")
            
            # Insertion des données de configuration par défaut
            self._insert_default_configuration()
            
            self.connection.commit()
            logger.info(f"Base de données créée avec succès: {self.db_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur création base de données: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _configure_performance(self):
        """Configure les paramètres de performance de SQLite."""
        performance_settings = [
            f"PRAGMA cache_size = {self.config.cache_size}",
            f"PRAGMA journal_mode = {self.config.journal_mode}",
            f"PRAGMA synchronous = {self.config.synchronous}",
            f"PRAGMA temp_store = {self.config.temp_store}",
            "PRAGMA optimize"
        ]
        
        for setting in performance_settings:
            self.connection.execute(setting)
        
        logger.info("Paramètres de performance configurés")
    
    def _insert_default_configuration(self):
        """Insère la configuration par défaut."""
        default_config = [
            ('dashboard_version', '1.0.0', 'Version du dashboard', 'System'),
            ('max_predictions_per_day', str(self.config.max_predictions_per_day), 'Limite prédictions par jour', 'Limits'),
            ('archive_days', str(self.config.archive_days), 'Jours avant archivage', 'Maintenance'),
            ('cleanup_days', str(self.config.cleanup_days), 'Jours avant nettoyage logs', 'Maintenance'),
            ('risk_threshold_high', '70.0', 'Seuil risque élevé', 'Risk'),
            ('risk_threshold_medium', '40.0', 'Seuil risque moyen', 'Risk'),
            ('inspection_frequency_days', '90', 'Fréquence inspections (jours)', 'Inspection')
        ]
        
        for key, value, description, category in default_config:
            self.connection.execute(
                "INSERT OR IGNORE INTO configuration (key, value, description, category) VALUES (?, ?, ?, ?)",
                (key, value, description, category)
            )
        
        logger.info("Configuration par défaut insérée")

def main():
    """Point d'entrée principal pour les tests."""
    logger.info("=== DATABASE SCHEMA DESIGN - MAPAQ ===")
    logger.info("Heures 89-92: Conception base de données dashboard")
    
    # Création du concepteur de schémas
    designer = DatabaseSchemaDesigner()
    
    # Création de la base de données
    success = designer.create_database()
    
    if success:
        logger.info("✅ Base de données créée avec succès!")
        
        # Affichage des statistiques
        if designer.connection:
            cursor = designer.connection.cursor()
            
            # Nombre de tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Nombre d'index
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]
            
            # Nombre de vues
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
            view_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Statistiques:")
            logger.info(f"   - Tables: {table_count}")
            logger.info(f"   - Index: {index_count}")
            logger.info(f"   - Vues: {view_count}")
            
            designer.connection.close()
    else:
        logger.error("❌ Échec de la création de la base de données")

if __name__ == "__main__":
    main()
