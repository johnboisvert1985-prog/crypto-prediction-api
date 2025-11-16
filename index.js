const express = require('express');
const axios = require('axios');
const { execFile } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');

const execFileAsync = promisify(execFile);
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// CORS activé
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// Configuration de l'API CoinGecko
const COINGECKO_API = 'https://api.coingecko.com/api/v3';
const API_KEY = process.env.COINGECKO_API_KEY;

// Cache pour la liste des cryptos
let cryptoListCache = null;
let cryptoListCacheTime = null;
const CACHE_DURATION = 3600000; // 1 heure

// Headers avec clé API si disponible
function getHeaders() {
    const headers = {};
    if (API_KEY) {
        headers['x-cg-demo-api-key'] = API_KEY;
    }
    return headers;
}

/**
 * Récupère la liste des top 100 cryptos depuis CoinGecko
 */
async function getTopCryptos() {
    // Utiliser le cache si valide
    if (cryptoListCache && cryptoListCacheTime && (Date.now() - cryptoListCacheTime < CACHE_DURATION)) {
        return cryptoListCache;
    }

    try {
        const headers = getHeaders();
        const response = await axios.get(`${COINGECKO_API}/coins/markets`, {
            params: {
                vs_currency: 'usd',
                order: 'market_cap_desc',
                per_page: 100,
                page: 1,
                sparkline: false
            },
            headers: headers
        });

        const cryptoList = response.data.map(coin => ({
            id: coin.id,
            symbol: coin.symbol.toUpperCase(),
            name: coin.name,
            image: coin.image,
            current_price: coin.current_price,
            market_cap: coin.market_cap,
            market_cap_rank: coin.market_cap_rank
        }));

        cryptoListCache = cryptoList;
        cryptoListCacheTime = Date.now();

        return cryptoList;
    } catch (error) {
        console.error('Erreur lors de la récupération de la liste:', error.message);
        // Retourner une liste par défaut en cas d'erreur
        return [
            { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', market_cap_rank: 1 },
            { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', market_cap_rank: 2 },
            { id: 'binancecoin', symbol: 'BNB', name: 'BNB', market_cap_rank: 3 }
        ];
    }
}

/**
 * Vérifie si le fichier de données existe pour une crypto
 */
function dataFileExists(coinId) {
    const filename = path.join(__dirname, `market_data_${coinId}.csv`);
    return fs.existsSync(filename);
}

/**
 * Collecte les données pour une crypto spécifique
 */
async function collectDataForCoin(coinId) {
    console.log(`📊 Collecte des données pour ${coinId}...`);

    try {
        const pythonScript = path.join(__dirname, 'collect_data.py');
        const { stdout, stderr } = await execFileAsync('python3', [pythonScript, coinId], {
            timeout: 60000
        });
        
        if (stderr && stderr.includes('❌')) {
            console.error('Erreur lors de la collecte:', stderr);
            return false;
        }

        console.log(stdout);
        return true;
    } catch (error) {
        console.error(`❌ Erreur lors de la collecte pour ${coinId}:`, error.message);
        return false;
    }
}

/**
 * Récupère les données actuelles d'une crypto depuis CoinGecko
 */
async function getCurrentCryptoData(coinId) {
    try {
        const headers = getHeaders();

        const simplePrice = axios.get(`${COINGECKO_API}/simple/price`, {
            params: {
                ids: coinId,
                vs_currencies: 'usd',
                include_24hr_vol: true,
                include_24hr_change: true
            },
            headers: headers
        });

        const marketData = axios.get(`${COINGECKO_API}/coins/${coinId}/market_chart`, {
            params: {
                vs_currency: 'usd',
                days: '2',
                interval: 'daily'
            },
            headers: headers
        });

        const [priceResponse, chartResponse] = await Promise.all([simplePrice, marketData]);
        
        if (!priceResponse.data[coinId]) {
            throw new Error(`Crypto ${coinId} introuvable`);
        }

        const currentPrice = priceResponse.data[coinId].usd;
        const volume24h = priceResponse.data[coinId].usd_24h_vol;
        const priceChange24h = priceResponse.data[coinId].usd_24h_change || 0;

        const volumes = chartResponse.data.total_volumes;
        const prevVolume = volumes[volumes.length - 2][1];
        const currVolume = volumes[volumes.length - 1][1];
        const volumeChange = ((currVolume - prevVolume) / prevVolume) * 100;

        return {
            currentPrice,
            volume24h,
            priceChange: priceChange24h / 100,
            volumeChange: volumeChange / 100
        };
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error.message);
        if (error.response && error.response.status === 429) {
            throw new Error('Limite de taux API CoinGecko atteinte.');
        }
        throw new Error(`Impossible de récupérer les données pour ${coinId}`);
    }
}

/**
 * Appelle le modèle Python pour faire une prédiction
 */
async function callPythonModel(coinId, currentPrice, volume, priceChange, volumeChange) {
    try {
        const pythonScript = path.join(__dirname, 'ai_model.py');
        
        const { stdout, stderr } = await execFileAsync('python3', [
            pythonScript,
            coinId,
            currentPrice.toString(),
            volume.toString(),
            priceChange.toString(),
            volumeChange.toString()
        ], {
            timeout: 30000
        });

        if (stderr) {
            console.error('Python stderr:', stderr);
        }

        const result = JSON.parse(stdout);
        return result;
    } catch (error) {
        console.error('Erreur Python:', error);
        throw new Error('Erreur lors de l\'exécution du modèle IA: ' + error.message);
    }
}

// Routes

/**
 * Route principale
 */
app.get('/', async (req, res) => {
    const cryptoList = await getTopCryptos();
    
    res.json({
        message: '🚀 API de Prédiction Crypto Multi-Devises avec IA',
        status: 'En ligne',
        api_key_configured: !!API_KEY,
        cors_enabled: true,
        supported_cryptos: cryptoList.length,
        endpoints: {
            '/cryptos': 'GET - Liste des top 100 cryptos disponibles',
            '/predict_price/:coin': 'GET - Prédiction pour une crypto spécifique',
            '/collect_data/:coin': 'POST - Collecter les données pour une crypto',
            '/health': 'GET - État du serveur',
            '/status/:coin': 'GET - État des données pour une crypto'
        },
        examples: {
            bitcoin: '/predict_price/bitcoin',
            ethereum: '/predict_price/ethereum',
            solana: '/predict_price/solana'
        },
        info: {
            model: 'Régression Linéaire',
            data_period: '30 jours',
            top_cryptos: cryptoList.slice(0, 5).map(c => `${c.name} (${c.symbol})`)
        }
    });
});

/**
 * Route pour obtenir la liste des cryptos disponibles
 */
app.get('/cryptos', async (req, res) => {
    try {
        const cryptoList = await getTopCryptos();
        res.json({
            count: cryptoList.length,
            cryptos: cryptoList
        });
    } catch (error) {
        res.status(500).json({
            error: 'Erreur lors de la récupération de la liste',
            message: error.message
        });
    }
});

/**
 * Route de prédiction pour une crypto spécifique
 */
app.get('/predict_price/:coin', async (req, res) => {
    const coinId = req.params.coin.toLowerCase();

    try {
        // Vérifier si les données existent
        if (!dataFileExists(coinId)) {
            console.log(`📊 Données manquantes pour ${coinId}, collecte automatique...`);
            const success = await collectDataForCoin(coinId);
            
            if (!success) {
                return res.status(503).json({
                    error: 'Données non disponibles',
                    message: `Impossible de collecter les données pour ${coinId}`,
                    help: `Essayez POST /collect_data/${coinId} ou attendez quelques minutes`
                });
            }
        }

        console.log(`📊 Récupération des données de marché pour ${coinId}...`);
        const marketData = await getCurrentCryptoData(coinId);
        
        console.log(`🤖 Exécution du modèle IA pour ${coinId}...`);
        const prediction = await callPythonModel(
            coinId,
            marketData.currentPrice,
            marketData.volume24h,
            marketData.priceChange,
            marketData.volumeChange
        );

        // Déterminer le signal de trading
        let signal = 'HOLD';
        let signalEmoji = '🟡';
        if (prediction.price_change_pct > 1) {
            signal = 'ACHETER';
            signalEmoji = '🟢';
        } else if (prediction.price_change_pct < -1) {
            signal = 'VENDRE';
            signalEmoji = '🔴';
        }

        // Récupérer les infos de la crypto
        const cryptoList = await getTopCryptos();
        const cryptoInfo = cryptoList.find(c => c.id === coinId) || { name: coinId.toUpperCase(), symbol: '?' };

        const response = {
            timestamp: new Date().toISOString(),
            coin: `${cryptoInfo.name} (${cryptoInfo.symbol})`,
            coin_id: coinId,
            latest_price: {
                value: marketData.currentPrice,
                currency: 'USD'
            },
            predicted_price: {
                value: prediction.predicted_price,
                currency: 'USD'
            },
            prediction: {
                change_percent: prediction.price_change_pct,
                change_usd: prediction.predicted_price - marketData.currentPrice
            },
            trading_signal: {
                action: signal,
                emoji: signalEmoji,
                description: signal === 'ACHETER' 
                    ? 'Le modèle prédit une hausse > 1%' 
                    : signal === 'VENDRE'
                    ? 'Le modèle prédit une baisse > 1%'
                    : 'Le modèle prédit un mouvement < 1%'
            },
            market_data: {
                volume_24h: marketData.volume24h,
                price_change_24h_percent: marketData.priceChange * 100,
                volume_change_percent: marketData.volumeChange * 100
            },
            model_metrics: prediction.model_metrics
        };

        console.log(`✅ Prédiction générée avec succès pour ${coinId}`);
        res.json(response);

    } catch (error) {
        console.error(`❌ Erreur pour ${coinId}:`, error);
        res.status(500).json({
            error: 'Erreur lors de la génération de la prédiction',
            message: error.message,
            coin_id: coinId,
            timestamp: new Date().toISOString()
        });
    }
});

/**
 * Route pour collecter les données d'une crypto
 */
app.post('/collect_data/:coin', async (req, res) => {
    const coinId = req.params.coin.toLowerCase();
    
    console.log(`📊 Démarrage de la collecte pour ${coinId}...`);
    
    const success = await collectDataForCoin(coinId);
    
    if (success) {
        res.json({
            success: true,
            message: `Données collectées avec succès pour ${coinId}`,
            coin_id: coinId,
            data_file_exists: dataFileExists(coinId),
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(500).json({
            success: false,
            error: 'Erreur lors de la collecte des données',
            coin_id: coinId,
            help: 'Attendez quelques minutes et réessayez. Limite API peut-être atteinte.',
            timestamp: new Date().toISOString()
        });
    }
});

/**
 * Route de statut pour une crypto
 */
app.get('/status/:coin', (req, res) => {
    const coinId = req.params.coin.toLowerCase();
    
    res.json({
        coin_id: coinId,
        data_file_exists: dataFileExists(coinId),
        api_key_configured: !!API_KEY,
        cors_enabled: true,
        timestamp: new Date().toISOString()
    });
});

/**
 * Route de santé
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        api_key_configured: !!API_KEY,
        cors_enabled: true
    });
});

// Démarrage du serveur
app.listen(PORT, async () => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🚀 Serveur API Multi-Crypto démarré!');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`📡 Port: ${PORT}`);
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`🔑 Clé API: ${API_KEY ? '✅ Configurée' : '⚠️  Non configurée'}`);
    console.log(`✅ CORS: Activé`);
    console.log('═══════════════════════════════════════════════════════');
    console.log('💡 Endpoints:');
    console.log('   GET  /cryptos - Liste des top 100 cryptos');
    console.log('   GET  /predict_price/:coin - Prédiction');
    console.log('   POST /collect_data/:coin - Collecter données');
    console.log('   GET  /status/:coin - État des données');
    console.log('   GET  /health - Santé du serveur');
    console.log('═══════════════════════════════════════════════════════');
    
    // Charger la liste des cryptos au démarrage
    console.log('📊 Chargement de la liste des top 100 cryptos...');
    const cryptos = await getTopCryptos();
    console.log(`✅ ${cryptos.length} cryptos chargées`);
    console.log(`🔝 Top 5: ${cryptos.slice(0, 5).map(c => c.symbol).join(', ')}`);
    console.log('═══════════════════════════════════════════════════════');
    console.log('✅ Serveur prêt!');
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Promesse rejetée:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('Exception non capturée:', error);
    process.exit(1);
});
