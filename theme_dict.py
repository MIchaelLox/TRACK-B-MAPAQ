
import pandas as pd
import numpy as np
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import Counter, defaultdict
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThemeDictionary:
    """
    Dictionnaire thématique pour classification des restaurants par type de cuisine.
    
    Fonctionnalités:
    - Classification par mots-clés (noms, descriptions, menus)
    - Algorithmes NLP basiques (TF-IDF, similarité)
    - Base de données de thèmes culinaires
    - Détection automatique de nouveaux thèmes
    - Scoring de confiance pour les classifications
    """
    
    def __init__(self, data: pd.DataFrame, theme_db_file: str = "theme_database.json"):
        """
        Initialiser le dictionnaire thématique.
        
        Args:
            data: DataFrame contenant les données de restaurants
            theme_db_file: Fichier de base de données des thèmes
        """
        self.data = data.copy()
        self.theme_db_file = Path(theme_db_file)
        
        # Statistiques de classification
        self.classification_stats = {
            'themes_classified': 0,
            'new_themes_detected': 0,
            'confidence_scores': [],
            'unclassified': 0
        }
        
        # Initialiser la base de données de thèmes
        self._init_theme_database()
        
        # Charger ou créer la base de données
        self.theme_database = self._load_theme_database()
        
        logger.info(f"ThemeDictionary initialized with {len(data)} records")
        logger.info(f"Theme database loaded with {len(self.theme_database)} categories")
    
    def _init_theme_database(self):
        """Initialiser la base de données de thèmes culinaires."""
        
        # Base de données complète des thèmes culinaires
        self.default_themes = {
            'italien': {
                'keywords': ['pizza', 'pizzeria', 'pasta', 'italien', 'trattoria', 'ristorante', 
                           'spaghetti', 'lasagne', 'risotto', 'antipasti', 'gelato', 'espresso'],
                'patterns': [r'pizz\w*', r'ital\w*', r'tratt\w*', r'rist\w*'],
                'confidence_boost': 1.2
            },
            'asiatique': {
                'keywords': ['sushi', 'ramen', 'asian', 'asiatique', 'chinois', 'thai', 'vietnamien',
                           'japonais', 'coréen', 'dim sum', 'pho', 'pad thai', 'tempura'],
                'patterns': [r'sush\w*', r'ram\w*', r'asi\w*', r'chin\w*', r'jap\w*'],
                'confidence_boost': 1.1
            },
            'français': {
                'keywords': ['bistro', 'brasserie', 'français', 'french', 'crêpe', 'crêperie',
                           'boulangerie', 'pâtisserie', 'fromagerie', 'charcuterie'],
                'patterns': [r'bistr\w*', r'brass\w*', r'fran\w*', r'crêp\w*'],
                'confidence_boost': 1.0
            },
            'mexicain': {
                'keywords': ['mexicain', 'mexican', 'taco', 'burrito', 'quesadilla', 'nachos',
                           'salsa', 'guacamole', 'tortilla', 'enchilada'],
                'patterns': [r'mexic\w*', r'tac\w*', r'burrit\w*'],
                'confidence_boost': 1.1
            },
            'indien': {
                'keywords': ['indien', 'indian', 'curry', 'tandoor', 'biryani', 'naan', 'samosa',
                           'masala', 'vindaloo', 'tikka'],
                'patterns': [r'ind\w*', r'curr\w*', r'tand\w*'],
                'confidence_boost': 1.1
            },
            'fast_food': {
                'keywords': ['fast', 'burger', 'hamburger', 'frites', 'hot dog', 'sandwich',
                           'subway', 'mcdonald', 'kfc', 'quick', 'drive'],
                'patterns': [r'fast\w*', r'burg\w*', r'sand\w*'],
                'confidence_boost': 0.9
            },
            'café_bar': {
                'keywords': ['café', 'coffee', 'bar', 'pub', 'taverne', 'bière', 'wine', 'vin',
                           'cocktail', 'lounge', 'espresso', 'cappuccino'],
                'patterns': [r'caf\w*', r'coff\w*', r'bar\w*', r'pub\w*'],
                'confidence_boost': 0.8
            },
            'fruits_mer': {
                'keywords': ['fruits de mer', 'seafood', 'poisson', 'fish', 'homard', 'crevette',
                           'huître', 'moule', 'saumon', 'thon', 'crabe'],
                'patterns': [r'sea\w*', r'fish\w*', r'poiss\w*'],
                'confidence_boost': 1.0
            },
            'steakhouse': {
                'keywords': ['steak', 'steakhouse', 'grill', 'bbq', 'barbecue', 'viande', 'beef',
                           'côte', 'filet', 'ribeye'],
                'patterns': [r'steak\w*', r'grill\w*', r'bbq\w*', r'barb\w*'],
                'confidence_boost': 1.0
            },
            'végétarien': {
                'keywords': ['végétarien', 'vegetarian', 'vegan', 'bio', 'organic', 'santé',
                           'health', 'salade', 'légume', 'quinoa'],
                'patterns': [r'veg\w*', r'bio\w*', r'org\w*', r'health\w*'],
                'confidence_boost': 1.0
            }
        }
    
    def _load_theme_database(self) -> Dict:
        """Charger la base de données de thèmes."""
        try:
            if self.theme_db_file.exists():
                with open(self.theme_db_file, 'r', encoding='utf-8') as f:
                    loaded_db = json.load(f)
                # Fusionner avec les thèmes par défaut
                merged_db = self.default_themes.copy()
                merged_db.update(loaded_db)
                return merged_db
        except Exception as e:
            logger.warning(f"Could not load theme database: {e}")
        
        return self.default_themes.copy()
    
    def _save_theme_database(self):
        """Sauvegarder la base de données de thèmes."""
        try:
            with open(self.theme_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.theme_database, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save theme database: {e}")
    
    def classify_theme(self, name_or_menu: str, confidence_threshold: float = 0.3) -> Tuple[str, float]:
        """
        Classifier un restaurant par type de cuisine.
        
        Args:
            name_or_menu: Nom du restaurant ou description du menu
            confidence_threshold: Seuil de confiance minimum
            
        Returns:
            Tuple (theme_label, confidence_score)
        """
        if not name_or_menu or pd.isna(name_or_menu):
            return 'non_classifié', 0.0
        
        text = str(name_or_menu).lower().strip()
        
        # Scores pour chaque thème
        theme_scores = {}
        
        for theme_name, theme_data in self.theme_database.items():
            score = self._calculate_theme_score(text, theme_data)
            if score > 0:
                theme_scores[theme_name] = score
        
        # Trouver le meilleur thème
        if theme_scores:
            best_theme = max(theme_scores, key=theme_scores.get)
            best_score = theme_scores[best_theme]
            
            if best_score >= confidence_threshold:
                return best_theme, best_score
        
        # Tentative de détection de nouveau thème
        new_theme = self._detect_new_theme(text)
        if new_theme:
            return new_theme, 0.5
        
        return 'non_classifié', 0.0
    
    def _calculate_theme_score(self, text: str, theme_data: Dict) -> float:
        """Calculer le score de correspondance pour un thème."""
        score = 0.0
        
        # Score basé sur les mots-clés
        keywords = theme_data.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword in text)
        keyword_score = keyword_matches / len(keywords) if keywords else 0
        
        # Score basé sur les patterns regex
        patterns = theme_data.get('patterns', [])
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, text))
        pattern_score = pattern_matches / len(patterns) if patterns else 0
        
        # Score combiné
        base_score = (keyword_score * 0.7) + (pattern_score * 0.3)
        
        # Appliquer le boost de confiance
        confidence_boost = theme_data.get('confidence_boost', 1.0)
        final_score = base_score * confidence_boost
        
        return min(final_score, 1.0)  # Limiter à 1.0
    
    def _detect_new_theme(self, text: str) -> Optional[str]:
        """Détecter un nouveau thème potentiel."""
        # Mots-clés culinaires génériques
        culinary_indicators = [
            'restaurant', 'cuisine', 'food', 'kitchen', 'chef', 'menu',
            'spécialité', 'traditionnel', 'authentique', 'maison'
        ]
        
        # Vérifier si le texte contient des indicateurs culinaires
        has_culinary_context = any(indicator in text for indicator in culinary_indicators)
        
        if has_culinary_context:
            # Extraire des mots potentiellement thématiques
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', text)
            for word in words:
                if word not in [kw for theme in self.theme_database.values() 
                              for kw in theme.get('keywords', [])]:
                    # Nouveau thème potentiel détecté
                    self.classification_stats['new_themes_detected'] += 1
                    return f'nouveau_{word}'
        
        return None
    
    def build_theme_column(self, name_column: str = 'etablissement', 
                          description_column: Optional[str] = None) -> pd.DataFrame:
        """
        Ajouter une colonne avec le type de cuisine inféré pour tous les restaurants.
        
        Args:
            name_column: Colonne contenant le nom du restaurant
            description_column: Colonne optionnelle avec description/menu
            
        Returns:
            DataFrame avec colonnes thématiques ajoutées
        """
        logger.info(f"Building theme classification for {len(self.data)} restaurants")
        
        themed_data = self.data.copy()
        themes = []
        confidence_scores = []
        
        for idx, row in self.data.iterrows():
            # Construire le texte à analyser
            text_parts = []
            
            if name_column in row and pd.notna(row[name_column]):
                text_parts.append(str(row[name_column]))
            
            if description_column and description_column in row and pd.notna(row[description_column]):
                text_parts.append(str(row[description_column]))
            
            combined_text = ' '.join(text_parts)
            
            # Classifier le thème
            theme, confidence = self.classify_theme(combined_text)
            themes.append(theme)
            confidence_scores.append(confidence)
            
            self.classification_stats['themes_classified'] += 1
            if theme == 'non_classifié':
                self.classification_stats['unclassified'] += 1
        
        # Ajouter les colonnes
        themed_data['theme_cuisine'] = themes
        themed_data['theme_confidence'] = confidence_scores
        
        # Statistiques
        self.classification_stats['confidence_scores'] = confidence_scores
        
        logger.info(f"Theme classification completed: {len(themes)} restaurants processed")
        return themed_data
    
    def get_theme_statistics(self) -> Dict[str, Any]:
        """Obtenir des statistiques sur la classification thématique."""
        if not self.classification_stats['confidence_scores']:
            return {'error': 'No classification performed yet'}
        
        confidence_scores = self.classification_stats['confidence_scores']
        
        return {
            'classification_stats': self.classification_stats,
            'confidence_analysis': {
                'mean_confidence': np.mean(confidence_scores) if confidence_scores else 0,
                'median_confidence': np.median(confidence_scores) if confidence_scores else 0,
                'min_confidence': min(confidence_scores) if confidence_scores else 0,
                'max_confidence': max(confidence_scores) if confidence_scores else 0
            },
            'theme_distribution': self._get_theme_distribution(),
            'database_info': {
                'total_themes': len(self.theme_database),
                'theme_names': list(self.theme_database.keys())
            }
        }
    
    def _get_theme_distribution(self) -> Dict[str, int]:
        """Obtenir la distribution des thèmes dans les données."""
        if 'theme_cuisine' not in self.data.columns:
            return {}
        
        return dict(Counter(self.data['theme_cuisine']))
    
    def add_custom_theme(self, theme_name: str, keywords: List[str], 
                        patterns: Optional[List[str]] = None, confidence_boost: float = 1.0):
        """
        Ajouter un thème personnalisé à la base de données.
        
        Args:
            theme_name: Nom du nouveau thème
            keywords: Liste de mots-clés
            patterns: Liste optionnelle de patterns regex
            confidence_boost: Facteur de boost de confiance
        """
        self.theme_database[theme_name] = {
            'keywords': keywords,
            'patterns': patterns or [],
            'confidence_boost': confidence_boost,
            'custom': True,
            'created_date': datetime.now().isoformat()
        }
        
        self._save_theme_database()
        logger.info(f"Custom theme '{theme_name}' added with {len(keywords)} keywords")
    
    def export_theme_analysis(self, output_file: str):
        """Exporter l'analyse thématique."""
        try:
            analysis_data = {
                'theme_statistics': self.get_theme_statistics(),
                'theme_database': self.theme_database,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Theme analysis exported to {output_file}")
        except Exception as e:
            logger.error(f"Export failed: {e}")

def test_theme_dictionary():
    """Test basique du dictionnaire thématique."""
    print("🧪 Testing ThemeDictionary...")
    
    # Créer des données de test
    test_data = pd.DataFrame({
        'etablissement': [
            'Pizzeria Mario - Cuisine Italienne Authentique',
            'Sushi Zen - Restaurant Japonais',
            'Le Bistro Français - Cuisine Traditionnelle',
            'Taco Loco - Spécialités Mexicaines',
            'Burger Palace - Fast Food Américain',
            'Café Central - Coffee & Pastries',
            'Curry House - Cuisine Indienne',
            'Ocean Grill - Fruits de mer frais'
        ]
    })
    
    # Initialiser le dictionnaire thématique
    theme_dict = ThemeDictionary(test_data)
    
    # Test de classification individuelle
    print("\n📋 Individual Theme Classification:")
    test_names = test_data['etablissement'].tolist()
    
    for i, name in enumerate(test_names):
        theme, confidence = theme_dict.classify_theme(name)
        print(f"  {i+1}. {name}")
        print(f"     → Theme: {theme} (Confidence: {confidence:.2f})")
    
    # Test de construction de colonne thématique
    themed_data = theme_dict.build_theme_column('etablissement')
    print(f"\n✅ Theme column built for {len(themed_data)} restaurants")
    
    # Statistiques
    stats = theme_dict.get_theme_statistics()
    print(f"\n📊 Theme Statistics:")
    print(f"  Restaurants classified: {stats['classification_stats']['themes_classified']}")
    print(f"  Mean confidence: {stats['confidence_analysis']['mean_confidence']:.2f}")
    print(f"  Unclassified: {stats['classification_stats']['unclassified']}")
    
    # Distribution des thèmes
    if 'theme_distribution' in stats:
        print(f"\n🎯 Theme Distribution:")
        for theme, count in stats['theme_distribution'].items():
            print(f"  {theme}: {count}")
    
    print("🎉 ThemeDictionary test completed!")

if __name__ == "__main__":
    test_theme_dictionary()
