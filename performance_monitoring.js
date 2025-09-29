
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
        