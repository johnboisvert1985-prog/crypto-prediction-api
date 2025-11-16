#!/bin/bash

# Script de démarrage rapide pour le système de prédiction crypto
# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Installation du Système de Prédiction Crypto avec IA${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Vérifier Node.js
echo -e "${YELLOW}🔍 Vérification de Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js n'est pas installé!${NC}"
    echo -e "${YELLOW}   Installez Node.js depuis: https://nodejs.org/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node --version) détecté${NC}"

# Vérifier Python
echo -e "${YELLOW}🔍 Vérification de Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé!${NC}"
    echo -e "${YELLOW}   Installez Python depuis: https://www.python.org/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version) détecté${NC}"
echo ""

# Installer les dépendances Node.js
echo -e "${BLUE}📦 Installation des dépendances Node.js...${NC}"
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de l'installation des dépendances Node.js${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dépendances Node.js installées${NC}"
echo ""

# Créer l'environnement virtuel Python
echo -e "${BLUE}🐍 Création de l'environnement virtuel Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
else
    echo -e "${YELLOW}⚠️  Environnement virtuel existe déjà${NC}"
fi

# Activer l'environnement virtuel et installer les dépendances
echo -e "${BLUE}📦 Installation des dépendances Python...${NC}"
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de l'installation des dépendances Python${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dépendances Python installées${NC}"
echo ""

# Collecter les données
echo -e "${BLUE}📊 Collecte des données historiques Bitcoin...${NC}"
python3 collect_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de la collecte des données${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Données collectées avec succès${NC}"
echo ""

# Tester le modèle
echo -e "${BLUE}🤖 Test du modèle IA...${NC}"
python3 ai_model.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors du test du modèle${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Modèle IA fonctionnel${NC}"
echo ""

# Démarrer le serveur
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Installation terminée avec succès!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}🚀 Démarrage du serveur...${NC}"
echo -e "${YELLOW}   Le serveur va démarrer sur http://localhost:3000${NC}"
echo -e "${YELLOW}   Testez: http://localhost:3000/predict_price${NC}"
echo ""
echo -e "${YELLOW}   Appuyez sur Ctrl+C pour arrêter le serveur${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Démarrer le serveur
node index.js
