"""
Module d'Amélioration Responsive pour geo_map.py
Optimisations pour appareils mobiles et tablettes

Auteur: Mouhamed Thiaw
Date: 2025-01-25
Heures: 109-112 (Mercredi - Responsive Design)
Fonctionnalités:
- Interface adaptative mobile/tablette/desktop
- Contrôles tactiles optimisés
- Menu hamburger pour mobile
- Popups redimensionnables
- Performance optimisée
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponsiveMapEnhancer:
    """Améliorateur responsive pour les cartes MAPAQ."""
    
    def __init__(self):
        """Initialise l'améliorateur responsive."""
        self.mobile_breakpoint = 768
        self.tablet_breakpoint = 1024
        self.touch_enabled = True
        
        logger.info("Améliorateur responsive initialisé")
    
    def get_responsive_css(self) -> str:
        """Retourne le CSS responsive avancé."""
        return """
        /* ========== RESPONSIVE DESIGN AVANCÉ ========== */
        
        /* Variables CSS pour cohérence */
        :root {
            --primary-color: #007bff;
            --secondary-color: #6c757d;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            
            --border-radius: 8px;
            --box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
            
            --panel-width-desktop: 300px;
            --panel-width-tablet: 250px;
            --panel-width-mobile: 100%;
        }
        
        /* Base responsive */
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow-x: hidden;
        }
        
        /* Carte principale */
        #map {
            height: 100vh;
            width: 100%;
            position: relative;
            z-index: 1;
        }
        
        /* ========== PANNEAUX ADAPTATIFS ========== */
        
        .map-panel {
            position: absolute;
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            transition: var(--transition);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        /* Panneau de statistiques */
        .stats-panel {
            top: 10px;
            left: 10px;
            width: var(--panel-width-desktop);
            padding: 15px;
        }
        
        /* Panneau de contrôles */
        .map-controls {
            top: 10px;
            right: 10px;
            width: var(--panel-width-desktop);
            padding: 15px;
        }
        
        /* Légende */
        .legend {
            bottom: 20px;
            left: 20px;
            padding: 15px;
            max-width: 250px;
        }
        
        /* ========== DESIGN TABLETTE (768px - 1024px) ========== */
        
        @media (max-width: 1024px) and (min-width: 769px) {
            .stats-panel,
            .map-controls {
                width: var(--panel-width-tablet);
                padding: 12px;
            }
            
            .stats-panel {
                top: 5px;
                left: 5px;
            }
            
            .map-controls {
                top: 5px;
                right: 5px;
            }
            
            .legend {
                bottom: 10px;
                left: 10px;
                padding: 12px;
            }
            
            /* Réduction taille police */
            .map-panel {
                font-size: 14px;
            }
            
            .map-panel h5 {
                font-size: 16px;
                margin-bottom: 8px;
            }
        }
        
        /* ========== DESIGN MOBILE (< 768px) ========== */
        
        @media (max-width: 768px) {
            /* Carte réduite pour laisser place aux contrôles */
            #map {
                height: 60vh;
            }
            
            /* Panneaux en mode mobile */
            .map-panel {
                position: relative;
                width: 100%;
                margin: 5px 0;
                border-radius: 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .stats-panel,
            .map-controls {
                position: relative;
                top: auto;
                left: auto;
                right: auto;
                width: 100%;
                padding: 10px;
                margin: 0;
            }
            
            .legend {
                position: relative;
                bottom: auto;
                left: auto;
                width: 100%;
                margin: 5px 0;
                padding: 10px;
            }
            
            /* Container mobile */
            .mobile-container {
                display: flex;
                flex-direction: column;
                height: 100vh;
            }
            
            .mobile-controls {
                flex: 0 0 auto;
                background: var(--light-color);
                padding: 10px;
                border-top: 1px solid #dee2e6;
                max-height: 40vh;
                overflow-y: auto;
            }
            
            /* Menu hamburger */
            .hamburger-menu {
                display: block;
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 2000;
                background: white;
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                box-shadow: var(--box-shadow);
                cursor: pointer;
                transition: var(--transition);
            }
            
            .hamburger-menu:hover {
                background: var(--light-color);
                transform: scale(1.05);
            }
            
            .hamburger-menu i {
                font-size: 20px;
                color: var(--primary-color);
            }
            
            /* Menu mobile coulissant */
            .mobile-menu {
                position: fixed;
                top: 0;
                right: -100%;
                width: 80%;
                max-width: 300px;
                height: 100vh;
                background: white;
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                transition: right 0.3s ease;
                z-index: 1500;
                overflow-y: auto;
                padding: 70px 20px 20px;
            }
            
            .mobile-menu.active {
                right: 0;
            }
            
            .mobile-menu-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1400;
                opacity: 0;
                visibility: hidden;
                transition: var(--transition);
            }
            
            .mobile-menu-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            
            /* Bouton fermeture menu */
            .close-menu {
                position: absolute;
                top: 15px;
                right: 15px;
                background: none;
                border: none;
                font-size: 24px;
                color: var(--secondary-color);
                cursor: pointer;
            }
            
            /* Réduction tailles mobiles */
            .map-panel h5 {
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .map-panel {
                font-size: 12px;
            }
            
            .btn-sm {
                font-size: 11px;
                padding: 4px 8px;
            }
        }
        
        /* ========== DESIGN TRÈS PETIT MOBILE (< 480px) ========== */
        
        @media (max-width: 480px) {
            #map {
                height: 50vh;
            }
            
            .mobile-menu {
                width: 90%;
            }
            
            .hamburger-menu {
                width: 45px;
                height: 45px;
            }
            
            .hamburger-menu i {
                font-size: 18px;
            }
            
            .map-panel {
                font-size: 11px;
                padding: 8px;
            }
            
            .legend-item {
                margin: 3px 0;
            }
            
            .legend-color {
                width: 15px;
                height: 15px;
            }
        }
        
        /* ========== POPUPS RESPONSIVES ========== */
        
        .leaflet-popup-content-wrapper {
            border-radius: var(--border-radius);
        }
        
        @media (max-width: 768px) {
            .leaflet-popup-content-wrapper {
                max-width: 250px !important;
                min-width: 200px;
            }
            
            .restaurant-popup {
                font-size: 12px;
            }
            
            .restaurant-popup h3 {
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .popup-actions button {
                font-size: 10px;
                padding: 3px 6px;
                margin: 1px;
            }
        }
        
        /* ========== OPTIMISATIONS TACTILES ========== */
        
        @media (hover: none) and (pointer: coarse) {
            /* Appareils tactiles */
            .btn, .form-control, .form-select {
                min-height: 44px; /* Taille minimum tactile */
            }
            
            .hamburger-menu {
                min-width: 44px;
                min-height: 44px;
            }
            
            /* Espacement tactile */
            .form-check {
                margin: 8px 0;
            }
            
            .form-check-input {
                width: 20px;
                height: 20px;
            }
            
            /* Marqueurs plus grands sur tactile */
            .custom-marker div {
                width: 35px !important;
                height: 35px !important;
            }
        }
        
        /* ========== ANIMATIONS ET TRANSITIONS ========== */
        
        .map-panel {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Hover effects pour desktop */
        @media (hover: hover) and (pointer: fine) {
            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            
            .map-panel:hover {
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            }
        }
        
        /* ========== ACCESSIBILITÉ ========== */
        
        /* Focus visible pour navigation clavier */
        .btn:focus,
        .form-control:focus,
        .form-select:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        /* Réduction mouvement pour utilisateurs sensibles */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Mode sombre */
        @media (prefers-color-scheme: dark) {
            :root {
                --light-color: #2d3748;
                --dark-color: #f7fafc;
            }
            
            .map-panel {
                background: #2d3748;
                color: #f7fafc;
            }
            
            .mobile-menu {
                background: #2d3748;
                color: #f7fafc;
            }
        }
        
        /* ========== UTILITAIRES RESPONSIVE ========== */
        
        .d-mobile-none {
            display: block;
        }
        
        .d-mobile-block {
            display: none;
        }
        
        @media (max-width: 768px) {
            .d-mobile-none {
                display: none;
            }
            
            .d-mobile-block {
                display: block;
            }
        }
        
        .text-mobile-center {
            text-align: left;
        }
        
        @media (max-width: 768px) {
            .text-mobile-center {
                text-align: center;
            }
        }
        """
    
    def get_responsive_javascript(self) -> str:
        """Retourne le JavaScript pour les fonctionnalités responsives."""
        return """
        // ========== JAVASCRIPT RESPONSIVE ========== 
        
        // Variables globales responsive
        let isMobile = window.innerWidth <= 768;
        let isTablet = window.innerWidth <= 1024 && window.innerWidth > 768;
        let isTouch = 'ontouchstart' in window;
        
        // Détection du type d'appareil
        function detectDevice() {
            const width = window.innerWidth;
            isMobile = width <= 768;
            isTablet = width <= 1024 && width > 768;
            
            // Mise à jour des classes CSS
            document.body.classList.toggle('is-mobile', isMobile);
            document.body.classList.toggle('is-tablet', isTablet);
            document.body.classList.toggle('is-desktop', !isMobile && !isTablet);
            document.body.classList.toggle('is-touch', isTouch);
        }
        
        // Initialisation responsive
        function initResponsive() {
            detectDevice();
            
            if (isMobile) {
                initMobileInterface();
            }
            
            // Écouteur redimensionnement
            let resizeTimer;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    const wasMobile = isMobile;
                    detectDevice();
                    
                    // Réinitialisation si changement mobile/desktop
                    if (wasMobile !== isMobile) {
                        if (isMobile) {
                            initMobileInterface();
                        } else {
                            initDesktopInterface();
                        }
                        
                        // Redimensionnement carte
                        setTimeout(() => {
                            map.invalidateSize();
                        }, 300);
                    }
                }, 250);
            });
        }
        
        // Interface mobile
        function initMobileInterface() {
            // Création du menu hamburger
            createHamburgerMenu();
            
            // Réorganisation des panneaux
            reorganizePanelsForMobile();
            
            // Optimisation des popups
            optimizePopupsForMobile();
            
            // Gestion tactile
            enableTouchOptimizations();
        }
        
        // Interface desktop
        function initDesktopInterface() {
            // Suppression éléments mobiles
            removeHamburgerMenu();
            
            // Restauration panneaux desktop
            restoreDesktopPanels();
        }
        
        // Création menu hamburger
        function createHamburgerMenu() {
            // Vérification existence
            if (document.querySelector('.hamburger-menu')) return;
            
            // Bouton hamburger
            const hamburger = document.createElement('button');
            hamburger.className = 'hamburger-menu';
            hamburger.innerHTML = '<i class="fas fa-bars"></i>';
            hamburger.setAttribute('aria-label', 'Menu');
            
            // Menu coulissant
            const mobileMenu = document.createElement('div');
            mobileMenu.className = 'mobile-menu';
            mobileMenu.innerHTML = `
                <button class="close-menu" aria-label="Fermer menu">
                    <i class="fas fa-times"></i>
                </button>
                <div id="mobile-menu-content"></div>
            `;
            
            // Overlay
            const overlay = document.createElement('div');
            overlay.className = 'mobile-menu-overlay';
            
            // Ajout au DOM
            document.body.appendChild(hamburger);
            document.body.appendChild(mobileMenu);
            document.body.appendChild(overlay);
            
            // Déplacement du contenu
            const statsPanel = document.querySelector('.stats-panel');
            const controlsPanel = document.querySelector('.map-controls');
            const legend = document.querySelector('.legend');
            
            const menuContent = document.getElementById('mobile-menu-content');
            if (statsPanel) menuContent.appendChild(statsPanel.cloneNode(true));
            if (controlsPanel) menuContent.appendChild(controlsPanel.cloneNode(true));
            if (legend) menuContent.appendChild(legend.cloneNode(true));
            
            // Événements
            hamburger.addEventListener('click', toggleMobileMenu);
            overlay.addEventListener('click', closeMobileMenu);
            mobileMenu.querySelector('.close-menu').addEventListener('click', closeMobileMenu);
            
            // Réattachement des événements
            reattachEventListeners(menuContent);
        }
        
        // Toggle menu mobile
        function toggleMobileMenu() {
            const menu = document.querySelector('.mobile-menu');
            const overlay = document.querySelector('.mobile-menu-overlay');
            
            menu.classList.toggle('active');
            overlay.classList.toggle('active');
            
            // Prévention scroll body
            document.body.style.overflow = menu.classList.contains('active') ? 'hidden' : '';
        }
        
        // Fermeture menu mobile
        function closeMobileMenu() {
            const menu = document.querySelector('.mobile-menu');
            const overlay = document.querySelector('.mobile-menu-overlay');
            
            menu.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        // Suppression menu hamburger
        function removeHamburgerMenu() {
            const elements = ['.hamburger-menu', '.mobile-menu', '.mobile-menu-overlay'];
            elements.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) element.remove();
            });
        }
        
        // Réorganisation panneaux mobile
        function reorganizePanelsForMobile() {
            const panels = document.querySelectorAll('.map-panel');
            panels.forEach(panel => {
                panel.style.position = 'relative';
                panel.style.top = 'auto';
                panel.style.left = 'auto';
                panel.style.right = 'auto';
                panel.style.bottom = 'auto';
            });
        }
        
        // Restauration panneaux desktop
        function restoreDesktopPanels() {
            const statsPanel = document.querySelector('.stats-panel');
            const controlsPanel = document.querySelector('.map-controls');
            const legend = document.querySelector('.legend');
            
            if (statsPanel) {
                statsPanel.style.position = 'absolute';
                statsPanel.style.top = '10px';
                statsPanel.style.left = '10px';
            }
            
            if (controlsPanel) {
                controlsPanel.style.position = 'absolute';
                controlsPanel.style.top = '10px';
                controlsPanel.style.right = '10px';
            }
            
            if (legend) {
                legend.style.position = 'absolute';
                legend.style.bottom = '20px';
                legend.style.left = '20px';
            }
        }
        
        // Optimisation popups mobile
        function optimizePopupsForMobile() {
            // Réduction taille popups
            const style = document.createElement('style');
            style.textContent = `
                @media (max-width: 768px) {
                    .leaflet-popup-content-wrapper {
                        max-width: 250px !important;
                        font-size: 12px;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Optimisations tactiles
        function enableTouchOptimizations() {
            if (!isTouch) return;
            
            // Désactivation hover sur tactile
            const style = document.createElement('style');
            style.textContent = `
                @media (hover: none) {
                    .btn:hover {
                        transform: none;
                        box-shadow: initial;
                    }
                }
            `;
            document.head.appendChild(style);
            
            // Gestion double-tap
            let lastTap = 0;
            document.addEventListener('touchend', function(e) {
                const currentTime = new Date().getTime();
                const tapLength = currentTime - lastTap;
                
                if (tapLength < 500 && tapLength > 0) {
                    // Double tap détecté
                    e.preventDefault();
                    
                    // Zoom sur la carte
                    if (e.target.closest('#map')) {
                        map.zoomIn();
                    }
                }
                lastTap = currentTime;
            });
        }
        
        // Réattachement événements
        function reattachEventListeners(container) {
            // Marqueurs
            const showMarkersCheckbox = container.querySelector('#show-markers');
            if (showMarkersCheckbox) {
                showMarkersCheckbox.addEventListener('change', function(e) {
                    if (e.target.checked) {
                        map.addLayer(markersGroup);
                    } else {
                        map.removeLayer(markersGroup);
                    }
                });
            }
            
            // Clusters
            const showClustersCheckbox = container.querySelector('#show-clusters');
            if (showClustersCheckbox) {
                showClustersCheckbox.addEventListener('change', function(e) {
                    if (e.target.checked) {
                        markersGroup.options.disableClusteringAtZoom = null;
                    } else {
                        markersGroup.options.disableClusteringAtZoom = 1;
                    }
                    markersGroup.refreshClusters();
                });
            }
            
            // Heatmap
            const showHeatmapCheckbox = container.querySelector('#show-heatmap');
            if (showHeatmapCheckbox) {
                showHeatmapCheckbox.addEventListener('change', function(e) {
                    if (e.target.checked) {
                        map.addLayer(heatmapGroup);
                    } else {
                        map.removeLayer(heatmapGroup);
                    }
                });
            }
            
            // Filtre risque
            const riskFilter = container.querySelector('#risk-filter');
            if (riskFilter) {
                riskFilter.addEventListener('change', function(e) {
                    currentFilter = e.target.value;
                    filterMarkers();
                });
            }
        }
        
        // Gestion orientation
        function handleOrientationChange() {
            setTimeout(() => {
                detectDevice();
                map.invalidateSize();
                
                // Réajustement interface
                if (isMobile) {
                    // Fermeture menu si ouvert
                    closeMobileMenu();
                }
            }, 500);
        }
        
        // Écouteur orientation
        window.addEventListener('orientationchange', handleOrientationChange);
        
        // Performance - Debounce scroll
        let scrollTimer;
        function debounceScroll(func, wait) {
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(scrollTimer);
                    func(...args);
                };
                clearTimeout(scrollTimer);
                scrollTimer = setTimeout(later, wait);
            };
        }
        
        // Optimisation performance mobile
        function optimizePerformance() {
            if (isMobile) {
                // Réduction qualité rendu sur mobile
                map.options.preferCanvas = true;
                
                // Limitation nombre marqueurs visibles
                if (markersData.length > 50) {
                    console.log('Optimisation mobile: limitation marqueurs');
                }
            }
        }
        
        // Initialisation au chargement
        document.addEventListener('DOMContentLoaded', function() {
            initResponsive();
            optimizePerformance();
        });
        """
    
    def enhance_map_template(self, original_template: str) -> str:
        """Améliore le template existant avec les fonctionnalités responsives."""
        
        # Injection du CSS responsive
        responsive_css = self.get_responsive_css()
        enhanced_template = original_template.replace(
            '@media (max-width: 768px) { .map-controls, .stats-panel { position: relative; width: 100%; margin: 10px 0; } #map { height: 70vh; } }',
            responsive_css
        )
        
        # Injection du JavaScript responsive
        responsive_js = self.get_responsive_javascript()
        enhanced_template = enhanced_template.replace(
            '    </script>',
            f'        \n        {responsive_js}\n    </script>'
        )
        
        return enhanced_template

def demo_responsive_enhancements():
    """Démonstration des améliorations responsives."""
    print("=== DÉMONSTRATION AMÉLIORATIONS RESPONSIVE ===")
    print("Génération d'une carte avec design responsive avancé...")
    
    try:
        # Import du module principal
        from geo_map import GeoMapGenerator
        
        # Création du générateur
        generator = GeoMapGenerator()
        generator._generate_demo_data()
        
        # Création de l'améliorateur responsive
        enhancer = ResponsiveMapEnhancer()
        
        # Génération du template de base
        base_template = generator._get_leaflet_template()
        
        # Amélioration avec responsive
        enhanced_template = enhancer.enhance_map_template(base_template)
        
        # Sauvegarde de la carte responsive
        output_file = "mapaq_responsive_map.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Remplacement des données
            markers_js = generator._generate_markers_javascript()
            clusters_js = generator._generate_clusters_javascript()
            heatmap_js = generator._generate_heatmap_javascript()
            
            enhanced_content = enhanced_template.replace('{{MARKERS_DATA}}', markers_js)
            enhanced_content = enhanced_content.replace('{{CLUSTERS_DATA}}', clusters_js)
            enhanced_content = enhanced_content.replace('{{HEATMAP_DATA}}', heatmap_js)
            enhanced_content = enhanced_content.replace('{{CENTER_LAT}}', str(generator.config.center_lat))
            enhanced_content = enhanced_content.replace('{{CENTER_LNG}}', str(generator.config.center_lng))
            enhanced_content = enhanced_content.replace('{{ZOOM_LEVEL}}', str(generator.config.zoom_level))
            
            f.write(enhanced_content)
        
        print(f"✅ Carte responsive générée: {Path(output_file).absolute()}")
        print("\n🎨 AMÉLIORATIONS RESPONSIVES AJOUTÉES:")
        print("- ✅ Interface adaptative mobile/tablette/desktop")
        print("- ✅ Menu hamburger pour navigation mobile")
        print("- ✅ Contrôles tactiles optimisés")
        print("- ✅ Popups redimensionnables")
        print("- ✅ Animations et transitions fluides")
        print("- ✅ Mode sombre automatique")
        print("- ✅ Accessibilité améliorée")
        print("- ✅ Performance optimisée")
        
        print(f"\n📱 BREAKPOINTS RESPONSIVE:")
        print("- Desktop: > 1024px")
        print("- Tablette: 769px - 1024px") 
        print("- Mobile: ≤ 768px")
        print("- Petit mobile: ≤ 480px")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Erreur démonstration responsive: {e}")
        return ""

if __name__ == "__main__":
    demo_responsive_enhancements()
