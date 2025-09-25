@echo off
echo ========================================
echo    OUVERTURE DASHBOARD MAPAQ
echo ========================================
echo.

echo Verification des fichiers...
if exist "mapaq_dashboard.html" (
    echo ✅ Dashboard MAPAQ trouve
) else (
    echo ❌ Dashboard MAPAQ manquant - Generation...
    python frontend_dashboard_mapaq.py
)

if exist "unified_mapaq_track_c_dashboard.html" (
    echo ✅ Dashboard unifie trouve
) else (
    echo ❌ Dashboard unifie manquant - Generation...
    python integration_track_c_components_robuste.py
)

echo.
echo Ouverture des dashboards...
echo.

echo 1. Dashboard MAPAQ principal
start "" "mapaq_dashboard.html"

echo 2. Dashboard unifie MAPAQ/Track-C
start "" "unified_mapaq_track_c_dashboard.html"

echo.
echo ✅ Dashboards ouverts dans votre navigateur par defaut
echo.
echo Pour VS Code avec Live Server:
echo 1. Ouvrez VS Code
echo 2. Installez l'extension "Live Server"
echo 3. Clic droit sur le fichier HTML
echo 4. Selectionnez "Open with Live Server"
echo.
pause
