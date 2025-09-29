"""
Tests Utilisateur Interface MAPAQ - interface_user_tests.py
Suite complète de tests d'interface utilisateur et d'expérience

Auteur: Mouhamed Thiaw
Date: 2025-01-27
Heures: 113-116 (Vendredi - Tests utilisateur interface)
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Résultat d'un test d'interface."""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARNING'
    duration: float
    details: Dict[str, Any]
    errors: List[str]
    recommendations: List[str]

class InterfaceUserTester:
    """Testeur d'interface utilisateur pour MAPAQ."""
    
    def __init__(self):
        """Initialise le testeur d'interface."""
        self.test_results = []
        self.test_config = {
            'timeout': 30,
            'retry_count': 3,
            'performance_tracking': True
        }
        logger.info("Testeur d'interface MAPAQ initialisé")
    
    def run_interface_validation_tests(self) -> List[TestResult]:
        """Exécute les tests de validation d'interface."""
        logger.info("=== TESTS DE VALIDATION INTERFACE ===")
        results = []
        
        results.append(self._test_html_css_validation())
        results.append(self._test_responsive_design())
        results.append(self._test_loading_performance())
        results.append(self._test_accessibility())
        
        return results
    
    def _test_html_css_validation(self) -> TestResult:
        """Test de validation HTML/CSS."""
        start_time = time.time()
        errors = []
        recommendations = []
        
        try:
            html_files = list(Path('.').glob('*.html'))
            details = {
                'html_files_found': len(html_files),
                'files_checked': [],
                'validation_issues': []
            }
            
            for html_file in html_files:
                if html_file.exists():
                    details['files_checked'].append(str(html_file))
                    
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérifications basiques
                    if '<!DOCTYPE html>' not in content:
                        errors.append(f"{html_file}: DOCTYPE manquant")
                    
                    if '<html lang=' not in content:
                        recommendations.append(f"{html_file}: Attribut lang recommandé")
                    
                    if 'viewport' not in content:
                        errors.append(f"{html_file}: Meta viewport manquant")
            
            status = "PASS" if not errors else "FAIL" if len(errors) > 3 else "WARNING"
            
            return TestResult(
                test_name="Validation HTML/CSS",
                status=status,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            return TestResult(
                test_name="Validation HTML/CSS",
                status="FAIL",
                duration=time.time() - start_time,
                details={'error': str(e)},
                errors=[f"Erreur test validation: {e}"],
                recommendations=[]
            )
    
    def _test_responsive_design(self) -> TestResult:
        """Test du design responsive."""
        start_time = time.time()
        errors = []
        recommendations = []
        
        try:
            html_files = list(Path('.').glob('*.html'))
            details = {
                'breakpoints_found': [],
                'media_queries': 0,
                'responsive_elements': []
            }
            
            for html_file in html_files:
                if html_file.exists():
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if '@media' in content:
                        details['media_queries'] += content.count('@media')
                        
                        breakpoints = ['768px', '1024px', '480px']
                        for bp in breakpoints:
                            if bp in content:
                                details['breakpoints_found'].append(bp)
                    
                    responsive_elements = ['viewport', 'max-width', 'flex', 'grid']
                    for element in responsive_elements:
                        if element in content.lower():
                            details['responsive_elements'].append(element)
            
            if details['media_queries'] == 0:
                errors.append("Aucune media query trouvée")
            
            if not details['breakpoints_found']:
                errors.append("Aucun breakpoint responsive trouvé")
            
            status = "PASS" if not errors else "WARNING"
            
            return TestResult(
                test_name="Design Responsive",
                status=status,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            return TestResult(
                test_name="Design Responsive",
                status="FAIL",
                duration=time.time() - start_time,
                details={'error': str(e)},
                errors=[f"Erreur test responsive: {e}"],
                recommendations=[]
            )
    
    def _test_loading_performance(self) -> TestResult:
        """Test de performance de chargement."""
        start_time = time.time()
        errors = []
        recommendations = []
        
        try:
            html_files = list(Path('.').glob('*.html'))
            details = {
                'file_sizes': {},
                'total_size': 0,
                'large_files': []
            }
            
            for html_file in html_files:
                if html_file.exists():
                    size = html_file.stat().st_size
                    details['file_sizes'][str(html_file)] = size
                    details['total_size'] += size
                    
                    if size > 500 * 1024:  # >500KB
                        details['large_files'].append(str(html_file))
                        recommendations.append(f"{html_file}: Fichier volumineux")
            
            total_mb = details['total_size'] / (1024 * 1024)
            
            if total_mb > 5:
                errors.append(f"Taille totale excessive: {total_mb:.1f}MB")
            elif total_mb > 2:
                recommendations.append(f"Taille importante: {total_mb:.1f}MB")
            
            status = "PASS" if not errors else "WARNING"
            
            return TestResult(
                test_name="Performance Chargement",
                status=status,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Chargement",
                status="FAIL",
                duration=time.time() - start_time,
                details={'error': str(e)},
                errors=[f"Erreur test performance: {e}"],
                recommendations=[]
            )
    
    def _test_accessibility(self) -> TestResult:
        """Test d'accessibilité."""
        start_time = time.time()
        errors = []
        recommendations = []
        
        try:
            html_files = list(Path('.').glob('*.html'))
            details = {
                'aria_labels': 0,
                'alt_texts': 0,
                'semantic_elements': [],
                'accessibility_features': []
            }
            
            for html_file in html_files:
                if html_file.exists():
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    details['aria_labels'] += content.count('aria-label')
                    details['alt_texts'] += content.count('alt=')
                    
                    semantic_elements = ['header', 'nav', 'main', 'section']
                    for element in semantic_elements:
                        if f'<{element}' in content:
                            details['semantic_elements'].append(element)
                    
                    if ':focus' in content:
                        details['accessibility_features'].append('Focus visible')
            
            if details['aria_labels'] == 0:
                errors.append("Aucun aria-label trouvé")
            
            if not details['semantic_elements']:
                errors.append("Aucun élément sémantique HTML5")
            
            status = "PASS" if not errors else "WARNING"
            
            return TestResult(
                test_name="Accessibilité",
                status=status,
                duration=time.time() - start_time,
                details=details,
                errors=errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            return TestResult(
                test_name="Accessibilité",
                status="FAIL",
                duration=time.time() - start_time,
                details={'error': str(e)},
                errors=[f"Erreur test accessibilité: {e}"],
                recommendations=[]
            )
    
    def generate_test_report(self, results: List[TestResult]) -> str:
        """Génère un rapport de tests détaillé."""
        report_lines = [
            "=" * 60,
            "RAPPORT DE TESTS INTERFACE UTILISATEUR MAPAQ",
            "=" * 60,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Nombre de tests: {len(results)}",
            ""
        ]
        
        # Résumé global
        passed = sum(1 for r in results if r.status == 'PASS')
        warnings = sum(1 for r in results if r.status == 'WARNING')
        failed = sum(1 for r in results if r.status == 'FAIL')
        
        report_lines.extend([
            "RÉSUMÉ GLOBAL:",
            f"✅ Tests réussis: {passed}",
            f"⚠️  Tests avec avertissements: {warnings}",
            f"❌ Tests échoués: {failed}",
            f"📊 Taux de réussite: {(passed/(len(results) or 1)*100):.1f}%",
            ""
        ])
        
        # Détails par test
        report_lines.append("DÉTAILS DES TESTS:")
        for result in results:
            status_icon = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌'}.get(result.status, '❓')
            
            report_lines.extend([
                f"{status_icon} {result.test_name}",
                f"   Status: {result.status}",
                f"   Durée: {result.duration:.2f}s",
                ""
            ])
            
            if result.errors:
                report_lines.append("   Erreurs:")
                for error in result.errors:
                    report_lines.append(f"   - {error}")
                report_lines.append("")
            
            if result.recommendations:
                report_lines.append("   Recommandations:")
                for rec in result.recommendations:
                    report_lines.append(f"   - {rec}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def run_complete_interface_tests(self) -> Dict[str, Any]:
        """Exécute la suite complète de tests d'interface."""
        logger.info("🧪 DÉBUT DES TESTS INTERFACE UTILISATEUR MAPAQ")
        logger.info("Heures 113-116: Tests utilisateur interface")
        
        start_time = time.time()
        
        # Tests de validation
        validation_results = self.run_interface_validation_tests()
        
        # Génération du rapport
        report = self.generate_test_report(validation_results)
        
        # Sauvegarde du rapport
        report_file = f"interface_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Statistiques finales
        total_duration = time.time() - start_time
        passed = sum(1 for r in validation_results if r.status == 'PASS')
        total_tests = len(validation_results)
        
        summary = {
            'total_tests': total_tests,
            'passed': passed,
            'failed': sum(1 for r in validation_results if r.status == 'FAIL'),
            'warnings': sum(1 for r in validation_results if r.status == 'WARNING'),
            'success_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'report_file': report_file
        }
        
        logger.info(f"✅ Tests terminés: {passed}/{total_tests} réussis")
        logger.info(f"📄 Rapport sauvegardé: {report_file}")
        
        return summary

def demo_interface_tests():
    """Démonstration des tests d'interface."""
    print("=== DÉMONSTRATION TESTS INTERFACE MAPAQ ===")
    print("Exécution des tests d'interface utilisateur...")
    
    try:
        tester = InterfaceUserTester()
        summary = tester.run_complete_interface_tests()
        
        print(f"\n📊 RÉSULTATS FINAUX:")
        print(f"- Total tests: {summary['total_tests']}")
        print(f"- Réussis: {summary['passed']}")
        print(f"- Échoués: {summary['failed']}")
        print(f"- Avertissements: {summary['warnings']}")
        print(f"- Taux de réussite: {summary['success_rate']:.1f}%")
        print(f"- Durée totale: {summary['total_duration']:.2f}s")
        print(f"- Rapport: {summary['report_file']}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Erreur tests interface: {e}")
        return {}

if __name__ == "__main__":
    demo_interface_tests()
