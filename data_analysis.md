# Analyse du Format des Données MAPAQ

##  Sources de Données Identifiées

### 1. **Données de Montréal - Inspections des aliments et contrevenants**
- **URL** : https://donnees.montreal.ca/dataset/inspection-aliments-contrevenants
- **Format** : CSV disponible
- **Mise à jour** : 2025-09-01 (très récent!)
- **Territoire** : Agglomération montréalaise

### 2. **Données Québec - MAPAQ Inspections**
- **URL** : https://www.donneesquebec.ca/recherche/dataset/vmtl-inspection-aliments-contrevenants
- **Format** : CSV + Visualisation PowerBI
- **Mise à jour** : 2025-09-01
- **Territoire** : Montréal (sous responsabilité MAPAQ)

## Structure des Données Analysée

### **Schéma Principal - Table "Violations"**

| Colonne | Type | Description |
|---------|------|-------------|
| `id_poursuite` | Numérique | Identifiant unique de la poursuite |
| `business_id` | Numérique | Identifiant Ville de l'établissement |
| `date` | Date | Date de l'infraction |
| `date_jugement` | Date | Date du jugement |
| `description` | Texte variable | Description détaillée de l'infraction |
| `etablissement` | Texte variable | Nom de l'établissement |
| `montant` | Numérique | Montant de l'amende ($) |
| `proprietaire` | Texte variable | Nom de l'exploitant |
| `ville` | Texte variable | Territoire de l'établissement |
| `statut` | Liste de valeurs | Statut actuel de l'établissement |
| `date_statut` | Date | Date du dernier changement de statut |
| `categorie` | Texte variable | Catégorie de l'établissement |

### **Valeurs Possibles - Statut**
- **Ouvert** : En exploitation
- **Fermé** : Définitivement fermé
- **Fermé changement d'exploitant** : Changement de propriétaire
- **Sous inspection fédérale** : Changement de juridiction d'inspection

## Variables Cibles pour le Modèle Prédictif

### **Variables Prédictives (Features)**
1. **Temporelles** :
   - `date` : Saisonnalité des infractions
   - `date_statut` : Ancienneté de l'établissement

2. **Établissement** :
   - `etablissement` : Nom (pour extraction thématique)
   - `categorie` : Type d'établissement
   - `ville` : Localisation géographique

3. **Historique** :
   - `business_id` : Pour calculer l'historique des infractions
   - `montant` : Gravité des infractions passées

### **Variable Cible (Target)**
- **Risque d'infraction** : À calculer basé sur :
  - Fréquence des infractions par établissement
  - Gravité (montant des amendes)
  - Récurrence temporelle

## Analyse Qualitative des Données

### **Points Forts** 
- **Données récentes** : Mise à jour septembre 2025
- **Historique riche** : Données depuis janvier 2011
- **Géolocalisation possible** : Adresses disponibles
- **Catégorisation** : Types d'établissements
- **Gravité mesurable** : Montants d'amendes

### **Défis Identifiés** 
- **Données de violations uniquement** : Pas d'inspections "propres"
- **Territoire limité** : Montréal seulement
- **Adresses à normaliser** : Format variable
- **Classification manuelle** : Catégories à enrichir


### **Questions à Résoudre**
- Comment gérer les établissements sans infractions ?
- Faut-il chercher des données d'autres villes québécoises ?
- Comment enrichir avec des données démographiques ?


##  Métriques du Dataset

- **Période couverte** : Janvier 2011 - Septembre 2025 (14+ années)
- **Territoire** : Agglomération montréalaise
- **Type de données** : Violations et contraventions
- **Format** : CSV structuré
- **Fréquence de mise à jour** : Mensuelle

