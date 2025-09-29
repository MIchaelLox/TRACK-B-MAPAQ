"""
Optimisateur de Performance Interface MAPAQ - performance_optimizer.py
Module d'optimisation des performances pour l'interface utilisateur

Auteur: Mouhamed Thiaw
Date: 2025-01-27
Heures: 117-120 (Vendredi - Optimisation performance)
"""

import sys
import os
import time
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Métrique de performance."""
    name: str
    value: float
    unit: str
    threshold: float
    status: str  # 'good', 'warning', 'critical'
    recommendations: List[str]

@dataclass
class OptimizationResult:
    """Résultat d'optimisation."""
    file_path: str
    original_size: int
    optimized_size: int
    compression_ratio: float
    optimization_type: str

class PerformanceOptimizer:
    """Optimisateur de performance pour l'interface MAPAQ."""
    
    def __init__(self):
        """Initialise l'optimisateur de performance."""
        self.optimization_results = []
        self.performance_metrics = []
        
        # Seuils de performance
        self.performance_thresholds = {
            'page_load_time': 3.0,  # secondes
            'file_size_html': 100 * 1024,  # 100KB
            'file_size_css': 50 * 1024,   # 50KB
            'file_size_js': 200 * 1024    # 200KB
        }
        
        logger.info("Optimisateur de performance MAPAQ initialisé")
    
    def optimize_html_files(self) -> List[OptimizationResult]:
        """Optimise les fichiers HTML."""
        logger.info("=== OPTIMISATION FICHIERS HTML ===")
        results = []
        
        html_files = list(Path('.').glob('*.html'))
        
        for html_file in html_files:
            if html_file.exists():
                result = self._optimize_html_file(html_file)
                if result:
                    results.append(result)
        
        return results
    
    def _optimize_html_file(self, file_path: Path) -> Optional[OptimizationResult]:
        """Optimise un fichier HTML spécifique."""
        try:
            # Lecture du fichier original
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            original_size = len(original_content.encode('utf-8'))
            
            # Optimisations
            optimized_content = original_content
            
            # 1. Suppression des commentaires HTML
            optimized_content = re.sub(r'<!--(?!\[if).*?-->', '', optimized_content, flags=re.DOTALL)
            
            # 2. Suppression des espaces multiples
            optimized_content = re.sub(r'\s+', ' ', optimized_content)
            
            # 3. Suppression des espaces autour des balises
            optimized_content = re.sub(r'>\s+<', '><', optimized_content)
            
            # 4. Minification CSS inline
            optimized_content = self._minify_inline_css(optimized_content)
            
            # 5. Minification JavaScript inline
            optimized_content = self._minify_inline_js(optimized_content)
            
            # Calcul des métriques
            optimized_size = len(optimized_content.encode('utf-8'))
            compression_ratio = (original_size - optimized_size) / original_size * 100
            
            # Sauvegarde du fichier optimisé
            optimized_path = file_path.with_suffix('.optimized.html')
            with open(optimized_path, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            
            logger.info(f"✅ {file_path}: {original_size//1024}KB → {optimized_size//1024}KB ({compression_ratio:.1f}% réduction)")
            
            return OptimizationResult(
                file_path=str(file_path),
                original_size=original_size,
                optimized_size=optimized_size,
                compression_ratio=compression_ratio,
                optimization_type="HTML Minification"
            )
            
        except Exception as e:
            logger.error(f"Erreur optimisation {file_path}: {e}")
            return None
    
    def _minify_inline_css(self, content: str) -> str:
        """Minifie le CSS inline."""
        def minify_css_block(match):
            css_content = match.group(1)
            
            # Suppression des commentaires CSS
            css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
            
            # Suppression des espaces multiples
            css_content = re.sub(r'\s+', ' ', css_content)
            
            # Suppression des espaces autour des caractères spéciaux
            css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
            
            return f'<style>{css_content.strip()}</style>'
        
        return re.sub(r'<style[^>]*>(.*?)</style>', minify_css_block, content, flags=re.DOTALL | re.IGNORECASE)
    
    def _minify_inline_js(self, content: str) -> str:
        """Minifie le JavaScript inline."""
        def minify_js_block(match):
            js_content = match.group(1)
            
            # Suppression des commentaires JavaScript simples
            js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
            
            # Suppression des commentaires multi-lignes
            js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
            
            # Suppression des espaces multiples
            js_content = re.sub(r'\s+', ' ', js_content)
            
            return f'<script>{js_content.strip()}</script>'
        
        return re.sub(r'<script[^>]*>(.*?)</script>', minify_js_block, content, flags=re.DOTALL | re.IGNORECASE)
    
    def create_lazy_loading_components(self) -> str:
        """Crée des composants avec lazy loading."""
        logger.info("=== CRÉATION COMPOSANTS LAZY LOADING ===")
        
        lazy_loading_js = """
// Lazy Loading Components MAPAQ
class LazyLoader {
    constructor() {
        this.observer = null;
        this.init();
    }
    
    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadComponent(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            
            this.observeElements();
        } else {
            this.loadAllComponents();
        }
    }
    
    observeElements() {
        const lazyElements = document.querySelectorAll('[data-lazy]');
        lazyElements.forEach(el => this.observer.observe(el));
    }
    
    loadComponent(element) {
        const componentType = element.dataset.lazy;
        
        switch(componentType) {
            case 'map':
                this.loadMap(element);
                break;
            case 'chart':
                this.loadChart(element);
                break;
            case 'table':
                this.loadTable(element);
                break;
            default:
                this.loadGeneric(element);
        }
    }
    
    loadMap(element) {
        element.innerHTML = '<div class="loading">Chargement de la carte...</div>';
        // Chargement différé de la carte
    }
    
    loadChart(element) {
        element.innerHTML = '<div class="loading">Chargement du graphique...</div>';
        // Chargement différé des graphiques
    }
    
    loadTable(element) {
        element.innerHTML = '<div class="loading">Chargement du tableau...</div>';
        // Chargement différé des tableaux
    }
    
    loadGeneric(element) {
        const src = element.dataset.src;
        if (src) {
            fetch(src)
                .then(response => response.text())
                .then(html => {
                    element.innerHTML = html;
                });
        }
    }
    
    loadAllComponents() {
        const lazyElements = document.querySelectorAll('[data-lazy]');
        lazyElements.forEach(el => this.loadComponent(el));
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    new LazyLoader();
});

// Cache intelligent pour les requêtes API
class APICache {
    constructor(maxAge = 300000) {
        this.cache = new Map();
        this.maxAge = maxAge;
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() - item.timestamp > this.maxAge) {
            this.cache.delete(key);
            return null;
        }
        
        return item.data;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
}

window.apiCache = new APICache();
        """
        
        # Sauvegarde du script de lazy loading
        lazy_file = Path('lazy_loading_components.js')
        with open(lazy_file, 'w', encoding='utf-8') as f:
            f.write(lazy_loading_js)
        
        logger.info(f"✅ Composants lazy loading créés: {lazy_file}")
        return str(lazy_file)
    
    def create_performance_monitoring(self) -> str:
        """Crée un système de monitoring des performances."""
        logger.info("=== CRÉATION MONITORING PERFORMANCE ===")
        
        monitoring_js = """
// Performance Monitoring MAPAQ
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        this.measurePageLoad();
        this.measureUserInteractions();
        this.setupPerformanceObserver();
    }
    
    measurePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            
            this.metrics.pageLoad = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                totalTime: navigation.loadEventEnd - navigation.fetchStart
            };
            
            this.reportMetrics();
        });
    }
    
    measureUserInteractions() {
        document.addEventListener('click', (event) => {
            const startTime = performance.now();
            
            requestAnimationFrame(() => {
                const responseTime = performance.now() - startTime;
                this.recordInteraction('click', responseTime, event.target);
            });
        });
    }
    
    setupPerformanceObserver() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'largest-contentful-paint') {
                        this.metrics.largestContentfulPaint = entry.startTime;
                    }
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }
    }
    
    recordInteraction(type, responseTime, element) {
        if (!this.metrics.interactions) {
            this.metrics.interactions = [];
        }
        
        this.metrics.interactions.push({
            type: type,
            responseTime: responseTime,
            element: element.tagName,
            timestamp: Date.now()
        });
    }
    
    reportMetrics() {
        if (Math.random() < 0.1) { // 10% des utilisateurs
            fetch('/api/v1/performance-metrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    metrics: this.metrics,
                    timestamp: Date.now(),
                    url: window.location.href
                })
            }).catch(error => {
                console.warn('Erreur envoi métriques:', error);
            });
        }
    }
    
    getMetrics() {
        return this.metrics;
    }
    
    displayMetrics() {
        console.group('📊 Métriques de Performance MAPAQ');
        console.log('Page Load:', this.metrics.pageLoad);
        console.log('Largest Contentful Paint:', this.metrics.largestContentfulPaint);
        console.log('Interactions:', this.metrics.interactions?.length || 0);
        console.groupEnd();
    }
}

const performanceMonitor = new PerformanceMonitor();

if (window.location.search.includes('debug=performance')) {
    setTimeout(() => {
        performanceMonitor.displayMetrics();
    }, 5000);
}
        """
        
        # Sauvegarde du script de monitoring
        monitoring_file = Path('performance_monitoring.js')
        with open(monitoring_file, 'w', encoding='utf-8') as f:
            f.write(monitoring_js)
        
        logger.info(f"✅ Monitoring performance créé: {monitoring_file}")
        return str(monitoring_file)
    
    def analyze_performance_metrics(self) -> List[PerformanceMetric]:
        """Analyse les métriques de performance actuelles."""
        logger.info("=== ANALYSE MÉTRIQUES PERFORMANCE ===")
        metrics = []
        
        # Analyse des tailles de fichiers
        html_files = list(Path('.').glob('*.html'))
        
        for html_file in html_files:
            if html_file.exists():
                size = html_file.stat().st_size
                
                status = 'good'
                recommendations = []
                
                if size > self.performance_thresholds['file_size_html']:
                    status = 'critical'
                    recommendations.extend(['Minification HTML', 'Compression gzip'])
                elif size > self.performance_thresholds['file_size_html'] * 0.7:
                    status = 'warning'
                    recommendations.append('Optimisation HTML possible')
                
                metrics.append(PerformanceMetric(
                    name=f"Taille fichier {html_file.name}",
                    value=size / 1024,
                    unit="KB",
                    threshold=self.performance_thresholds['file_size_html'] / 1024,
                    status=status,
                    recommendations=recommendations
                ))
        
        return metrics
    
    def generate_optimization_report(self) -> str:
        """Génère un rapport d'optimisation complet."""
        logger.info("=== GÉNÉRATION RAPPORT OPTIMISATION ===")
        
        # Exécution des optimisations
        html_optimizations = self.optimize_html_files()
        lazy_loading_file = self.create_lazy_loading_components()
        monitoring_file = self.create_performance_monitoring()
        performance_metrics = self.analyze_performance_metrics()
        
        # Génération du rapport
        report_lines = [
            "=" * 60,
            "RAPPORT D'OPTIMISATION PERFORMANCE MAPAQ",
            "=" * 60,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Heures: 117-120 (Optimisation performance)",
            ""
        ]
        
        # Résumé des optimisations HTML
        if html_optimizations:
            total_original = sum(opt.original_size for opt in html_optimizations)
            total_optimized = sum(opt.optimized_size for opt in html_optimizations)
            total_savings = total_original - total_optimized
            avg_compression = (total_savings / total_original * 100) if total_original > 0 else 0
            
            report_lines.extend([
                "📄 OPTIMISATIONS HTML:",
                f"- Fichiers optimisés: {len(html_optimizations)}",
                f"- Taille originale: {total_original//1024} KB",
                f"- Taille optimisée: {total_optimized//1024} KB",
                f"- Économies: {total_savings//1024} KB ({avg_compression:.1f}%)",
                ""
            ])
        
        # Composants créés
        report_lines.extend([
            "🚀 COMPOSANTS CRÉÉS:",
            f"- Lazy loading: {lazy_loading_file}",
            f"- Monitoring: {monitoring_file}",
            ""
        ])
        
        # Métriques de performance
        report_lines.extend([
            "📊 MÉTRIQUES DE PERFORMANCE:",
            "-" * 30
        ])
        
        for metric in performance_metrics:
            status_icon = {'good': '✅', 'warning': '⚠️', 'critical': '❌'}.get(metric.status, '❓')
            
            report_lines.extend([
                f"{status_icon} {metric.name}:",
                f"   Valeur: {metric.value:.1f} {metric.unit}",
                f"   Status: {metric.status.upper()}",
                ""
            ])
        
        # Recommandations globales
        report_lines.extend([
            "🎯 RECOMMANDATIONS GLOBALES:",
            "• Activer la compression gzip sur le serveur",
            "• Utiliser un CDN pour les ressources statiques",
            "• Implémenter le cache navigateur",
            "• Optimiser les images (WebP, AVIF)",
            "• Utiliser le lazy loading pour composants lourds",
            "• Monitorer les performances en continu",
            ""
        ])
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def run_complete_optimization(self) -> Dict[str, Any]:
        """Exécute l'optimisation complète des performances."""
        logger.info("🚀 DÉBUT OPTIMISATION PERFORMANCE MAPAQ")
        logger.info("Heures 117-120: Optimisation performance")
        
        start_time = time.time()
        
        # Génération du rapport complet
        report = self.generate_optimization_report()
        
        # Sauvegarde du rapport
        report_file = f"performance_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Statistiques finales
        total_duration = time.time() - start_time
        
        summary = {
            'html_files_optimized': len(list(Path('.').glob('*.optimized.html'))),
            'lazy_loading_created': os.path.exists('lazy_loading_components.js'),
            'monitoring_created': os.path.exists('performance_monitoring.js'),
            'total_duration': total_duration,
            'report_file': report_file
        }
        
        logger.info(f"✅ Optimisation terminée en {total_duration:.2f}s")
        logger.info(f"📄 Rapport sauvegardé: {report_file}")
        
        return summary

def demo_performance_optimization():
    """Démonstration de l'optimisation des performances."""
    print("=== DÉMONSTRATION OPTIMISATION PERFORMANCE MAPAQ ===")
    print("Exécution de l'optimisation des performances...")
    
    try:
        optimizer = PerformanceOptimizer()
        summary = optimizer.run_complete_optimization()
        
        print(f"\n🎯 RÉSULTATS OPTIMISATION:")
        print(f"- Fichiers HTML optimisés: {summary['html_files_optimized']}")
        print(f"- Lazy loading créé: {'✅' if summary['lazy_loading_created'] else '❌'}")
        print(f"- Monitoring créé: {'✅' if summary['monitoring_created'] else '❌'}")
        print(f"- Durée totale: {summary['total_duration']:.2f}s")
        print(f"- Rapport: {summary['report_file']}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Erreur optimisation performance: {e}")
        return {}

if __name__ == "__main__":
    demo_performance_optimization()
