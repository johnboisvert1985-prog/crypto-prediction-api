# 🚀 Système de Prédiction de Prix Crypto avec IA

Un système complet de prédiction de prix de cryptomonnaies utilisant l'intelligence artificielle et l'API CoinGecko. Ce projet combine Python pour le machine learning et Node.js pour l'API REST.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Architecture](#-architecture)
- [API Endpoints](#-api-endpoints)
- [Comment ça fonctionne](#-comment-ça-fonctionne)
- [Améliorer le modèle](#-améliorer-le-modèle)

## ✨ Fonctionnalités

- 📊 **Collecte automatique de données** historiques via l'API CoinGecko
- 🤖 **Modèle IA de prédiction** utilisant la régression linéaire (scikit-learn)
- 🔮 **Prédictions en temps réel** avec signaux de trading (ACHETER/VENDRE/HOLD)
- 🌐 **API REST complète** avec Express.js
- 📈 **Métriques de performance** du modèle (MSE, R² Score)
- 💹 **Signaux de trading automatiques** basés sur les prédictions

## 🔧 Prérequis

### Logiciels requis

- **Node.js** v16+ et npm
- **Python** 3.7+
- **pip** (gestionnaire de paquets Python)

### Compte CoinGecko (optionnel)

Le plan gratuit de CoinGecko est suffisant pour ce projet:
- 30 appels/minute
- 10,000 appels/mois
- Inscrivez-vous sur: https://www.coingecko.com/en/api/pricing

## 📦 Installation

### 1. Cloner/Télécharger le projet

```bash
# Si vous utilisez Git
git clone <votre-repo>
cd crypto-price-prediction-ai

# Ou simplement téléchargez et extrayez les fichiers
```

### 2. Installer les dépendances Node.js

```bash
npm install
```

### 3. Installer les dépendances Python

```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 4. Configuration (optionnel)

Copiez le fichier de configuration:
```bash
cp .env.example .env
```

Modifiez `.env` si nécessaire (le port par défaut est 3000).

## 🚀 Utilisation

### Étape 1: Collecter les données historiques

```bash
# Avec npm script
npm run collect

# Ou directement avec Python
python3 collect_data.py
```

Cela va:
- ✅ Récupérer 30 jours de données historiques Bitcoin
- ✅ Créer un fichier `market_data.csv`
- ✅ Afficher un résumé des données collectées

### Étape 2: Tester le modèle IA (optionnel)

```bash
# Avec npm script
npm run train

# Ou directement avec Python
python3 ai_model.py
```

Cela va:
- ✅ Entraîner le modèle de régression linéaire
- ✅ Afficher les métriques de performance
- ✅ Faire une prédiction de test

### Étape 3: Démarrer le serveur API

```bash
# Mode production
npm start

# Mode développement (avec auto-reload)
npm run dev
```

Le serveur démarre sur `http://localhost:3000`

### Étape 4: Tester l'API

Ouvrez votre navigateur ou utilisez curl:

```bash
# Page d'accueil
curl http://localhost:3000/

# Obtenir une prédiction
curl http://localhost:3000/predict_price

# Vérifier la santé du serveur
curl http://localhost:3000/health

# Collecter de nouvelles données via l'API
curl -X POST http://localhost:3000/collect_data
```

## 🏗️ Architecture

```
📁 crypto-price-prediction-ai/
│
├── 📄 collect_data.py       # Script de collecte de données
├── 📄 ai_model.py           # Modèle IA de prédiction
├── 📄 index.js              # Serveur Express API
│
├── 📄 package.json          # Dépendances Node.js
├── 📄 requirements.txt      # Dépendances Python
├── 📄 .env.example          # Configuration exemple
├── 📄 .gitignore           # Fichiers à ignorer
│
├── 📄 market_data.csv       # Données historiques (généré)
└── 📄 README.md            # Cette documentation
```

## 🌐 API Endpoints

### GET `/`
Page d'accueil avec la liste des endpoints disponibles.

**Réponse:**
```json
{
  "message": "🚀 API de Prédiction Crypto avec IA",
  "endpoints": {
    "/predict_price": "GET - Obtenir la prédiction de prix Bitcoin",
    "/health": "GET - Vérifier l'état du serveur",
    "/collect_data": "POST - Collecter les données historiques"
  }
}
```

### GET `/predict_price`
Obtient la prédiction de prix Bitcoin en temps réel.

**Réponse:**
```json
{
  "timestamp": "2025-11-16T10:30:00.000Z",
  "coin": "Bitcoin (BTC)",
  "latest_price": {
    "value": 91234.56,
    "currency": "USD"
  },
  "predicted_price": {
    "value": 92100.00,
    "currency": "USD"
  },
  "prediction": {
    "change_percent": 0.95,
    "change_usd": 865.44
  },
  "trading_signal": {
    "action": "HOLD",
    "emoji": "🟡",
    "description": "Le modèle prédit un mouvement < 1%"
  },
  "market_data": {
    "volume_24h": 35678901234,
    "price_change_24h_percent": 2.34,
    "volume_change_percent": -5.67
  },
  "model_metrics": {
    "mse": 1234567.89,
    "r2_score": 0.8567
  }
}
```

### GET `/health`
Vérifie l'état du serveur.

**Réponse:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-16T10:30:00.000Z"
}
```

### POST `/collect_data`
Lance la collecte de nouvelles données historiques.

**Réponse:**
```json
{
  "success": true,
  "message": "Données collectées avec succès",
  "output": "..."
}
```

## 🔍 Comment ça fonctionne

### 1. Collecte de données

Le script `collect_data.py`:
- Interroge l'API CoinGecko pour 30 jours de données Bitcoin
- Récupère les prix et volumes journaliers
- Sauvegarde dans `market_data.csv`

### 2. Feature Engineering

Le modèle utilise ces features:
- **prev_price**: Prix du jour précédent
- **prev_volume**: Volume du jour précédent
- **price_change**: Changement de prix en pourcentage
- **volume_change**: Changement de volume en pourcentage

### 3. Entraînement du modèle

Le modèle de régression linéaire:
- S'entraîne sur 80% des données
- Teste sur 20% des données
- Calcule MSE et R² Score pour évaluer la performance

### 4. Prédiction

Pour faire une prédiction:
1. Le serveur récupère les dernières données de CoinGecko
2. Appelle le script Python avec ces données
3. Le modèle fait une prédiction
4. Retourne le prix prédit et un signal de trading

### 5. Signaux de trading

- **🟢 ACHETER**: Si le prix prédit est > 1% au-dessus du prix actuel
- **🔴 VENDRE**: Si le prix prédit est > 1% en-dessous du prix actuel
- **🟡 HOLD**: Si le changement prédit est < 1%

## 📊 Métriques du modèle

### MSE (Mean Squared Error)
Mesure l'erreur moyenne au carré. Plus c'est bas, mieux c'est.

### R² Score
Mesure la qualité de l'ajustement (0 à 1):
- **0.9-1.0**: Excellent
- **0.7-0.9**: Bon
- **0.5-0.7**: Moyen
- **<0.5**: Faible

## 🚀 Améliorer le modèle

### 1. Ajouter plus de features

```python
# Dans ai_model.py, ajouter:
df['moving_avg_7'] = df['price'].rolling(window=7).mean()
df['volatility'] = df['price'].rolling(window=7).std()
df['rsi'] = calculate_rsi(df['price'])  # Implémenter RSI
```

### 2. Utiliser plus de données

```python
# Dans collect_data.py, modifier:
days = '90'  # Au lieu de '30'
```

### 3. Essayer d'autres modèles

```python
# Régression polynomiale
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

model = make_pipeline(PolynomialFeatures(2), LinearRegression())

# Ou Random Forest
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor(n_estimators=100)

# Ou XGBoost (installer: pip install xgboost)
import xgboost as xgb
model = xgb.XGBRegressor(n_estimators=100)
```

### 4. Ajouter plus de cryptos

Modifiez `index.js` pour supporter plusieurs cryptos:

```javascript
app.get('/predict_price/:coin', async (req, res) => {
    const coinId = req.params.coin;  // bitcoin, ethereum, etc.
    // ...
});
```

### 5. Implémenter un backtesting

Testez la stratégie sur des données historiques:

```python
def backtest_strategy(df):
    initial_capital = 10000
    capital = initial_capital
    positions = []
    
    for i in range(len(df)):
        prediction = model.predict(...)
        if prediction > current_price * 1.01:
            # Acheter
            positions.append({'type': 'buy', 'price': current_price})
        elif prediction < current_price * 0.99:
            # Vendre
            if positions:
                profit = (current_price - positions[-1]['price']) / positions[-1]['price']
                capital *= (1 + profit)
    
    return (capital - initial_capital) / initial_capital * 100
```

## ⚠️ Avertissements

1. **Ce n'est PAS un conseil financier**
   - Ce projet est à but éducatif uniquement
   - Les prédictions ne sont pas garanties
   - Ne tradez jamais avec plus que vous ne pouvez perdre

2. **Limitations du modèle**
   - La régression linéaire est un modèle simple
   - Les marchés crypto sont très volatiles
   - Beaucoup de facteurs externes ne sont pas pris en compte

3. **Tests requis**
   - Backtestez toujours votre stratégie
   - Testez avec du paper trading avant de trader réellement
   - Surveillez les performances du modèle régulièrement

## 📝 Licence

MIT - Utilisez librement pour vos projets personnels et commerciaux.

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à:
- Reporter des bugs
- Suggérer des améliorations
- Proposer de nouvelles features

## 📚 Ressources

- [Documentation API CoinGecko](https://www.coingecko.com/en/api/documentation)
- [Scikit-learn Documentation](https://scikit-learn.org/)
- [Express.js Guide](https://expressjs.com/)
- [Tutorial original CoinGecko](https://www.coingecko.com/learn/crypto-price-prediction-ai-model)

---

**Bon trading! 🚀📈💰**

*N'oubliez pas: La meilleure stratégie est celle qui correspond à votre profil de risque et vos objectifs.*
