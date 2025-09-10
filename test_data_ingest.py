
from data_ingest import DataIngestor
import os

def test_csv_loading():
    """Test loading data from CSV file."""
    print("=" * 50)
    print("TEST 1: Loading data from CSV file")
    print("=" * 50)
    
    # Chemin vers notre fichier d'exemple
    csv_path = "sample_data.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: File {csv_path} not found")
        return False
    
    try:
        # Initialiser l'ingesteur
        ingestor = DataIngestor(csv_path)
        
        # Charger les données
        data = ingestor.load_raw_data()
        
        print(f"✅ Successfully loaded data!")
        print(f"📊 Shape: {data.shape}")
        print(f"📋 Columns: {list(data.columns)}")
        
        # Afficher les premières lignes
        print("\n📄 First 3 rows:")
        print(data.head(3))
        
        # Obtenir des informations détaillées
        print("\n📈 Data Info:")
        info = ingestor.get_data_info()
        for key, value in info.items():
            if key != "sample_data":  # Skip sample data for cleaner output
                print(f"  {key}: {value}")
        
        # Valider la structure
        print("\n🔍 Structure Validation:")
        validation = ingestor.validate_data_structure()
        for key, value in validation.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_url_loading():
    """Test loading data from URL (exemple avec une URL publique)."""
    print("\n" + "=" * 50)
    print("TEST 2: Loading data from URL")
    print("=" * 50)
    
    # URL d'exemple (données CSV publiques)
    test_url = "https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv"
    
    try:
        ingestor = DataIngestor(test_url)
        data = ingestor.load_raw_data()
        
        print(f"✅ Successfully loaded data from URL!")
        print(f"📊 Shape: {data.shape}")
        print(f"📋 Columns: {list(data.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading from URL: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for invalid sources."""
    print("\n" + "=" * 50)
    print("TEST 3: Error handling")
    print("=" * 50)
    
    # Test avec un fichier inexistant
    try:
        ingestor = DataIngestor("nonexistent_file.csv")
        data = ingestor.load_raw_data()
        print("❌ Should have failed for nonexistent file")
        return False
    except Exception as e:
        print(f"✅ Correctly handled nonexistent file: {str(e)}")
    
    # Test avec un format non supporté
    try:
        ingestor = DataIngestor("invalid_format.xyz")
        data = ingestor.load_raw_data()
        print("❌ Should have failed for invalid format")
        return False
    except Exception as e:
        print(f"✅ Correctly handled invalid format: {str(e)}")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Testing DataIngestor Implementation")
    print("=" * 60)
    
    results = []
    
    # Test 1: CSV Loading
    results.append(test_csv_loading())
    
    # Test 2: URL Loading (optionnel)
    results.append(test_url_loading())
    
    # Test 3: Error Handling
    results.append(test_error_handling())
    
    # Résumé des résultats
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! DataIngestor is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()
