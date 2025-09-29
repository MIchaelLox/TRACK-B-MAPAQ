
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
        