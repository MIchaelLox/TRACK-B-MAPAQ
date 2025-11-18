"""
Scheduler pour Pipeline MAPAQ
==============================
Automatise l'exécution périodique du pipeline de données

Auteur: Grace MANDIANGU
Date: 2025-11-17
"""

import schedule
import time
import logging
from datetime import datetime
from data_pipeline import DataPipelineManager, PipelineConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Planificateur d'exécution automatique du pipeline"""
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.pipeline = DataPipelineManager(self.config)
        logger.info("Scheduler initialisé")
    
    def run_pipeline_job(self):
        """Exécute le pipeline comme job planifié"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🕐 EXÉCUTION PLANIFIÉE DU PIPELINE")
        logger.info(f"   Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*70}\n")
        
        try:
            result = self.pipeline.run_full_pipeline()
            
            if result['status'] == 'success':
                logger.info("✅ Pipeline exécuté avec succès")
            else:
                logger.error(f"❌ Pipeline échoué: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution: {e}")
    
    def start_daily_schedule(self, time_str: str = "02:00"):
        """
        Lance l'exécution quotidienne du pipeline
        
        Args:
            time_str: Heure d'exécution (format HH:MM)
        """
        schedule.every().day.at(time_str).do(self.run_pipeline_job)
        
        logger.info(f"📅 Pipeline planifié quotidiennement à {time_str}")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
        except KeyboardInterrupt:
            logger.info("\n⏹️  Scheduler arrêté")
    
    def start_hourly_schedule(self):
        """Lance l'exécution horaire du pipeline"""
        schedule.every().hour.do(self.run_pipeline_job)
        
        logger.info("📅 Pipeline planifié toutes les heures")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("\n⏹️  Scheduler arrêté")
    
    def start_interval_schedule(self, minutes: int = 30):
        """
        Lance l'exécution à intervalle régulier
        
        Args:
            minutes: Intervalle en minutes
        """
        schedule.every(minutes).minutes.do(self.run_pipeline_job)
        
        logger.info(f"📅 Pipeline planifié toutes les {minutes} minutes")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("\n⏹️  Scheduler arrêté")


if __name__ == '__main__':
    import sys
    
    scheduler = PipelineScheduler()
    
    print("\n" + "="*70)
    print("🤖 SCHEDULER PIPELINE MAPAQ")
    print("="*70)
    print("\nOptions:")
    print("  1. Exécution quotidienne (02:00)")
    print("  2. Exécution horaire")
    print("  3. Exécution toutes les 30 minutes")
    print("  4. Exécution immédiate (une fois)")
    print("="*70)
    
    choice = input("\nChoisissez une option (1-4): ").strip()
    
    if choice == '1':
        scheduler.start_daily_schedule("02:00")
    elif choice == '2':
        scheduler.start_hourly_schedule()
    elif choice == '3':
        scheduler.start_interval_schedule(30)
    elif choice == '4':
        scheduler.run_pipeline_job()
    else:
        print("Option invalide")
