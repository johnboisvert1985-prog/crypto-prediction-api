const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Cache pour la liste des cryptos
let cryptoListCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 60 * 60 * 1000; // 1 heure

// Données mock TOP 100 cryptos (pour test immédiat)
const MOCK_CRYPTOS = [
    { id: "bitcoin", symbol: "BTC", name: "Bitcoin", rank: 1, price: 43250.50, market_cap: 846000000000, price_change_24h: 2.5 },
    { id: "ethereum", symbol: "ETH", name: "Ethereum", rank: 2, price: 2280.45, market_cap: 274000000000, price_change_24h: 3.2 },
    { id: "binancecoin", symbol: "BNB", name: "BNB", rank: 3, price: 310.20, market_cap: 47500000000, price_change_24h: 1.8 },
    { id: "solana", symbol: "SOL", name: "Solana", rank: 4, price: 98.75, market_cap: 43200000000, price_change_24h: 5.1 },
    { id: "ripple", symbol: "XRP", name: "XRP", rank: 5, price: 0.62, market_cap: 33800000000, price_change_24h: -0.8 },
    { id: "cardano", symbol: "ADA", name: "Cardano", rank: 6, price: 0.58, market_cap: 20400000000, price_change_24h: 1.2 },
    { id: "avalanche-2", symbol: "AVAX", name: "Avalanche", rank: 7, price: 38.90, market_cap: 14600000000, price_change_24h: 4.3 },
    { id: "dogecoin", symbol: "DOGE", name: "Dogecoin", rank: 8, price: 0.088, market_cap: 12500000000, price_change_24h: 2.1 },
    { id: "polkadot", symbol: "DOT", name: "Polkadot", rank: 9, price: 7.25, market_cap: 9800000000, price_change_24h: -1.5 },
    { id: "chainlink", symbol: "LINK", name: "Chainlink", rank: 10, price: 14.85, market_cap: 8500000000, price_change_24h: 3.7 },
    { id: "tron", symbol: "TRX", name: "TRON", rank: 11, price: 0.105, market_cap: 9200000000, price_change_24h: 1.9 },
    { id: "matic-network", symbol: "MATIC", name: "Polygon", rank: 12, price: 0.82, market_cap: 7600000000, price_change_24h: 2.8 },
    { id: "litecoin", symbol: "LTC", name: "Litecoin", rank: 13, price: 72.50, market_cap: 5400000000, price_change_24h: 0.9 },
    { id: "shiba-inu", symbol: "SHIB", name: "Shiba Inu", rank: 14, price: 0.000024, market_cap: 14200000000, price_change_24h: 4.2 },
    { id: "uniswap", symbol: "UNI", name: "Uniswap", rank: 15, price: 6.45, market_cap: 4800000000, price_change_24h: 1.5 }
];

// Générer 485 cryptos supplémentaires pour atteindre 500
for (let i = 16; i <= 500; i++) {
    MOCK_CRYPTOS.push({
        id: `crypto-${i}`,
        symbol: `CRY${i}`,
        name: `Crypto ${i}`,
        rank: i,
        price: Math.random() * 100,
        market_cap: Math.random() * 1000000000,
        price_change_24h: (Math.random() - 0.5) * 10
    });
}

// Endpoint pour obtenir la liste des cryptos
app.get('/api/crypto-list', async (req, res) => {
    try {
        // Vérifier le cache
        if (cryptoListCache && cacheTimestamp && (Date.now() - cacheTimestamp < CACHE_DURATION)) {
            console.log('📦 Retour de la liste depuis le cache');
            return res.json(cryptoListCache);
        }

        console.log('🔄 Chargement des données (MODE TEST)...');
        
        // Simuler un délai comme une vraie API
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Formater avec images
        const cryptoList = MOCK_CRYPTOS.map(crypto => ({
            ...crypto,
            image: `https://via.placeholder.com/32/6366f1/ffffff?text=${crypto.symbol}`
        }));

        // Mettre en cache
        cryptoListCache = {
            cryptos: cryptoList,
            total: cryptoList.length,
            timestamp: new Date().toISOString(),
            note: "Données de test - CoinGecko rate limit actif"
        };
        cacheTimestamp = Date.now();

        console.log(`✅ Liste TOP ${cryptoList.length} cryptos (MODE TEST) mise en cache`);
        res.json(cryptoListCache);

    } catch (error) {
        console.error('❌ Erreur:', error);
        res.status(500).json({
            error: 'Erreur lors de la récupération de la liste',
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
        cache: cryptoListCache ? `${cryptoListCache.total} cryptos en cache (MODE TEST)` : 'Aucun cache',
        note: 'Données de test - CoinGecko rate limit actif'
    });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Serveur de prédiction crypto IA démarré!`);
    console.log(`📡 Port: ${PORT}`);
    console.log(`⚠️  MODE TEST: Données mockées (500 cryptos)`);
    console.log(`💡 CoinGecko rate limit actif - Réessayez demain`);
    console.log(`${'='.repeat(60)}\n`);
});
