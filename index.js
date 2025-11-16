const express = require('express');
const axios = require('axios');
const { execFile } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Configuration de l'API CoinGecko
const COINGECKO_API = 'https://api.coingecko.com/api/v3';
const COIN_ID = 'bitcoin';
const API_KEY = process.env.COINGECKO_API_KEY;

// Headers avec clé API si disponible
function getHeaders() {
    const headers = {};
    if (API_KEY) {
        headers['x-cg-demo-api-key'] = API_KEY;
    }
    return headers;
}

/**
 * Récupère les données actuelles de Bitcoin depuis CoinGecko
 */
async function getCurrentBitcoinData() {
    try {
        const headers = getHeaders();

        // Récupération du prix et volume actuels
        const simplePrice = axios.get(`${COINGECKO_API}/simple/price`, {
            params: {
                ids: COIN_ID,
                vs_currencies: 'usd',
                include_24hr_vol: true,
                include_24hr_change: true
            },
            headers: headers
        });

        // Récupération des données de marché détaillées
        const marketData = axios.get(`${COINGECKO_API}/coins/${COIN_ID}/market_chart`, {
            params: {
                vs_currency: 'usd',
                days: '2',
                interval: 'daily'
            },
            headers: headers
        });

        const [priceResponse, chartResponse] = await Promise.all([simplePrice, marketData]);
        
        const currentPrice = priceResponse.data[COIN_ID].usd;
        const volume24h = priceResponse.data[COIN_ID].usd_24h_vol;
        const priceChange24h = priceResponse.data[COIN_ID].usd_24h_change || 0;

        // Calculer le changement de volume (approximation)
        const volumes = chartResponse.data.total_volumes;
        const prevVolume = volumes[volumes.length - 2][1];
        const currVolume = volumes[volumes.length - 1][1];
        const volumeChange = ((currVolume - prevVolume) / prevVolume) * 100;

        return {
            currentPrice,
            volume24h,
            priceChange: priceChange24h / 100, // Convertir en décimal
            volumeChange: volumeChange / 100    // Convertir en décimal
        };
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error.message);
        if (error.response && error.response.status === 429) {
            throw new Error('Limite de taux API CoinGecko atteinte. Veuillez patienter ou ajouter une clé API.');
        }
        throw new Error('Impossible de récupérer les données de marché');
    }
}

/**
 * Appelle le modèle Python pour faire une prédiction
 */
function callPythonModel(currentPrice, volume, priceChange, volumeChange) {
    return new Promise((resolve, reject) => {
        const pythonScript = path.join(__dirname, 'ai_model.py');
        
        // Note: Utilisez 'python3' si vous avez plusieurs versions de Python
        execFile('python3', [
            pythonScript,
            currentPrice.toString(),
            volume.toString(),
            priceChange.toString(),
            volumeChange.toString()
        ], (error, stdout, stderr) => {
            if (error) {
                console.error('Erreur Python:', error);
                console.error('Stderr:', stderr);
                reject(new Error('Erreur lors de l\'exécution du modèle IA'));
                return;
            }

            try {
                const result = JSON.parse(stdout);
                resolve(result);
            } catch (parseError) {
                console.error('Erreur de parsing JSON:', parseError);
                console.error('Stdout:', stdout);
                reject(new Error('Erreur lors du parsing de la prédiction'));
            }
        });
    });
}

// Routes

/**
 * Route principale
 */
app.get('/', (req, res) => {
    res.json({
        message: '🚀 API de Prédiction Crypto avec IA',
        status: 'En ligne',
        api_key_configured: !!API_KEY,
        endpoints: {
            '/predict_price': 'GET - Obtenir la prédiction de prix Bitcoin',
            '/health': 'GET - Vérifier l\'état du serveur',
            '/collect_data': 'POST - Collecter les données historiques'
        },
        info: {
            coin: 'Bitcoin (BTC)',
            model: 'Régression Linéaire',
            data_period: '30 jours'
        },
        author: 'Système de Trading Automatisé'
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
        api_key_configured: !!API_KEY
    });
});

/**
 * Route de prédiction principale
 */
app.get('/predict_price', async (req, res) => {
    try {
        console.log('📊 Récupération des données de marché...');
        const marketData = await getCurrentBitcoinData();
        
        console.log('🤖 Exécution du modèle IA...');
        const prediction = await callPythonModel(
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

        const response = {
            timestamp: new Date().toISOString(),
            coin: 'Bitcoin (BTC)',
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

        console.log('✅ Prédiction générée avec succès');
        res.json(response);

    } catch (error) {
        console.error('❌ Erreur:', error);
        res.status(500).json({
            error: 'Erreur lors de la génération de la prédiction',
            message: error.message,
            timestamp: new Date().toISOString(),
            help: error.message.includes('Limite de taux') 
                ? 'Obtenez une clé API gratuite sur https://www.coingecko.com/en/api/pricing'
                : 'Vérifiez que les données ont été collectées avec /collect_data'
        });
    }
});

/**
 * Route pour collecter les données historiques
 */
app.post('/collect_data', (req, res) => {
    const pythonScript = path.join(__dirname, 'collect_data.py');
    
    console.log('📊 Démarrage de la collecte de données...');
    
    execFile('python3', [pythonScript], (error, stdout, stderr) => {
        if (error) {
            console.error('Erreur:', error);
            console.error('Stderr:', stderr);
            res.status(500).json({
                success: false,
                error: 'Erreur lors de la collecte des données',
                message: stderr || error.message,
                help: stderr.includes('429') 
                    ? 'Limite API atteinte. Attendez 2-3 minutes ou ajoutez une clé API.'
                    : 'Vérifiez les logs pour plus de détails'
            });
            return;
        }

        console.log('✅ Collecte terminée');
        res.json({
            success: true,
            message: 'Données collectées avec succès',
            output: stdout
        });
    });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🚀 Serveur API de Prédiction Crypto démarré!');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`📡 Port: ${PORT}`);
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`🔮 Prédiction: http://localhost:${PORT}/predict_price`);
    console.log(`🔑 Clé API CoinGecko: ${API_KEY ? '✅ Configurée' : '⚠️  Non configurée (API gratuite)'}`);
    console.log('═══════════════════════════════════════════════════════');
    console.log('💡 Endpoints disponibles:');
    console.log('   GET  / - Page d\'accueil');
    console.log('   GET  /predict_price - Prédiction de prix');
    console.log('   GET  /health - État du serveur');
    console.log('   POST /collect_data - Collecter les données');
    console.log('═══════════════════════════════════════════════════════');
    if (!API_KEY) {
        console.log('⚠️  ATTENTION: Pas de clé API configurée');
        console.log('   L\'API gratuite a des limites (30 appels/min)');
        console.log('   Pour augmenter les limites:');
        console.log('   1. Obtenez une clé gratuite sur https://www.coingecko.com/en/api/pricing');
        console.log('   2. Ajoutez COINGECKO_API_KEY dans vos variables d\'environnement');
        console.log('═══════════════════════════════════════════════════════');
    }
});

// Gestion des erreurs non capturées
process.on('unhandledRejection', (reason, promise) => {
    console.error('Promesse rejetée non gérée:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('Exception non capturée:', error);
    process.exit(1);
});
