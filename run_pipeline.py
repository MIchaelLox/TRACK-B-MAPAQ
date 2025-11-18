"""
Script de Lancement du Pipeline MAPAQ
======================================
Interface en ligne de commande pour exécuter le pipeline

Auteur: Grace MANDIANGU
Date: 2025-11-17
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from data_pipeline import DataPipelineManager, PipelineConfig


def print_banner():
    """Affiche la bannière du programme"""
    print("\n" + "="*70)
    print("🚀 PIPELINE DE DONNÉES MAPAQ - TRACK B")
    print("   Système Prédictif de Risques Sanitaires")
    print("="*70 + "\n")


def print_summary(result: dict):
    """Affiche le résumé d'exécution"""
    print("\n" + "="*70)
    print("📊 RÉSUMÉ D'EXÉCUTION")
    print("="*70)
    print(f"Statut: {result['status'].upper()}")
    
    if result['status'] == 'success':
        print(f"✅ Enregistrements traités: {result.get('records_processed', 0)}")
    else:
        print(f"❌ Erreur: {result.get('error', 'Inconnue')}")
    
    print("="*70 + "\n")


def run_pipeline_interactive():
    """Mode interactif"""
    print_banner()
    
    print("Configuration du pipeline:")
    print("-" * 70)
    
    # Configuration interactive
    source_path = input("Chemin des données source [data/raw/mapaq_inspections.csv]: ").strip()
    if not source_path:
        source_path = "data/raw/mapaq_inspections.csv"
    
    db_path = input("Chemin de la base de données [mapaq_dashboard.db]: ").strip()
    if not db_path:
        db_path = "mapaq_dashboard.db"
    
    backup = input("Activer les backups? [O/n]: ").strip().lower()
    backup_enabled = backup != 'n'
    
    print("\n" + "-" * 70)
    print("Configuration:")
    print(f"  Source: {source_path}")
    print(f"  Base de données: {db_path}")
    print(f"  Backups: {'Activés' if backup_enabled else 'Désactivés'}")
    print("-" * 70 + "\n")
    
    confirm = input("Lancer le pipeline? [O/n]: ").strip().lower()
    if confirm == 'n':
        print("❌ Annulé")
        return
    
    # Créer la configuration
    config = PipelineConfig(
        source_data_path=source_path,
        output_db_path=db_path,
        backup_enabled=backup_enabled
    )
    
    # Exécuter le pipeline
    print("\n🚀 Démarrage du pipeline...\n")
    pipeline = DataPipelineManager(config)
    result = pipeline.run_full_pipeline()
    
    print_summary(result)


def run_pipeline_cli(args):
    """Mode ligne de commande"""
    print_banner()
    
    # Charger la configuration
    if args.config:
        config = PipelineConfig.from_file(args.config)
    else:
        config = PipelineConfig(
            source_data_path=args.source,
            output_db_path=args.output,
            backup_enabled=args.backup
        )
    
    # Afficher la configuration
    print("Configuration:")
    print(f"  Source: {config.source_data_path}")
    print(f"  Base de données: {config.output_db_path}")
    print(f"  Backups: {'Activés' if config.backup_enabled else 'Désactivés'}")
    print(f"  Tentatives max: {config.max_retries}")
    print()
    
    # Exécuter le pipeline
    pipeline = DataPipelineManager(config)
    result = pipeline.run_full_pipeline()
    
    print_summary(result)
    
    # Sauvegarder le rapport si demandé
    if args.report:
        report_path = Path(args.report)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 Rapport sauvegardé: {report_path}")
    
    # Code de sortie
    sys.exit(0 if result['status'] == 'success' else 1)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='Pipeline de données MAPAQ Track-B',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  Mode interactif:
    python run_pipeline.py
  
  Mode CLI avec options:
    python run_pipeline.py --source data/raw/inspections.csv --output mapaq.db
  
  Avec fichier de configuration:
    python run_pipeline.py --config pipeline_config.json
  
  Avec rapport de sortie:
    python run_pipeline.py --report rapport_pipeline.json
        """
    )
    
    parser.add_argument(
        '--source',
        default='data/raw/mapaq_inspections.csv',
        help='Chemin du fichier source (CSV)'
    )
    
    parser.add_argument(
        '--output',
        default='mapaq_dashboard.db',
        help='Chemin de la base de données de sortie'
    )
    
    parser.add_argument(
        '--config',
        help='Fichier de configuration JSON'
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Activer les backups de la base de données'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_false',
        dest='backup',
        help='Désactiver les backups'
    )
    
    parser.add_argument(
        '--report',
        help='Chemin du fichier de rapport JSON'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Mode interactif'
    )
    
    args = parser.parse_args()
    
    # Mode interactif si aucun argument ou --interactive
    if len(sys.argv) == 1 or args.interactive:
        run_pipeline_interactive()
    else:
        run_pipeline_cli(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
