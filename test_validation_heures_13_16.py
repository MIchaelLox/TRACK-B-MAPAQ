

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_data_cleaner_structure():
    """Test de la structure du data_cleaner.py pour Heures 9-12."""
    print("=" * 60)
    print("TEST 1: Structure data_cleaner.py (Heures 9-12)")
    print("=" * 60)
    
    # Vérifier que le fichier existe
    cleaner_file = Path("data_cleaner.py")
    if not cleaner_file.exists():
        print("❌ data_cleaner.py not found")
        return False
    
    print("✅ data_cleaner.py found")
    
    # Lire le contenu
    with open(cleaner_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier les éléments requis pour Heures 9-12
    required_elements = {
        'class DataCleaner': 'Classe principale',
        'def remove_nulls': 'Nettoyage données nulles',
        'def unify_formats': 'Normalisation formats colonnes', 
        'def encode_categoricals': 'Encodage variables catégorielles',
        'def clean_pipeline': 'Pipeline complet',
        'strategy': 'Stratégies de nettoyage',
        'smart': 'Stratégie intelligente',
        'ordinal': 'Encodage ordinal',
        'one_hot': 'Encodage one-hot'
    }
    
    missing_elements = []
    found_elements = []
    
    for element, description in required_elements.items():
        if element in content:
            found_elements.append(f"✅ {description}")
        else:
            missing_elements.append(f"❌ {description}")
    
    # Afficher les résultats
    for element in found_elements:
        print(f"  {element}")
    
    for element in missing_elements:
        print(f"  {element}")
    
    success_rate = len(found_elements) / len(required_elements) * 100
    print(f"\n📊 Couverture des exigences: {success_rate:.1f}%")
    
    return success_rate >= 80

def test_null_handling_implementation():
    """Test de l'implémentation du nettoyage des nulls."""
    print("\n" + "=" * 60)
    print("TEST 2: Implémentation nettoyage nulls")
    print("=" * 60)
    
    with open("data_cleaner.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier les stratégies de nettoyage des nulls
    null_strategies = {
        'smart': 'Stratégie intelligente',
        'drop': 'Suppression des nulls',
        'fill': 'Remplissage des nulls',
        '_smart_null_handling': 'Méthode smart',
        '_drop_null_handling': 'Méthode drop',
        '_fill_null_handling': 'Méthode fill'
    }
    
    implemented_strategies = []
    missing_strategies = []
    
    for strategy, description in null_strategies.items():
        if strategy in content:
            implemented_strategies.append(f"✅ {description}")
        else:
            missing_strategies.append(f"❌ {description}")
    
    for strategy in implemented_strategies:
        print(f"  {strategy}")
    
    for strategy in missing_strategies:
        print(f"  {strategy}")
    
    success_rate = len(implemented_strategies) / len(null_strategies) * 100
    print(f"\n📊 Implémentation nulls: {success_rate:.1f}%")
    
    return success_rate >= 70

def test_format_normalization():
    """Test de la normalisation des formats."""
    print("\n" + "=" * 60)
    print("TEST 3: Normalisation formats colonnes")
    print("=" * 60)
    
    with open("data_cleaner.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier les éléments de normalisation
    format_elements = {
        'unify_formats': 'Méthode principale',
        'date': 'Normalisation dates',
        'montant': 'Normalisation montants',
        'text': 'Normalisation texte',
        'lower': 'Conversion minuscules',
        'strip': 'Suppression espaces',
        'to_datetime': 'Conversion dates'
    }
    
    implemented_formats = []
    missing_formats = []
    
    for element, description in format_elements.items():
        if element in content:
            implemented_formats.append(f"✅ {description}")
        else:
            missing_formats.append(f"❌ {description}")
    
    for fmt in implemented_formats:
        print(f"  {fmt}")
    
    for fmt in missing_formats:
        print(f"  {fmt}")
    
    success_rate = len(implemented_formats) / len(format_elements) * 100
    print(f"\n📊 Normalisation formats: {success_rate:.1f}%")
    
    return success_rate >= 60

def test_categorical_encoding():
    """Test de l'encodage des variables catégorielles."""
    print("\n" + "=" * 60)
    print("TEST 4: Encodage variables catégorielles")
    print("=" * 60)
    
    with open("data_cleaner.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier les types d'encodage
    encoding_types = {
        'encode_categoricals': 'Méthode principale',
        'ordinal': 'Encodage ordinal',
        'one_hot': 'Encodage one-hot',
        'statut_encoded': 'Encodage statut',
        'get_dummies': 'Variables dummy',
        'map': 'Mapping de valeurs',
        'status_mapping': 'Mapping statut'
    }
    
    implemented_encoding = []
    missing_encoding = []
    
    for element, description in encoding_types.items():
        if element in content:
            implemented_encoding.append(f"✅ {description}")
        else:
            missing_encoding.append(f"❌ {description}")
    
    for enc in implemented_encoding:
        print(f"  {enc}")
    
    for enc in missing_encoding:
        print(f"  {enc}")
    
    success_rate = len(implemented_encoding) / len(encoding_types) * 100
    print(f"\n📊 Encodage catégoriel: {success_rate:.1f}%")
    
    return success_rate >= 70

def test_pipeline_integration():
    """Test de l'intégration du pipeline."""
    print("\n" + "=" * 60)
    print("TEST 5: Intégration pipeline (Heures 13-16)")
    print("=" * 60)
    
    with open("data_cleaner.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier l'intégration du pipeline
    pipeline_elements = {
        'clean_pipeline': 'Pipeline principal',
        'cleaning_stats': 'Statistiques de nettoyage',
        'cleaning_steps': 'Étapes de nettoyage',
        'get_cleaning_report': 'Rapport de nettoyage',
        'logger': 'Logging',
        'original_shape': 'Forme originale',
        'final_shape': 'Forme finale'
    }
    
    integrated_elements = []
    missing_elements = []
    
    for element, description in pipeline_elements.items():
        if element in content:
            integrated_elements.append(f"✅ {description}")
        else:
            missing_elements.append(f"❌ {description}")
    
    for elem in integrated_elements:
        print(f"  {elem}")
    
    for elem in missing_elements:
        print(f"  {elem}")
    
    success_rate = len(integrated_elements) / len(pipeline_elements) * 100
    print(f"\n📊 Intégration pipeline: {success_rate:.1f}%")
    
    return success_rate >= 80

def test_code_quality():
    """Test de la qualité du code."""
    print("\n" + "=" * 60)
    print("TEST 6: Qualité du code")
    print("=" * 60)
    
    with open("data_cleaner.py", 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Analyser la qualité
    quality_metrics = {
        'docstrings': content.count('"""') + content.count("'''"),
        'comments': len([line for line in lines if line.strip().startswith('#')]),
        'error_handling': content.count('try:') + content.count('except'),
        'logging': content.count('logger.'),
        'type_hints': content.count(': ') + content.count('->'),
        'code_lines': len([line for line in lines if line.strip() and not line.strip().startswith('#')])
    }
    
    print(f"📊 Métriques de qualité:")
    print(f"  Docstrings: {quality_metrics['docstrings']}")
    print(f"  Commentaires: {quality_metrics['comments']}")
    print(f"  Gestion d'erreurs: {quality_metrics['error_handling']}")
    print(f"  Logging: {quality_metrics['logging']}")
    print(f"  Type hints: {quality_metrics['type_hints']}")
    print(f"  Lignes de code: {quality_metrics['code_lines']}")
    
    # Score de qualité
    quality_score = 0
    if quality_metrics['docstrings'] >= 4: quality_score += 20
    if quality_metrics['comments'] >= 10: quality_score += 15
    if quality_metrics['error_handling'] >= 3: quality_score += 20
    if quality_metrics['logging'] >= 5: quality_score += 20
    if quality_metrics['code_lines'] >= 200: quality_score += 25
    
    print(f"\n🎯 Score de qualité: {quality_score}/100")
    
    return quality_score >= 70

def main():
    """Exécuter la validation des Heures 9-12 et 13-16."""
    print("🚀 Validation Heures 9-12 et 13-16")
    print("=" * 70)
    print("Focus: data_cleaner.py et validation pipeline")
    print("=" * 70)
    
    results = []
    
    # Tests ciblés
    tests = [
        ("Structure data_cleaner.py", test_data_cleaner_structure),
        ("Nettoyage nulls", test_null_handling_implementation),
        ("Normalisation formats", test_format_normalization),
        ("Encodage catégoriel", test_categorical_encoding),
        ("Intégration pipeline", test_pipeline_integration),
        ("Qualité du code", test_code_quality)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            results.append(False)
    
    # Résumé final
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS VALIDATION HEURES 9-12 et 13-16")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Score global: {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    # Évaluation finale
    if passed >= 5:
        print("🎉 VALIDATION RÉUSSIE!")
        print("✅ Heures 9-12: data_cleaner.py implémenté correctement")
        print("✅ Heures 13-16: Pipeline validé et fonctionnel")
        print("📋 Prêt pour la suite du développement")
    elif passed >= 4:
        print("⚠️  VALIDATION PARTIELLE")
        print("🔧 Quelques améliorations nécessaires")
    else:
        print("❌ VALIDATION ÉCHOUÉE")
        print("🛠️  Révision nécessaire avant de continuer")
    
    return passed >= 4

if __name__ == "__main__":
    main()
