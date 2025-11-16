@echo off
setlocal enabledelayedexpansion

echo ===============================================================
echo 🚀 Installation du Système de Prédiction Crypto avec IA
echo ===============================================================
echo.

REM Vérifier Node.js
echo 🔍 Vérification de Node.js...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js n'est pas installé!
    echo    Installez Node.js depuis: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo ✅ Node.js détecté
echo.

REM Vérifier Python
echo 🔍 Vérification de Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé!
    echo    Installez Python depuis: https://www.python.org/
    pause
    exit /b 1
)
python --version
echo ✅ Python détecté
echo.

REM Installer les dépendances Node.js
echo 📦 Installation des dépendances Node.js...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Erreur lors de l'installation des dépendances Node.js
    pause
    exit /b 1
)
echo ✅ Dépendances Node.js installées
echo.

REM Créer l'environnement virtuel Python
echo 🐍 Création de l'environnement virtuel Python...
if not exist "venv" (
    python -m venv venv
    echo ✅ Environnement virtuel créé
) else (
    echo ⚠️  Environnement virtuel existe déjà
)
echo.

REM Activer l'environnement virtuel et installer les dépendances
echo 📦 Installation des dépendances Python...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Erreur lors de l'installation des dépendances Python
    pause
    exit /b 1
)
echo ✅ Dépendances Python installées
echo.

REM Collecter les données
echo 📊 Collecte des données historiques Bitcoin...
python collect_data.py
if %errorlevel% neq 0 (
    echo ❌ Erreur lors de la collecte des données
    pause
    exit /b 1
)
echo ✅ Données collectées avec succès
echo.

REM Tester le modèle
echo 🤖 Test du modèle IA...
python ai_model.py
if %errorlevel% neq 0 (
    echo ❌ Erreur lors du test du modèle
    pause
    exit /b 1
)
echo ✅ Modèle IA fonctionnel
echo.

REM Démarrer le serveur
echo ===============================================================
echo ✅ Installation terminée avec succès!
echo ===============================================================
echo.
echo 🚀 Démarrage du serveur...
echo    Le serveur va démarrer sur http://localhost:3000
echo    Testez: http://localhost:3000/predict_price
echo.
echo    Appuyez sur Ctrl+C pour arrêter le serveur
echo ===============================================================
echo.

node index.js
