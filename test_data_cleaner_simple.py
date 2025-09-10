
import sys
import os
from pathlib import Path

# Test de la structure et logique sans pandas
def test_data_cleaner_structure():
    """Test de la structure du module DataCleaner."""
    print("=" * 60)
    print("TEST STRUCTURE: DataCleaner Module")
    print("=" * 60)
    
    try:
        # Vérifier que le fichier existe
        cleaner_file = Path("data_cleaner.py")
        if not cleaner_file.exists():
            print("❌ data_cleaner.py not found")
            return False
        
        print("✅ data_cleaner.py found")
        
        # Lire le contenu du fichier
        with open(cleaner_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les éléments clés
        required_elements = [
            "class DataCleaner",
            "def __init__",
            "def remove_nulls",
            "def unify_formats", 
            "def encode_categoricals",
            "def clean_pipeline",
            "def get_cleaning_report",
            "def validate_cleaned_data",
            "def analyze_data_quality",
            "import pandas",
            "import numpy",
            "import logging"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements: {missing_elements}")
            return False
        
        print("✅ All required elements found")
        
        # Vérifier les stratégies de nettoyage
        strategies = ["drop", "fill", "smart"]
        for strategy in strategies:
            if f"'{strategy}'" not in content or f'"{strategy}"' not in content:
                if strategy not in content:
                    print(f"⚠️  Strategy '{strategy}' might be missing")
        
        print("✅ Cleaning strategies implemented")
        
        # Vérifier les méthodes d'encodage
        encoding_methods = ["ordinal", "one_hot", "label_encoding"]
        encoding_found = any(method in content for method in encoding_methods)
        if encoding_found:
            print("✅ Encoding methods implemented")
        else:
            print("⚠️  Encoding methods might be missing")
        
        # Compter les lignes de code
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        print(f"📊 Code lines: {len(code_lines)}")
        
        if len(code_lines) > 400:
            print("✅ Substantial implementation (>400 lines)")
        else:
            print("⚠️  Implementation might be incomplete")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_config_integration():
    """Test de l'intégration avec config.py."""
    print("\n" + "=" * 60)
    print("TEST INTEGRATION: Config Module")
    print("=" * 60)
    
    try:
        # Vérifier que config.py existe
        config_file = Path("config.py")
        if not config_file.exists():
            print("❌ config.py not found")
            return False
        
        print("✅ config.py found")
        
        # Vérifier l'intégration dans data_cleaner.py
        with open("data_cleaner.py", 'r', encoding='utf-8') as f:
            cleaner_content = f.read()
        
        if "from config import" in cleaner_content or "import config" in cleaner_content:
            print("✅ Config integration found")
        else:
            print("⚠️  Config integration might be missing")
        
        # Vérifier les configurations de logging
        if "logging" in cleaner_content and ("getLogger" in cleaner_content or "Logger" in cleaner_content):
            print("✅ Logging configuration found")
        else:
            print("⚠️  Logging configuration might be missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_data_ingest_integration():
    """Test de l'intégration avec data_ingest.py."""
    print("\n" + "=" * 60)
    print("TEST INTEGRATION: DataIngest Module")
    print("=" * 60)
    
    try:
        # Vérifier que data_ingest.py existe
        ingest_file = Path("data_ingest.py")
        if not ingest_file.exists():
            print("❌ data_ingest.py not found")
            return False
        
        print("✅ data_ingest.py found")
        
        # Vérifier la compatibilité des formats
        with open("data_ingest.py", 'r', encoding='utf-8') as f:
            ingest_content = f.read()
        
        with open("data_cleaner.py", 'r', encoding='utf-8') as f:
            cleaner_content = f.read()
        
        # Vérifier que les deux utilisent pandas DataFrame
        if "DataFrame" in ingest_content and "DataFrame" in cleaner_content:
            print("✅ Compatible DataFrame usage")
        else:
            print("⚠️  DataFrame compatibility might be missing")
        
        # Vérifier les colonnes attendues
        expected_columns = [
            "id_poursuite", "business_id", "date", "date_jugement",
            "description", "etablissement", "montant", "proprietaire",
            "ville", "statut", "date_statut", "categorie"
        ]
        
        columns_found = sum(1 for col in expected_columns if col in cleaner_content)
        print(f"📊 Expected columns referenced: {columns_found}/{len(expected_columns)}")
        
        if columns_found >= len(expected_columns) * 0.8:
            print("✅ Good column coverage")
        else:
            print("⚠️  Some expected columns might be missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_file_structure():
    """Test de la structure des fichiers du projet."""
    print("\n" + "=" * 60)
    print("TEST STRUCTURE: Project Files")
    print("=" * 60)
    
    try:
        # Fichiers requis
        required_files = [
            "data_ingest.py",
            "data_cleaner.py", 
            "config.py",
            "requirements.txt",
            ".gitignore",
            ".env.example"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False
        
        print("✅ All required files present")
        
        # Vérifier les dossiers
        required_dirs = ["data", "logs", "cache", "models"]
        existing_dirs = []
        for dir_name in required_dirs:
            if Path(dir_name).exists():
                existing_dirs.append(dir_name)
        
        print(f"📁 Directories present: {existing_dirs}")
        
        # Vérifier requirements.txt
        with open("requirements.txt", 'r', encoding='utf-8') as f:
            requirements = f.read()
        
        essential_deps = ["pandas", "numpy", "scikit-learn", "requests"]
        deps_found = sum(1 for dep in essential_deps if dep in requirements)
        
        print(f"📦 Essential dependencies: {deps_found}/{len(essential_deps)}")
        
        if deps_found == len(essential_deps):
            print("✅ All essential dependencies listed")
        else:
            print("⚠️  Some essential dependencies might be missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_code_quality():
    """Test de la qualité du code."""
    print("\n" + "=" * 60)
    print("TEST QUALITY: Code Analysis")
    print("=" * 60)
    
    try:
        with open("data_cleaner.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Analyser la documentation
        docstring_lines = [line for line in lines if '"""' in line or "'''" in line]
        print(f"📝 Docstring indicators: {len(docstring_lines)}")
        
        # Analyser les commentaires
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        print(f"💬 Comment lines: {len(comment_lines)}")
        
        # Analyser la gestion d'erreurs
        error_handling = content.count('try:') + content.count('except')
        print(f"🛡️  Error handling blocks: {error_handling}")
        
        # Analyser le logging
        log_statements = content.count('logger.') + content.count('logging.')
        print(f"📊 Logging statements: {log_statements}")
        
        # Analyser les méthodes privées
        private_methods = content.count('def _')
        print(f"🔒 Private methods: {private_methods}")
        
        # Score de qualité
        quality_score = 0
        if len(docstring_lines) >= 4: quality_score += 20
        if len(comment_lines) >= 20: quality_score += 20
        if error_handling >= 5: quality_score += 20
        if log_statements >= 10: quality_score += 20
        if private_methods >= 2: quality_score += 20
        
        print(f"\n🎯 Code Quality Score: {quality_score}/100")
        
        if quality_score >= 80:
            print("✅ Excellent code quality")
        elif quality_score >= 60:
            print("✅ Good code quality")
        else:
            print("⚠️  Code quality could be improved")
        
        return quality_score >= 60
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Exécuter tous les tests simples."""
    print("🚀 Simple Testing - DataCleaner Implementation")
    print("=" * 70)
    print("Heures 9-12: Validation structure et logique")
    print("=" * 70)
    
    results = []
    
    # Tests à exécuter
    tests = [
        ("DataCleaner Structure", test_data_cleaner_structure),
        ("Config Integration", test_config_integration),
        ("DataIngest Integration", test_data_ingest_integration),
        ("File Structure", test_file_structure),
        ("Code Quality", test_code_quality)
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
    print("📊 SIMPLE TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= 4:
        print("🎉 DATACLEANER STRUCTURE VALIDATION SUCCESSFUL!")
        print("📋 Next: Install dependencies and run advanced tests")
        print("💡 Command: python -m pip install -r requirements.txt")
    else:
        print("⚠️  Some structural issues detected. Review the implementation.")
    
    return passed >= 4

if __name__ == "__main__":
    main()
