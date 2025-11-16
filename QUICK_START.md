# 🚀 DÉMARRAGE RAPIDE - Système de Prédiction Crypto IA

Salut! Voici ton système complet de prédiction de prix crypto basé sur l'article de CoinGecko.

## 📁 Fichiers créés

```
crypto-prediction-ai/
│
├── 📄 collect_data.py          # Collecte les données Bitcoin (30 jours)
├── 📄 ai_model.py              # Modèle IA de régression linéaire
├── 📄 index.js                 # Serveur Express API
│
├── 📄 package.json             # Dépendances Node.js
├── 📄 requirements.txt         # Dépendances Python
│
├── 📄 start.sh                 # Script de démarrage rapide (Linux/Mac)
├── 📄 start.bat                # Script de démarrage rapide (Windows)
│
├── 📄 .env.example             # Configuration exemple
├── 📄 .gitignore              # Fichiers à ignorer
│
├── 📄 README.md               # Documentation complète
└── 📄 DEPLOYMENT.md           # Guide de déploiement
```

## ⚡ Installation Ultra-Rapide

### Sur Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

### Sur Windows:
```cmd
start.bat
```

**C'est tout!** Le script va:
1. ✅ Vérifier Node.js et Python
2. ✅ Installer toutes les dépendances
3. ✅ Collecter les données Bitcoin
4. ✅ Entraîner le modèle IA
5. ✅ Démarrer le serveur sur http://localhost:3000

## 🎯 Test Rapide

Une fois le serveur démarré, teste:

```bash
# Dans un nouveau terminal
curl http://localhost:3000/predict_price
```

Tu devrais voir une réponse JSON avec:
- Prix actuel de Bitcoin
- Prix prédit par l'IA
- Signal de trading (ACHETER/VENDRE/HOLD)
- Métriques du modèle

## 📊 Exemple de Réponse

```json
{
  "timestamp": "2025-11-16T14:30:00.000Z",
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

## 🔗 Intégration avec ton Dashboard

Tu peux facilement intégrer cette API dans ton dashboard existant:

### En Python (Flask/FastAPI):
```python
import requests

def get_crypto_prediction():
    response = requests.get('http://localhost:3000/predict_price')
    data = response.json()
    return data

# Utilise dans ton dashboard
prediction = get_crypto_prediction()
print(f"Signal: {prediction['trading_signal']['action']}")
print(f"Prix prédit: ${prediction['predicted_price']['value']:,.2f}")
```

### En JavaScript (Frontend):
```javascript
async function getCryptoPrediction() {
    const response = await fetch('http://localhost:3000/predict_price');
    const data = await response.json();
    return data;
}

// Affiche dans ton interface
getCryptoPrediction().then(data => {
    console.log(`Signal: ${data.trading_signal.action}`);
    console.log(`Prix prédit: $${data.predicted_price.value.toFixed(2)}`);
});
```

## 🎨 Personnalisation Rapide

### 1. Changer la crypto:
Dans `index.js`, ligne 10:
```javascript
const COIN_ID = 'ethereum';  // ou 'solana', 'cardano', etc.
```

### 2. Augmenter les données:
Dans `collect_data.py`, ligne 12:
```python
days = '90'  # Au lieu de '30'
```

### 3. Ajuster le seuil de trading:
Dans `index.js`, ligne 111:
```javascript
if (prediction.price_change_pct > 1) {  // Change le 1 à 2 ou 0.5
```

## 🚀 Déploiement sur Railway

Ton setup est déjà prêt pour Railway! Tu dois juste:

1. Push le code sur GitHub
2. Va sur https://railway.app/
3. "New Project" → "Deploy from GitHub"
4. Sélectionne ton repo
5. Railway détecte automatiquement Node.js + Python!

Après le déploiement:
```bash
curl -X POST https://ton-app.railway.app/collect_data
```

**Consulte DEPLOYMENT.md pour d'autres options (Render, Heroku, VPS)**

## 🔄 Mise à jour des données

Pour garder les données fraîches:

### Manuel:
```bash
# Dans ton terminal
curl -X POST http://localhost:3000/collect_data
```

### Automatique (Railway):
Configure un cron externe sur https://cron-job.org/:
- URL: `https://ton-app.railway.app/collect_data`
- Méthode: POST
- Fréquence: Toutes les heures

### Automatique (VPS):
Ajoute à crontab:
```bash
crontab -e
# Ajoute cette ligne:
0 * * * * cd /path/to/project && python3 collect_data.py
```

## 📱 Intégration avec Telegram

Tu peux ajouter des alertes Telegram quand il y a un signal:

```python
# Ajoute ce code dans index.js après la ligne 111

async function sendTelegramAlert(signal, price, predicted) {
    const token = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;
    
    const message = `
🚨 *Signal de Trading Bitcoin*

${signal.emoji} *Action:* ${signal.action}

💰 Prix actuel: $${price.toFixed(2)}
🔮 Prix prédit: $${predicted.toFixed(2)}
📊 Changement: ${((predicted - price) / price * 100).toFixed(2)}%

${signal.description}
    `;
    
    await axios.post(`https://api.telegram.org/bot${token}/sendMessage`, {
        chat_id: chatId,
        text: message,
        parse_mode: 'Markdown'
    });
}

// Appelle après la génération du signal
if (signal !== 'HOLD') {
    await sendTelegramAlert(response.trading_signal, marketData.currentPrice, prediction.predicted_price);
}
```

## 🛠️ Prochaines Étapes

1. ✅ **Teste le système en local**
2. ✅ **Vérifie les prédictions** pendant quelques jours
3. ✅ **Ajuste les paramètres** si nécessaire
4. ✅ **Déploie sur Railway/Render** pour 24/7
5. ✅ **Intègre dans ton dashboard existant**
6. ✅ **Ajoute des alertes Telegram** (optionnel)
7. ✅ **Backteste la stratégie** avant de trader

## ⚠️ Notes Importantes

- 🚫 **Ce n'est PAS un conseil financier**
- 📊 Teste TOUJOURS en paper trading d'abord
- 🔄 Le modèle s'améliore avec plus de données
- 📈 Surveille les performances du modèle
- 💡 Combine avec d'autres indicateurs pour de meilleurs résultats

## 📚 Documentation Complète

- **README.md** - Documentation détaillée de tout le système
- **DEPLOYMENT.md** - Guide complet de déploiement

## 🆘 Support

Si tu as des questions ou des problèmes:

1. Vérifie les logs du serveur
2. Assure-toi que les dépendances sont installées
3. Vérifie que `market_data.csv` existe
4. Teste manuellement `python3 collect_data.py`

## 🎉 Tu es prêt!

Tout est configuré et prêt à l'emploi. Le système suit exactement l'approche de CoinGecko avec:

✅ Collecte automatique de données via API CoinGecko
✅ Modèle IA de régression linéaire avec scikit-learn  
✅ API REST complète avec Express.js
✅ Signaux de trading automatiques
✅ Métriques de performance du modèle
✅ Prêt pour le déploiement

**Lance `./start.sh` (Linux/Mac) ou `start.bat` (Windows) et c'est parti! 🚀**

Bon trading! 💰📈
