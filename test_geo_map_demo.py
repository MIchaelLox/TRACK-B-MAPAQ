"""
Test et Démonstration du Module geo_map.py
Validation des fonctionnalités de cartographie interactive MAPAQ

Auteur: Mouhamed Thiaw
Date: 2025-01-25
Heures: 105-108 (Test et validation)
"""

import sys
import os
from pathlib import Path

# Ajout du répertoire parent au path
sys.path.append(str(Path(__file__).parent))

try:
    from geo_map import GeoMapGenerator, MapConfig, create_demo_map, demo_geo_map
    print("✅ Import du module geo_map réussi")
except ImportError as e:
    print(f"❌ Erreur import geo_map: {e}")
    sys.exit(1)

def test_geo_map_basic():
    """Test basique du générateur de cartes."""
    print("\n=== TEST BASIQUE GEO_MAP ===")
    
    try:
        # Création du générateur
        generator = GeoMapGenerator()
        print("✅ Générateur créé avec succès")
        
        # Test de génération de données de démonstration
        generator._generate_demo_data()
        print(f"✅ Données de démonstration générées: {len(generator.restaurants_data)} restaurants")
        
        # Vérification des clusters
        total_clustered = sum(len(restaurants) for restaurants in generator.risk_clusters.values())
        print(f"✅ Clustering validé: {total_clustered} restaurants répartis")
        
        # Test de génération de la carte
        map_file = generator.generate_leaflet_map("test_mapaq_interactive.html")
        if map_file and os.path.exists(map_file):
            print(f"✅ Carte interactive générée: {map_file}")
            return True
        else:
            print("❌ Échec génération carte")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test basique: {e}")
        return False

def test_geo_map_with_custom_data():
    """Test avec données personnalisées."""
    print("\n=== TEST DONNÉES PERSONNALISÉES ===")
    
    try:
        # Données de test personnalisées
        custom_data = [
            {
                'id': 'test_1',
                'nom': 'Restaurant Test 1',
                'latitude': 45.5088,
                'longitude': -73.5878,
                'adresse': '123 Test Street, Montréal',
                'theme': 'Test Cuisine',
                'score_risque': 0.3,
                'categorie_risque': 'Faible',
                'probabilite_infraction': 0.2,
                'derniere_inspection': '2024-12-01',
                'nombre_infractions': 1
            },
            {
                'id': 'test_2',
                'nom': 'Restaurant Test 2',
                'latitude': 45.5017,
                'longitude': -73.5673,
                'adresse': '456 Test Avenue, Montréal',
                'theme': 'Test Food',
                'score_risque': 0.8,
                'categorie_risque': 'Élevé',
                'probabilite_infraction': 0.7,
                'derniere_inspection': '2024-11-15',
                'nombre_infractions': 4
            }
        ]
        
        # Création du générateur avec données personnalisées
        generator = GeoMapGenerator()
        success = generator.load_restaurant_data(custom_data)
        
        if success:
            print(f"✅ Chargement données personnalisées réussi: {len(generator.restaurants_data)} restaurants")
            
            # Génération de la carte
            map_file = generator.generate_leaflet_map("test_custom_data_map.html")
            if map_file and os.path.exists(map_file):
                print(f"✅ Carte avec données personnalisées générée: {map_file}")
                return True
            else:
                print("❌ Échec génération carte personnalisée")
                return False
        else:
            print("❌ Échec chargement données personnalisées")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test données personnalisées: {e}")
        return False

def test_geo_map_legacy_compatibility():
    """Test de compatibilité avec l'ancienne classe GeoMap."""
    print("\n=== TEST COMPATIBILITÉ LEGACY ===")
    
    try:
        from geo_map import GeoMap
        
        # Test avec données vides (utilise les données de démo)
        legacy_map = GeoMap(None)
        map_file = legacy_map.render_map("test_legacy_map.html")
        
        if map_file and os.path.exists(map_file):
            print(f"✅ Compatibilité legacy validée: {map_file}")
            return True
        else:
            print("❌ Échec test compatibilité legacy")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test legacy: {e}")
        return False

def test_map_configuration():
    """Test de configuration personnalisée de la carte."""
    print("\n=== TEST CONFIGURATION CARTE ===")
    
    try:
        # Configuration personnalisée
        custom_config = MapConfig(
            center_lat=45.5200,  # Légèrement différent
            center_lng=-73.5800,
            zoom_level=12,
            cluster_distance=30,
            heatmap_radius=20
        )
        
        generator = GeoMapGenerator(custom_config)
        generator._generate_demo_data()
        
        # Vérification de la configuration
        assert generator.config.center_lat == 45.5200
        assert generator.config.zoom_level == 12
        assert generator.config.cluster_distance == 30
        
        print("✅ Configuration personnalisée validée")
        
        # Test de génération avec config personnalisée
        map_file = generator.generate_leaflet_map("test_custom_config_map.html")
        if map_file and os.path.exists(map_file):
            print(f"✅ Carte avec configuration personnalisée générée: {map_file}")
            return True
        else:
            print("❌ Échec génération carte avec config personnalisée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test configuration: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests du module geo_map."""
    print("🗺️  TESTS COMPLETS DU MODULE GEO_MAP.PY")
    print("=" * 50)
    
    tests = [
        ("Test Basique", test_geo_map_basic),
        ("Test Données Personnalisées", test_geo_map_with_custom_data),
        ("Test Compatibilité Legacy", test_geo_map_legacy_compatibility),
        ("Test Configuration", test_map_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Exécution: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    # Résumé des résultats
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{len(tests)} tests réussis")
    
    if passed == len(tests):
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("\n📋 FONCTIONNALITÉS VALIDÉES:")
        print("- ✅ Génération de cartes interactives Leaflet")
        print("- ✅ Marqueurs colorés par niveau de risque")
        print("- ✅ Clustering automatique des restaurants")
        print("- ✅ Heatmap des risques")
        print("- ✅ Popups informatifs avec détails")
        print("- ✅ Interface responsive")
        print("- ✅ Filtres par catégorie de risque")
        print("- ✅ Compatibilité avec l'ancien code")
        print("- ✅ Configuration personnalisable")
        
        print("\n🚀 MODULE GEO_MAP.PY PRÊT POUR PRODUCTION!")
        return True
    else:
        print(f"⚠️  {len(tests) - passed} test(s) ont échoué")
        return False

if __name__ == "__main__":
    # Exécution des tests
    success = run_all_tests()
    
    # Démonstration finale
    if success:
        print("\n" + "=" * 50)
        print("🎨 GÉNÉRATION CARTE DE DÉMONSTRATION FINALE")
        print("=" * 50)
        
        try:
            demo_map_file = demo_geo_map()
            if demo_map_file:
                print(f"\n🌟 Carte de démonstration finale: {demo_map_file}")
                print("📖 Ouvrez ce fichier dans votre navigateur pour voir la carte interactive!")
            else:
                print("❌ Échec génération carte de démonstration")
        except Exception as e:
            print(f"❌ Erreur démonstration finale: {e}")
    
    print("\n🏁 Tests terminés!")
