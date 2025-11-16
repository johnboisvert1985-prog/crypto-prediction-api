const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Cache pour la liste des cryptos (rafraîchi toutes les heures)
let cryptoListCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 60 * 60 * 1000; // 1 heure

// Endpoint pour obtenir la liste des TOP 500 cryptos
app.get('/api/crypto-list', async (req, res) => {
    try {
        // Vérifier le cache
        if (cryptoListCache && cacheTimestamp && (Date.now() - cacheTimestamp < CACHE_DURATION)) {
            console.log('📦 Retour de la liste depuis le cache');
            return res.json(cryptoListCache);
        }

        console.log('🔄 Récupération de la liste via CoinCap API...');
        
        const fetch = (await import('node-fetch')).default;
        
        // CoinCap API - Récupérer TOP 500 (max 2000 par requête)
        const url = 'https://api.coincap.io/v2/assets?limit=500';
        
        console.log('📡 Requête CoinCap API...');
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Erreur CoinCap API: ${response.status}`);
        }
        
        const result = await response.json();
        const data = result.data;
        
        console.log(`✅ ${data.length} cryptos récupérées`);
        
        // Formater la liste pour correspondre au format CoinGecko
        const cryptoList = data.map((crypto, index) => ({
            id: crypto.id,
            symbol: crypto.symbol,
            name: crypto.name,
            rank: parseInt(crypto.rank),
            price: parseFloat(crypto.priceUsd),
            market_cap: parseFloat(crypto.marketCapUsd),
            price_change_24h: parseFloat(crypto.changePercent24Hr),
            image: `https://assets.coincap.io/assets/icons/${crypto.symbol.toLowerCase()}@2x.png`
        }));

        // Mettre en cache
        cryptoListCache = {
            cryptos: cryptoList,
            total: cryptoList.length,
            timestamp: new Date().toISOString()
        };
        cacheTimestamp = Date.now();

        console.log(`✅ Liste TOP ${cryptoList.length} cryptos mise en cache`);
        res.json(cryptoListCache);

    } catch (error) {
        console.error('❌ Erreur lors de la récupération de la liste:', error);
        res.status(500).json({
            error: 'Erreur lors de la récupération de la liste des cryptomonnaies',
            message: error.message
        });
    }
});

// Endpoint pour obtenir la prédiction
app.get('/api/predict/:coinId', async (req, res) => {
    const { coinId } = req.params;
    
    console.log(`\n🔮 Nouvelle demande de prédiction pour: ${coinId}`);
    console.log('⏳ Collecte des données en cours...');

    try {
        // 1. Collecter les données
        const collectData = spawn('python3', ['collect_data.py', coinId]);
        
        let collectOutput = '';
        let collectError = '';
        
        collectData.stdout.on('data', (data) => {
            collectOutput += data.toString();
            console.log(data.toString().trim());
        });
        
        collectData.stderr.on('data', (data) => {
            collectError += data.toString();
            console.error(data.toString().trim());
        });

        await new Promise((resolve, reject) => {
            collectData.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Erreur collecte données: ${collectError}`));
                } else {
                    resolve();
                }
            });
        });

        console.log('✅ Données collectées avec succès');
        console.log('🤖 Entraînement du modèle IA...');

        // 2. Entraîner le modèle et faire la prédiction
        const runModel = spawn('python3', ['ai_model.py']);
        
        let modelOutput = '';
        let modelError = '';
        
        runModel.stdout.on('data', (data) => {
            modelOutput += data.toString();
            console.log(data.toString().trim());
        });
        
        runModel.stderr.on('data', (data) => {
            modelError += data.toString();
            console.error(data.toString().trim());
        });

        const result = await new Promise((resolve, reject) => {
            runModel.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Erreur modèle IA: ${modelError}`));
                } else {
                    try {
                        // Extraire le JSON de la sortie
                        const jsonMatch = modelOutput.match(/\{[\s\S]*\}/);
                        if (jsonMatch) {
                            const prediction = JSON.parse(jsonMatch[0]);
                            resolve(prediction);
                        } else {
                            reject(new Error('Format de réponse invalide'));
                        }
                    } catch (e) {
                        reject(new Error(`Erreur parsing JSON: ${e.message}`));
                    }
                }
            });
        });

        console.log('✅ Prédiction générée avec succès');
        res.json(result);

    } catch (error) {
        console.error('❌ Erreur:', error.message);
        res.status(500).json({
            error: 'Erreur lors de la prédiction',
            message: error.message
        });
    }
});

// Endpoint de santé
app.get('/api/health', (req, res) => {
    res.json({
        status: 'online',
        timestamp: new Date().toISOString(),
        cache: cryptoListCache ? `${cryptoListCache.total} cryptos en cache` : 'Aucun cache'
    });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Serveur de prédiction crypto IA démarré!`);
    console.log(`📡 Port: ${PORT}`);
    console.log(`🌐 http://localhost:${PORT}`);
    console.log(`💹 Support: TOP 500 cryptomonnaies via CoinCap`);
    console.log(`${'='.repeat(60)}\n`);
});
