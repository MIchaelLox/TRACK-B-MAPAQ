#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Géospatiales MAPAQ - Corrélations et Densité d'Infractions
Heures 5-8: Analytics géospatiales (corrélations géographiques, densité infractions par quartier)

Auteur: Mouhamed Thiaw
Date: 2025-09-30
Fonctionnalités:
- Analyse de densité d'infractions par zone géographique
- Corrélations spatiales entre restaurants et infractions
- Clustering géographique des risques
- Heatmaps de densité par quartier
- Analyse des patterns géographiques
"""

import json
import logging
import sqlite3
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import os
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ZoneGeographique:
    """Structure pour une zone géographique d'analyse."""
    id: str
    nom: str
    centre_lat: float
    centre_lng: float
    rayon_km: float
    restaurants: List[Dict[str, Any]]
    nb_infractions: int
    densite_infractions: float
    score_risque_moyen: float
    categories_risque: Dict[str, int]

@dataclass
class CorrelationSpatiale:
    """Structure pour les corrélations spatiales."""
    zone_a: str
    zone_b: str
    distance_km: float
    correlation_infractions: float
    correlation_risque: float
    restaurants_communs: int
    tendance: str  # "positive", "negative", "neutre"

class AnalyticsGeospatiales:
    """Analyseur géospatial pour les données MAPAQ."""
    
    def __init__(self, db_path: str = "mapaq_dashboard.db"):
        """Initialise l'analyseur géospatial."""
        self.db_path = db_path
        self.zones_geographiques = []
        self.correlations_spatiales = []
        self.quartiers_montreal = self._definir_quartiers_montreal()
        
        logger.info("Analyseur géospatial MAPAQ initialisé")
    
    def _definir_quartiers_montreal(self) -> List[Dict[str, Any]]:
        """Définit les principaux quartiers de Montréal pour l'analyse."""
        return [
            {
                "id": "plateau",
                "nom": "Plateau-Mont-Royal",
                "centre_lat": 45.5200,
                "centre_lng": -73.5800,
                "rayon_km": 2.0
            },
            {
                "id": "centre_ville",
                "nom": "Centre-Ville",
                "centre_lat": 45.5017,
                "centre_lng": -73.5673,
                "rayon_km": 1.5
            },
            {
                "id": "vieux_montreal",
                "nom": "Vieux-Montréal",
                "centre_lat": 45.5088,
                "centre_lng": -73.5540,
                "rayon_km": 1.0
            },
            {
                "id": "mile_end",
                "nom": "Mile End",
                "centre_lat": 45.5230,
                "centre_lng": -73.6000,
                "rayon_km": 1.2
            },
            {
                "id": "verdun",
                "nom": "Verdun",
                "centre_lat": 45.4580,
                "centre_lng": -73.5680,
                "rayon_km": 2.5
            },
            {
                "id": "outremont",
                "nom": "Outremont",
                "centre_lat": 45.5180,
                "centre_lng": -73.6100,
                "rayon_km": 1.8
            },
            {
                "id": "rosemont",
                "nom": "Rosemont-La Petite-Patrie",
                "centre_lat": 45.5400,
                "centre_lng": -73.5800,
                "rayon_km": 2.2
            },
            {
                "id": "hochelaga",
                "nom": "Hochelaga-Maisonneuve",
                "centre_lat": 45.5300,
                "centre_lng": -73.5400,
                "rayon_km": 2.0
            }
        ]
    
    def charger_donnees_restaurants(self) -> List[Dict[str, Any]]:
        """Charge les données des restaurants depuis la base de données."""
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Base de données non trouvée: {self.db_path}")
                return self._generer_donnees_demo()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            query = """
            SELECT id, nom, adresse, latitude, longitude, theme, 
                   score_risque, categorie_risque, probabilite_infraction,
                   derniere_inspection, nombre_infractions
            FROM restaurants 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
            
            cursor = conn.execute(query)
            restaurants = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"Chargé {len(restaurants)} restaurants avec coordonnées")
            return restaurants
            
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            return self._generer_donnees_demo()
    
    def _generer_donnees_demo(self) -> List[Dict[str, Any]]:
        """Génère des données de démonstration pour l'analyse."""
        import random
        
        restaurants_demo = []
        themes = ["Italien", "Asiatique", "Français", "Fast Food", "Mexicain", "Grec", "Libanais"]
        
        # Génération de restaurants dans différents quartiers
        for i, quartier in enumerate(self.quartiers_montreal):
            nb_restaurants = random.randint(8, 15)
            
            for j in range(nb_restaurants):
                # Position aléatoire dans le rayon du quartier
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, quartier["rayon_km"])
                
                lat_offset = (distance * math.cos(angle)) / 111.0  # ~111 km par degré
                lng_offset = (distance * math.sin(angle)) / (111.0 * math.cos(math.radians(quartier["centre_lat"])))
                
                lat = quartier["centre_lat"] + lat_offset
                lng = quartier["centre_lng"] + lng_offset
                
                # Score de risque influencé par le quartier
                base_risk = {
                    "centre_ville": 0.6, "plateau": 0.4, "vieux_montreal": 0.3,
                    "mile_end": 0.45, "verdun": 0.55, "outremont": 0.35,
                    "rosemont": 0.5, "hochelaga": 0.65
                }.get(quartier["id"], 0.5)
                
                score_risque = max(0.1, min(0.95, base_risk + random.uniform(-0.2, 0.2)))
                
                # Catégorisation du risque
                if score_risque >= 0.8:
                    categorie = "Critique"
                elif score_risque >= 0.6:
                    categorie = "Élevé"
                elif score_risque >= 0.3:
                    categorie = "Modéré"
                else:
                    categorie = "Faible"
                
                # Nombre d'infractions basé sur le score
                nb_infractions = max(0, int(score_risque * 10 + random.uniform(-2, 3)))
                
                restaurant = {
                    "id": f"demo_{quartier['id']}_{j+1}",
                    "nom": f"Restaurant {quartier['nom']} {j+1}",
                    "adresse": f"{random.randint(100, 999)} Rue {quartier['nom']}, Montréal",
                    "latitude": lat,
                    "longitude": lng,
                    "theme": random.choice(themes),
                    "score_risque": round(score_risque, 3),
                    "categorie_risque": categorie,
                    "probabilite_infraction": round(score_risque * 0.8, 3),
                    "derniere_inspection": "2024-12-01",
                    "nombre_infractions": nb_infractions,
                    "quartier": quartier["nom"]
                }
                
                restaurants_demo.append(restaurant)
        
        logger.info(f"Généré {len(restaurants_demo)} restaurants de démonstration")
        return restaurants_demo
    
    def calculer_distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcule la distance en kilomètres entre deux points GPS."""
        # Formule de Haversine
        R = 6371  # Rayon de la Terre en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def analyser_densite_par_quartier(self, restaurants: List[Dict[str, Any]]) -> List[ZoneGeographique]:
        """Analyse la densité d'infractions par quartier."""
        zones_analysees = []
        
        for quartier in self.quartiers_montreal:
            # Filtrer les restaurants dans ce quartier
            restaurants_quartier = []
            
            for restaurant in restaurants:
                distance = self.calculer_distance_km(
                    quartier["centre_lat"], quartier["centre_lng"],
                    restaurant["latitude"], restaurant["longitude"]
                )
                
                if distance <= quartier["rayon_km"]:
                    restaurants_quartier.append(restaurant)
            
            if not restaurants_quartier:
                continue
            
            # Calculs statistiques
            nb_infractions = sum(r["nombre_infractions"] for r in restaurants_quartier)
            score_risque_moyen = sum(r["score_risque"] for r in restaurants_quartier) / len(restaurants_quartier)
            
            # Densité d'infractions par km²
            superficie_km2 = math.pi * (quartier["rayon_km"] ** 2)
            densite_infractions = nb_infractions / superficie_km2
            
            # Répartition par catégorie de risque
            categories_risque = Counter(r["categorie_risque"] for r in restaurants_quartier)
            
            zone = ZoneGeographique(
                id=quartier["id"],
                nom=quartier["nom"],
                centre_lat=quartier["centre_lat"],
                centre_lng=quartier["centre_lng"],
                rayon_km=quartier["rayon_km"],
                restaurants=restaurants_quartier,
                nb_infractions=nb_infractions,
                densite_infractions=round(densite_infractions, 2),
                score_risque_moyen=round(score_risque_moyen, 3),
                categories_risque=dict(categories_risque)
            )
            
            zones_analysees.append(zone)
        
        # Tri par densité décroissante
        zones_analysees.sort(key=lambda z: z.densite_infractions, reverse=True)
        
        logger.info(f"Analysé {len(zones_analysees)} zones géographiques")
        return zones_analysees
    
    def calculer_correlations_spatiales(self, zones: List[ZoneGeographique]) -> List[CorrelationSpatiale]:
        """Calcule les corrélations spatiales entre zones."""
        correlations = []
        
        for i, zone_a in enumerate(zones):
            for j, zone_b in enumerate(zones[i+1:], i+1):
                # Distance entre centres des zones
                distance = self.calculer_distance_km(
                    zone_a.centre_lat, zone_a.centre_lng,
                    zone_b.centre_lat, zone_b.centre_lng
                )
                
                # Corrélation des infractions (simplifiée)
                if zone_a.nb_infractions > 0 and zone_b.nb_infractions > 0:
                    correlation_infractions = min(zone_a.nb_infractions, zone_b.nb_infractions) / max(zone_a.nb_infractions, zone_b.nb_infractions)
                else:
                    correlation_infractions = 0.0
                
                # Corrélation des scores de risque
                diff_risque = abs(zone_a.score_risque_moyen - zone_b.score_risque_moyen)
                correlation_risque = max(0, 1 - diff_risque)
                
                # Restaurants communs (dans un rayon étendu)
                restaurants_communs = 0
                for rest_a in zone_a.restaurants:
                    for rest_b in zone_b.restaurants:
                        if rest_a["theme"] == rest_b["theme"]:
                            restaurants_communs += 1
                
                # Détermination de la tendance
                if correlation_infractions > 0.7 and correlation_risque > 0.7:
                    tendance = "positive"
                elif correlation_infractions < 0.3 or correlation_risque < 0.3:
                    tendance = "negative"
                else:
                    tendance = "neutre"
                
                correlation = CorrelationSpatiale(
                    zone_a=zone_a.nom,
                    zone_b=zone_b.nom,
                    distance_km=round(distance, 2),
                    correlation_infractions=round(correlation_infractions, 3),
                    correlation_risque=round(correlation_risque, 3),
                    restaurants_communs=restaurants_communs,
                    tendance=tendance
                )
                
                correlations.append(correlation)
        
        # Tri par corrélation décroissante
        correlations.sort(key=lambda c: (c.correlation_infractions + c.correlation_risque) / 2, reverse=True)
        
        logger.info(f"Calculé {len(correlations)} corrélations spatiales")
        return correlations
    
    def generer_heatmap_data(self, zones: List[ZoneGeographique]) -> Dict[str, Any]:
        """Génère les données pour une heatmap de densité."""
        heatmap_data = {
            "zones": [],
            "max_densite": 0,
            "min_densite": float('inf'),
            "moyenne_densite": 0
        }
        
        densites = []
        
        for zone in zones:
            zone_data = {
                "id": zone.id,
                "nom": zone.nom,
                "centre": [zone.centre_lat, zone.centre_lng],
                "rayon_km": zone.rayon_km,
                "densite": zone.densite_infractions,
                "nb_restaurants": len(zone.restaurants),
                "nb_infractions": zone.nb_infractions,
                "score_risque_moyen": zone.score_risque_moyen,
                "couleur_intensite": min(1.0, zone.densite_infractions / 20.0)  # Normalisation
            }
            
            heatmap_data["zones"].append(zone_data)
            densites.append(zone.densite_infractions)
        
        if densites:
            heatmap_data["max_densite"] = max(densites)
            heatmap_data["min_densite"] = min(densites)
            heatmap_data["moyenne_densite"] = round(sum(densites) / len(densites), 2)
        
        return heatmap_data
    
    def generer_rapport_analytics(self, zones: List[ZoneGeographique], 
                                 correlations: List[CorrelationSpatiale]) -> Dict[str, Any]:
        """Génère un rapport complet d'analytics géospatiales."""
        
        # Statistiques globales
        total_restaurants = sum(len(z.restaurants) for z in zones)
        total_infractions = sum(z.nb_infractions for z in zones)
        
        # Top zones à risque
        zones_risque_eleve = [z for z in zones if z.score_risque_moyen >= 0.6]
        zones_densite_elevee = [z for z in zones if z.densite_infractions >= 10.0]
        
        # Corrélations significatives
        correlations_fortes = [c for c in correlations if 
                              (c.correlation_infractions + c.correlation_risque) / 2 >= 0.7]
        
        # Analyse par thème
        themes_par_zone = defaultdict(lambda: defaultdict(int))
        for zone in zones:
            for restaurant in zone.restaurants:
                themes_par_zone[zone.nom][restaurant["theme"]] += 1
        
        rapport = {
            "timestamp": datetime.now().isoformat(),
            "resume_executif": {
                "total_zones_analysees": len(zones),
                "total_restaurants": total_restaurants,
                "total_infractions": total_infractions,
                "densite_moyenne_infractions": round(total_infractions / len(zones), 2) if zones else 0,
                "zones_risque_eleve": len(zones_risque_eleve),
                "zones_densite_elevee": len(zones_densite_elevee)
            },
            "top_zones_risque": [
                {
                    "nom": z.nom,
                    "score_risque_moyen": z.score_risque_moyen,
                    "densite_infractions": z.densite_infractions,
                    "nb_restaurants": len(z.restaurants),
                    "nb_infractions": z.nb_infractions
                }
                for z in zones[:5]
            ],
            "correlations_spatiales_fortes": [
                {
                    "zones": f"{c.zone_a} ↔ {c.zone_b}",
                    "distance_km": c.distance_km,
                    "correlation_moyenne": round((c.correlation_infractions + c.correlation_risque) / 2, 3),
                    "tendance": c.tendance
                }
                for c in correlations_fortes[:10]
            ],
            "analyse_thematique": dict(themes_par_zone),
            "recommandations": self._generer_recommandations(zones, correlations),
            "donnees_detaillees": {
                "zones": [asdict(z) for z in zones],
                "correlations": [asdict(c) for c in correlations]
            }
        }
        
        return rapport
    
    def _generer_recommandations(self, zones: List[ZoneGeographique], 
                                correlations: List[CorrelationSpatiale]) -> List[str]:
        """Génère des recommandations basées sur l'analyse."""
        recommandations = []
        
        # Zones à surveiller
        zones_critiques = [z for z in zones if z.score_risque_moyen >= 0.7]
        if zones_critiques:
            recommandations.append(
                f"Surveillance renforcée recommandée pour {len(zones_critiques)} zones: " +
                ", ".join(z.nom for z in zones_critiques[:3])
            )
        
        # Densité élevée
        zones_denses = [z for z in zones if z.densite_infractions >= 15.0]
        if zones_denses:
            recommandations.append(
                f"Inspections préventives dans les zones à forte densité: " +
                ", ".join(z.nom for z in zones_denses[:3])
            )
        
        # Corrélations spatiales
        correlations_fortes = [c for c in correlations if c.correlation_infractions >= 0.8]
        if correlations_fortes:
            recommandations.append(
                "Coordination des inspections entre zones corrélées pour optimiser l'efficacité"
            )
        
        # Thèmes à risque
        themes_risque = defaultdict(list)
        for zone in zones:
            for restaurant in zone.restaurants:
                if restaurant["score_risque"] >= 0.7:
                    themes_risque[restaurant["theme"]].append(zone.nom)
        
        if themes_risque:
            theme_critique = max(themes_risque.keys(), key=lambda t: len(themes_risque[t]))
            recommandations.append(
                f"Attention particulière aux restaurants de type '{theme_critique}' " +
                f"(présents dans {len(themes_risque[theme_critique])} zones à risque)"
            )
        
        # Recommandations générales
        recommandations.extend([
            "Implémenter un système d'alerte géographique pour les nouvelles infractions",
            "Développer des profils de risque spécifiques par quartier",
            "Optimiser les tournées d'inspection basées sur la proximité géographique",
            "Analyser l'impact des facteurs démographiques sur les patterns de risque"
        ])
        
        return recommandations
    
    def sauvegarder_rapport(self, rapport: Dict[str, Any], 
                           fichier: str = "rapport_analytics_geospatiales.json") -> str:
        """Sauvegarde le rapport d'analytics."""
        try:
            with open(fichier, 'w', encoding='utf-8') as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Rapport sauvegardé: {fichier}")
            return fichier
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport: {e}")
            return ""
    
    def executer_analyse_complete(self) -> Dict[str, Any]:
        """Exécute l'analyse géospatiale complète."""
        logger.info("=== ANALYTICS GÉOSPATIALES MAPAQ ===")
        logger.info("Heures 5-8: Corrélations géographiques et densité infractions")
        
        try:
            # 1. Chargement des données
            restaurants = self.charger_donnees_restaurants()
            
            # 2. Analyse par quartier
            zones = self.analyser_densite_par_quartier(restaurants)
            self.zones_geographiques = zones
            
            # 3. Corrélations spatiales
            correlations = self.calculer_correlations_spatiales(zones)
            self.correlations_spatiales = correlations
            
            # 4. Génération heatmap
            heatmap_data = self.generer_heatmap_data(zones)
            
            # 5. Rapport complet
            rapport = self.generer_rapport_analytics(zones, correlations)
            rapport["heatmap_data"] = heatmap_data
            
            # 6. Sauvegarde
            fichier_rapport = self.sauvegarder_rapport(rapport)
            
            # 7. Résumé des résultats
            logger.info("=== RÉSULTATS ANALYTICS GÉOSPATIALES ===")
            logger.info(f"✅ Zones analysées: {len(zones)}")
            logger.info(f"✅ Restaurants analysés: {sum(len(z.restaurants) for z in zones)}")
            logger.info(f"✅ Corrélations calculées: {len(correlations)}")
            logger.info(f"✅ Rapport généré: {fichier_rapport}")
            
            # Top 3 zones à risque
            if zones:
                logger.info("🔥 Top 3 zones à risque:")
                for i, zone in enumerate(zones[:3], 1):
                    logger.info(f"   {i}. {zone.nom}: {zone.score_risque_moyen:.3f} (densité: {zone.densite_infractions}/km²)")
            
            return rapport
            
        except Exception as e:
            logger.error(f"Erreur analyse géospatiale: {e}")
            return {"erreur": str(e)}

def main():
    """Fonction principale pour tester l'analytics géospatiales."""
    try:
        # Initialisation de l'analyseur
        analyseur = AnalyticsGeospatiales()
        
        # Exécution de l'analyse complète
        rapport = analyseur.executer_analyse_complete()
        
        if "erreur" not in rapport:
            print("\n" + "="*60)
            print("📊 ANALYTICS GÉOSPATIALES MAPAQ - RÉSULTATS")
            print("="*60)
            
            resume = rapport["resume_executif"]
            print(f"🏙️  Zones analysées: {resume['total_zones_analysees']}")
            print(f"🍽️  Restaurants: {resume['total_restaurants']}")
            print(f"⚠️  Infractions totales: {resume['total_infractions']}")
            print(f"📈 Densité moyenne: {resume['densite_moyenne_infractions']}/km²")
            
            print(f"\n🔥 TOP ZONES À RISQUE:")
            for zone in rapport["top_zones_risque"][:3]:
                print(f"   • {zone['nom']}: Score {zone['score_risque_moyen']:.3f}")
            
            print(f"\n🔗 CORRÉLATIONS SPATIALES FORTES:")
            for corr in rapport["correlations_spatiales_fortes"][:3]:
                print(f"   • {corr['zones']}: {corr['correlation_moyenne']:.3f}")
            
            print(f"\n💡 RECOMMANDATIONS CLÉS:")
            for i, rec in enumerate(rapport["recommandations"][:3], 1):
                print(f"   {i}. {rec}")
            
            print(f"\n✅ Analyse terminée avec succès!")
            print(f"📄 Rapport détaillé: rapport_analytics_geospatiales.json")
            
        return True
        
    except Exception as e:
        logger.error(f"Erreur dans main(): {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
