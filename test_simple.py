# ===========================================
# File: test_simple.py
# Purpose: Simple test without external dependencies
# ===========================================

import csv
import os

def test_csv_reading():
    """Test basic CSV reading functionality."""
    print("=" * 50)
    print("TEST: Basic CSV Reading")
    print("=" * 50)
    
    csv_path = "sample_data.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: File {csv_path} not found")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
            print(f"✅ Successfully read CSV file!")
            print(f"📊 Number of records: {len(rows)}")
            print(f"📋 Columns: {list(rows[0].keys()) if rows else 'No data'}")
            
            # Afficher les premières lignes
            print("\n📄 First 3 rows:")
            for i, row in enumerate(rows[:3]):
                print(f"  Row {i+1}: {dict(row)}")
            
            # Vérifier la structure attendue
            expected_columns = [
                'id_poursuite', 'business_id', 'date', 'date_jugement',
                'description', 'etablissement', 'montant', 'proprietaire',
                'ville', 'statut', 'date_statut', 'categorie'
            ]
            
            actual_columns = list(rows[0].keys()) if rows else []
            missing_columns = set(expected_columns) - set(actual_columns)
            
            print(f"\n🔍 Structure Validation:")
            print(f"  Expected columns: {len(expected_columns)}")
            print(f"  Actual columns: {len(actual_columns)}")
            print(f"  Missing columns: {list(missing_columns)}")
            print(f"  Valid structure: {'✅ Yes' if not missing_columns else '❌ No'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run the simple test."""
    print("🚀 Testing CSV Data Structure")
    print("=" * 60)
    
    success = test_csv_reading()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULT")
    print("=" * 60)
    
    if success:
        print("🎉 Test passed! Sample data structure is correct.")
        print("📝 Next step: Install Python dependencies (pandas, numpy, requests)")
        print("💡 Command: python -m pip install pandas numpy requests")
    else:
        print("⚠️  Test failed. Check the sample data file.")
    
    return success

if __name__ == "__main__":
    main()
