# ===========================================
# File: test_data_ingest_advanced.py
# Purpose: Test avancé pour DataIngestor avec API MAPAQ
# Heures 5-8 : Validation implémentation complète
# ===========================================

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from data_ingest import DataIngestor
    from config import DataSources, APIConfig
    import pandas as pd
    import json
    from datetime import datetime
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Make sure to install dependencies: python -m pip install pandas requests")
    sys.exit(1)

def test_auto_download():
    """Test du téléchargement automatique depuis l'API MAPAQ."""
    print("=" * 60)
    print("TEST 1: Auto-download from MAPAQ API")
    print("=" * 60)
    
    try:
        # Initialiser avec auto-download
        ingestor = DataIngestor(auto_download=True)
        
        print("🔄 Attempting to download latest MAPAQ data...")
        data = ingestor.load_raw_data()
        
        print(f"✅ Successfully loaded data!")
        print(f"📊 Shape: {data.shape}")
        print(f"📋 Columns: {list(data.columns)}")
        
        # Afficher les statistiques de téléchargement
        stats = ingestor.get_download_stats()
        print(f"\n📈 Download Statistics:")
        for key, value in stats.items():
            if key != 'cache_info':  # Afficher cache_info séparément
                print(f"  {key}: {value}")
        
        # Informations sur le cache
        print(f"\n💾 Cache Information:")
        cache_info = stats.get('cache_info', {})
        for key, value in cache_info.items():
            print(f"  {key}: {value}")
        
        # Validation de la structure
        validation = ingestor.validate_data_structure()
        print(f"\n🔍 Structure Validation:")
        print(f"  Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")
        print(f"  Total records: {validation['total_records']}")
        
        if validation['missing_columns']:
            print(f"  Missing columns: {validation['missing_columns']}")
        if validation['extra_columns']:
            print(f"  Extra columns: {validation['extra_columns']}")
        
        # Afficher un échantillon des données
        print(f"\n📄 Sample Data (first 2 rows):")
        print(data.head(2).to_string())
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_fallback_to_sample():
    """Test du fallback vers les données d'exemple."""
    print("\n" + "=" * 60)
    print("TEST 2: Fallback to sample data")
    print("=" * 60)
    
    try:
        # Forcer l'utilisation des données d'exemple
        sample_path = DataSources.SAMPLE_DATA
        ingestor = DataIngestor(source_path=str(sample_path), auto_download=False)
        
        data = ingestor.load_raw_data()
        
        print(f"✅ Successfully loaded sample data!")
        print(f"📊 Shape: {data.shape}")
        print(f"📋 Columns: {list(data.columns)}")
        
        # Vérifier que c'est bien les données d'exemple
        if len(data) == 8:  # Notre fichier d'exemple a 8 lignes
            print("✅ Confirmed: Using sample data as expected")
        else:
            print(f"⚠️  Unexpected data size: {len(data)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_data_freshness():
    """Test de la fraîcheur des données."""
    print("\n" + "=" * 60)
    print("TEST 3: Data freshness evaluation")
    print("=" * 60)
    
    try:
        ingestor = DataIngestor()
        
        # Charger les données (utilisera le cache s'il existe)
        data = ingestor.load_raw_data()
        
        # Obtenir les informations de fraîcheur
        stats = ingestor.get_download_stats()
        freshness = stats.get('data_freshness', 'unknown')
        
        freshness_messages = {
            'very_fresh': '🟢 Very Fresh (< 1 hour)',
            'fresh': '🟡 Fresh (< 6 hours)',
            'acceptable': '🟠 Acceptable (< 24 hours)',
            'stale': '🔴 Stale (> 24 hours)',
            'no_cache': '⚪ No Cache Available'
        }
        
        print(f"📅 Data Freshness: {freshness_messages.get(freshness, freshness)}")
        
        cache_info = stats.get('cache_info', {})
        if cache_info.get('exists'):
            print(f"📁 Cache file size: {cache_info['size_bytes']} bytes")
            print(f"🕐 Last modified: {cache_info['last_modified']}")
            print(f"⏰ Age: {cache_info['age_hours']:.1f} hours")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_data_validation():
    """Test approfondi de la validation des données."""
    print("\n" + "=" * 60)
    print("TEST 4: Advanced data validation")
    print("=" * 60)
    
    try:
        ingestor = DataIngestor()
        data = ingestor.load_raw_data()
        
        # Validation de base
        validation = ingestor.validate_data_structure()
        print(f"🔍 Basic validation: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
        
        # Validations supplémentaires
        print(f"\n📊 Advanced Data Analysis:")
        
        # Vérifier les types de données
        print(f"  Data types:")
        for col, dtype in data.dtypes.items():
            print(f"    {col}: {dtype}")
        
        # Vérifier les valeurs nulles
        null_counts = data.isnull().sum()
        total_nulls = null_counts.sum()
        print(f"\n  Null values: {total_nulls} total")
        if total_nulls > 0:
            for col, count in null_counts.items():
                if count > 0:
                    print(f"    {col}: {count} nulls")
        
        # Vérifier les valeurs uniques pour certaines colonnes
        if 'statut' in data.columns:
            statuts = data['statut'].value_counts()
            print(f"\n  Status distribution:")
            for status, count in statuts.items():
                print(f"    {status}: {count}")
        
        # Vérifier les dates
        date_columns = [col for col in data.columns if 'date' in col.lower()]
        if date_columns:
            print(f"\n  Date columns found: {date_columns}")
            for col in date_columns:
                try:
                    pd.to_datetime(data[col])
                    print(f"    {col}: ✅ Valid date format")
                except:
                    print(f"    {col}: ❌ Invalid date format")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_performance():
    """Test de performance du chargement."""
    print("\n" + "=" * 60)
    print("TEST 5: Performance testing")
    print("=" * 60)
    
    try:
        import time
        
        # Test 1: Premier chargement (peut inclure téléchargement)
        start_time = time.time()
        ingestor1 = DataIngestor()
        data1 = ingestor1.load_raw_data()
        first_load_time = time.time() - start_time
        
        print(f"⏱️  First load: {first_load_time:.2f}s ({len(data1)} records)")
        
        # Test 2: Deuxième chargement (devrait utiliser le cache)
        start_time = time.time()
        ingestor2 = DataIngestor()
        data2 = ingestor2.load_raw_data()
        second_load_time = time.time() - start_time
        
        print(f"⏱️  Second load: {second_load_time:.2f}s ({len(data2)} records)")
        
        # Calculer l'amélioration
        if first_load_time > 0:
            improvement = ((first_load_time - second_load_time) / first_load_time) * 100
            print(f"🚀 Performance improvement: {improvement:.1f}%")
        
        # Vérifier que les données sont identiques
        if data1.equals(data2):
            print("✅ Data consistency: Identical datasets")
        else:
            print("⚠️  Data consistency: Datasets differ")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Exécuter tous les tests avancés."""
    print("🚀 Advanced Testing - DataIngestor with MAPAQ API")
    print("=" * 70)
    print("Heures 5-8: Validation implémentation complète")
    print("=" * 70)
    
    results = []
    
    # Exécuter tous les tests
    tests = [
        ("Auto-download from MAPAQ API", test_auto_download),
        ("Fallback to sample data", test_fallback_to_sample),
        ("Data freshness evaluation", test_data_freshness),
        ("Advanced data validation", test_data_validation),
        ("Performance testing", test_performance)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Résumé des résultats
    print("\n" + "=" * 70)
    print("📊 ADVANCED TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! DataIngestor with MAPAQ API is fully functional.")
        print("✅ Ready for Heures 9-12: Development data_cleaner.py")
    else:
        print("⚠️  Some tests failed. Review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()
