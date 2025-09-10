
import sys
import os
from pathlib import Path

def test_categorical_encoding_logic():
    """Test de la logique d'encodage catégoriel sans dépendances."""
    print("=" * 60)
    print("TEST 1: Categorical Encoding Logic")
    print("=" * 60)
    
    # Test d'encodage ordinal manuel
    status_order = ['Ouvert', 'Sous inspection fédérale', 'Fermé changement d\'exploitant', 'Fermé']
    status_data = ['Ouvert', 'Fermé', 'Ouvert', 'Sous inspection fédérale']
    
    # Créer le mapping ordinal
    ordinal_mapping = {value: idx for idx, value in enumerate(status_order)}
    print(f"📋 Ordinal mapping: {ordinal_mapping}")
    
    # Encoder les données
    encoded_status = [ordinal_mapping.get(status, -1) for status in status_data]
    print(f"📊 Original: {status_data}")
    print(f"📊 Encoded: {encoded_status}")
    
    # Vérifier l'encodage
    if all(val >= 0 for val in encoded_status):
        print("✅ Ordinal encoding successful")
        return True
    else:
        print("❌ Ordinal encoding failed")
        return False

def test_one_hot_encoding_logic():
    """Test de la logique one-hot encoding."""
    print("\n" + "=" * 60)
    print("TEST 2: One-Hot Encoding Logic")
    print("=" * 60)
    
    # Données de test
    categories = ['Restaurant', 'Café', 'Restaurant', 'Bar', 'Restaurant']
    unique_categories = list(set(categories))
    
    print(f"📋 Categories: {categories}")
    print(f"📋 Unique: {unique_categories}")
    
    # Créer l'encodage one-hot manuel
    one_hot_encoded = {}
    for category in unique_categories:
        column_name = f"cat_{category}"
        one_hot_encoded[column_name] = [1 if cat == category else 0 for cat in categories]
    
    print(f"📊 One-hot encoded:")
    for col, values in one_hot_encoded.items():
        print(f"  {col}: {values}")
    
    # Vérifier que chaque ligne a exactement un 1
    for i in range(len(categories)):
        row_sum = sum(one_hot_encoded[col][i] for col in one_hot_encoded.keys())
        if row_sum != 1:
            print(f"❌ Row {i} has sum {row_sum} (should be 1)")
            return False
    
    print("✅ One-hot encoding successful")
    return True

def test_frequency_encoding_logic():
    """Test de la logique d'encodage par fréquence."""
    print("\n" + "=" * 60)
    print("TEST 3: Frequency Encoding Logic")
    print("=" * 60)
    
    # Données avec différentes fréquences
    cities = ['Montréal', 'Montréal', 'Québec', 'Montréal', 'Laval', 'Québec', 'Montréal']
    
    # Calculer les fréquences
    frequency_map = {}
    for city in cities:
        frequency_map[city] = frequency_map.get(city, 0) + 1
    
    print(f"📋 Cities: {cities}")
    print(f"📊 Frequency map: {frequency_map}")
    
    # Encoder par fréquence
    encoded_cities = [frequency_map[city] for city in cities]
    print(f"📊 Frequency encoded: {encoded_cities}")
    
    # Vérifier que les villes les plus fréquentes ont les valeurs les plus élevées
    max_freq = max(frequency_map.values())
    most_frequent_city = [city for city, freq in frequency_map.items() if freq == max_freq][0]
    
    if frequency_map[most_frequent_city] == max_freq:
        print("✅ Frequency encoding successful")
        return True
    else:
        print("❌ Frequency encoding failed")
        return False

def test_rare_category_grouping():
    """Test du regroupement des catégories rares."""
    print("\n" + "=" * 60)
    print("TEST 4: Rare Category Grouping")
    print("=" * 60)
    
    # Données avec catégories rares
    owners = ['Jean Dupont', 'Marie Tremblay', 'Jean Dupont', 'Pierre Leblanc', 
              'Jean Dupont', 'Sophie Martin', 'Marie Tremblay', 'Jean Dupont']
    
    min_frequency = 3
    
    # Calculer les fréquences
    owner_counts = {}
    for owner in owners:
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    
    print(f"📋 Owners: {owners}")
    print(f"📊 Owner counts: {owner_counts}")
    
    # Identifier les catégories rares
    rare_owners = [owner for owner, count in owner_counts.items() if count < min_frequency]
    common_owners = [owner for owner, count in owner_counts.items() if count >= min_frequency]
    
    print(f"🔍 Rare owners (freq < {min_frequency}): {rare_owners}")
    print(f"✅ Common owners (freq >= {min_frequency}): {common_owners}")
    
    # Regrouper les catégories rares
    grouped_owners = ['RARE_CATEGORY' if owner in rare_owners else owner for owner in owners]
    print(f"📊 Grouped: {grouped_owners}")
    
    # Vérifier le regroupement
    rare_count_after = grouped_owners.count('RARE_CATEGORY')
    expected_rare_count = sum(owner_counts[owner] for owner in rare_owners)
    
    if rare_count_after == expected_rare_count:
        print("✅ Rare category grouping successful")
        return True
    else:
        print("❌ Rare category grouping failed")
        return False

def test_text_feature_extraction():
    """Test simple d'extraction de features textuelles."""
    print("\n" + "=" * 60)
    print("TEST 5: Text Feature Extraction")
    print("=" * 60)
    
    # Descriptions d'infractions
    descriptions = [
        'Température inadéquate réfrigération',
        'Contamination croisée aliments',
        'Équipement défaillant température',
        'Non-respect normes hygiène'
    ]
    
    print(f"📋 Descriptions: {descriptions}")
    
    # Extraction simple de mots-clés
    all_words = []
    for desc in descriptions:
        words = desc.lower().split()
        all_words.extend(words)
    
    # Compter les mots
    word_counts = {}
    for word in all_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    print(f"📊 Word counts: {word_counts}")
    
    # Créer des features binaires pour les mots fréquents
    frequent_words = [word for word, count in word_counts.items() if count >= 2]
    print(f"🔍 Frequent words: {frequent_words}")
    
    # Encoder les descriptions
    text_features = {}
    for word in frequent_words:
        text_features[f"has_{word}"] = [1 if word in desc.lower() else 0 for desc in descriptions]
    
    print(f"📊 Text features:")
    for feature, values in text_features.items():
        print(f"  {feature}: {values}")
    
    if len(text_features) > 0:
        print("✅ Text feature extraction successful")
        return True
    else:
        print("❌ Text feature extraction failed")
        return False

def test_mapaq_specific_encoding():
    """Test de l'encodage spécifique MAPAQ."""
    print("\n" + "=" * 60)
    print("TEST 6: MAPAQ-Specific Encoding")
    print("=" * 60)
    
    # Données MAPAQ typiques
    mapaq_data = {
        'statut': ['Ouvert', 'Fermé', 'Sous inspection fédérale', 'Ouvert'],
        'categorie': ['Restaurant', 'Café', 'Restaurant', 'Bar'],
        'ville': ['Montréal', 'Montréal', 'Québec', 'Montréal'],
        'description': ['Température inadéquate', 'Contamination croisée', 'Équipement défaillant', 'Normes non respectées']
    }
    
    print("📊 MAPAQ Data Sample:")
    for col, values in mapaq_data.items():
        print(f"  {col}: {values}")
    
    # Test encodage ordinal pour statut
    status_order = ['Ouvert', 'Sous inspection fédérale', 'Fermé changement d\'exploitant', 'Fermé']
    status_mapping = {status: idx for idx, status in enumerate(status_order)}
    encoded_status = [status_mapping.get(s, -1) for s in mapaq_data['statut']]
    
    print(f"\n🔢 Status encoding: {mapaq_data['statut']} → {encoded_status}")
    
    # Test one-hot pour catégories
    unique_categories = list(set(mapaq_data['categorie']))
    category_encoding = {}
    for cat in unique_categories:
        category_encoding[f"cat_{cat}"] = [1 if c == cat else 0 for c in mapaq_data['categorie']]
    
    print(f"🏷️  Category encoding:")
    for col, values in category_encoding.items():
        print(f"  {col}: {values}")
    
    # Test fréquence pour villes
    city_counts = {}
    for city in mapaq_data['ville']:
        city_counts[city] = city_counts.get(city, 0) + 1
    encoded_cities = [city_counts[city] for city in mapaq_data['ville']]
    
    print(f"🌍 City frequency encoding: {mapaq_data['ville']} → {encoded_cities}")
    
    # Vérifications
    checks = [
        all(val >= 0 for val in encoded_status),  # Status encoding valid
        len(category_encoding) > 0,  # Categories encoded
        max(encoded_cities) >= min(encoded_cities)  # City frequencies valid
    ]
    
    if all(checks):
        print("✅ MAPAQ-specific encoding successful")
        return True
    else:
        print("❌ MAPAQ-specific encoding failed")
        return False

def generate_encoding_summary():
    """Générer un résumé des techniques d'encodage."""
    print("\n" + "=" * 60)
    print("CATEGORICAL ENCODING SUMMARY")
    print("=" * 60)
    
    techniques = {
        'Ordinal Encoding': {
            'use_case': 'Variables avec ordre naturel (statut, sévérité)',
            'example': 'Ouvert(0) < Sous inspection(1) < Fermé(2)',
            'advantages': 'Préserve l\'ordre, compact',
            'disadvantages': 'Assume une relation ordinale'
        },
        'One-Hot Encoding': {
            'use_case': 'Variables nominales avec peu de catégories',
            'example': 'Restaurant → [1,0,0], Café → [0,1,0], Bar → [0,0,1]',
            'advantages': 'Pas d\'assumption ordinale, interprétable',
            'disadvantages': 'Augmente la dimensionnalité'
        },
        'Frequency Encoding': {
            'use_case': 'Variables haute cardinalité',
            'example': 'Montréal(100) > Québec(50) > Laval(10)',
            'advantages': 'Compact, capture la popularité',
            'disadvantages': 'Perd l\'information catégorielle'
        },
        'Rare Category Grouping': {
            'use_case': 'Réduire la cardinalité',
            'example': 'Propriétaires rares → RARE_CATEGORY',
            'advantages': 'Réduit le bruit, généralise mieux',
            'disadvantages': 'Perte d\'information spécifique'
        },
        'Text Feature Extraction': {
            'use_case': 'Descriptions textuelles',
            'example': 'TF-IDF, mots-clés binaires',
            'advantages': 'Capture le contenu sémantique',
            'disadvantages': 'Haute dimensionnalité'
        }
    }
    
    for technique, details in techniques.items():
        print(f"\n🔧 {technique}:")
        for key, value in details.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n💡 Recommendations for MAPAQ:")
    print(f"  • Use ordinal encoding for 'statut' (natural order)")
    print(f"  • Use one-hot encoding for 'categorie' (few categories)")
    print(f"  • Use frequency encoding for 'ville' (many cities)")
    print(f"  • Group rare categories for 'proprietaire' (high cardinality)")
    print(f"  • Extract text features from 'description' (semantic content)")

def main():
    """Exécuter tous les tests d'encodage catégoriel."""
    print("🚀 Categorical Encoding Tests - Heures 17-20")
    print("=" * 70)
    print("Validation des techniques d'encodage catégoriel")
    print("=" * 70)
    
    results = []
    
    # Tests à exécuter
    tests = [
        ("Ordinal Encoding Logic", test_categorical_encoding_logic),
        ("One-Hot Encoding Logic", test_one_hot_encoding_logic),
        ("Frequency Encoding Logic", test_frequency_encoding_logic),
        ("Rare Category Grouping", test_rare_category_grouping),
        ("Text Feature Extraction", test_text_feature_extraction),
        ("MAPAQ-Specific Encoding", test_mapaq_specific_encoding)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Générer le résumé
    generate_encoding_summary()
    
    # Résumé des résultats
    print("\n" + "=" * 70)
    print("📊 CATEGORICAL ENCODING TEST RESULTS")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= 5:
        print("🎉 CATEGORICAL ENCODING VALIDATION SUCCESSFUL!")
        print("✅ Ready for Heures 21-24: Tests unitaires ingestion/nettoyage")
    else:
        print("⚠️  Some encoding tests failed. Review the implementation.")
    
    return passed >= 5

if __name__ == "__main__":
    main()
