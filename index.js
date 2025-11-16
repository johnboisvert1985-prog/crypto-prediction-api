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

        console.log('🔄 Récupération de la liste des TOP 500 cryptos...');
        
        const fetch = (await import('node-fetch')).default;
        
        // Récupérer le TOP 500 en plusieurs pages (250 par page)
        const pages = 2; // 2 pages × 250 = 500 cryptos
        let allCryptos = [];
        
        for (let page = 1; page <= pages; page++) {
            const url = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=${page}&sparkline=false`;
            
            console.log(`📡 Requête page ${page}/${pages}...`);
            const response = await fetch(url);
            
            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error(`Rate limit CoinGecko atteint. Réessayez dans 1 minute.`);
                }
                throw new Error(`Erreur API CoinGecko: ${response.status}`);
            }
            
            const data = await response.json();
            allCryptos = allCryptos.concat(data);
            
            console.log(`✅ Page ${page}/${pages} récupérée (${data.length} cryptos)`);
            
            // Pause de 3 secondes entre les requêtes pour respecter les limites
            if (page < pages) {
                console.log(`⏳ Pause de 3 secondes...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }

        // Formater la liste
        const cryptoList = allCryptos.map((crypto, index) => ({
            id: crypto.id,
            symbol: crypto.symbol.toUpperCase(),
            name: crypto.name,
            rank: index + 1,
            price: crypto.current_price,
            market_cap: crypto.market_cap,
            price_change_24h: crypto.price_change_percentage_24h,
            image: crypto.image
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
    console.log(`💹 Support: TOP 500 cryptomonnaies`);
    console.log(`${'='.repeat(60)}\n`);
});
