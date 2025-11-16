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

// ✅ ACTIVER CORS - IMPORTANT pour permettre les requêtes depuis le HTML local
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    
    next();
});

// Configuration de l'API CoinGecko
const COINGECKO_API = 'https://api.coingecko.com/api/v3';
const COIN_ID = 'bitcoin';
const API_KEY = process.env.COINGECKO_API_KEY;
const DATA_FILE = path.join(__dirname, 'market_data.csv');

// État de l'application
let isDataCollected = false;
let isCollecting = false;

// Headers avec clé API si disponible
function getHeaders() {
    const headers = {};
    if (API_KEY) {
        headers['x-cg-demo-api-key'] = API_KEY;
    }
    return headers;
}

/**
 * Vérifie si le fichier de données existe
 */
function dataFileExists() {
    return fs.existsSync(DATA_FILE);
}

/**
 * Collecte les données automatiquement
 */
async function collectDataAutomatically() {
    if (isCollecting) {
        console.log('⏳ Collecte déjà en cours...');
        return false;
    }

    isCollecting = true;
    console.log('📊 Collecte automatique des données...');

    try {
        const pythonScript = path.join(__dirname, 'collect_data.py');
        const { stdout, stderr } = await execFileAsync('python3', [pythonScript], {
            timeout: 60000 // 60 secondes timeout
        });
        
        if (stderr && stderr.includes('❌')) {
            console.error('Erreur lors de la collecte:', stderr);
            isCollecting = false;
            return false;
        }

        console.log(stdout);
        isDataCollected = true;
        isCollecting = false;
        return true;
    } catch (error) {
        console.error('❌ Erreur lors de la collecte automatique:', error.message);
        isCollecting = false;
        return false;
    }
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
async function callPythonModel(currentPrice, volume, priceChange, volumeChange) {
    try {
        const pythonScript = path.join(__dirname, 'ai_model.py');
        
        const { stdout, stderr } = await execFileAsync('python3', [
            pythonScript,
            currentPrice.toString(),
            volume.toString(),
            priceChange.toString(),
            volumeChange.toString()
        ], {
            timeout: 30000 // 30 secondes timeout
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
app.get('/', (req, res) => {
    res.json({
        message: '🚀 API de Prédiction Crypto avec IA',
        status: 'En ligne',
        data_collected: isDataCollected,
        data_file_exists: dataFileExists(),
        api_key_configured: !!API_KEY,
        cors_enabled: true,
        endpoints: {
            '/predict_price': 'GET - Obtenir la prédiction de prix Bitcoin',
            '/health': 'GET - Vérifier l\'état du serveur',
            '/collect_data': 'POST - Collecter les données historiques',
            '/status': 'GET - Vérifier l\'état des données'
        },
        info: {
            coin: 'Bitcoin (BTC)',
            model: 'Régression Linéaire',
            data_period: '30 jours'
        },
        warning: !isDataCollected ? 'Les données ne sont pas encore collectées. Le serveur va les collecter automatiquement.' : null
    });
});

/**
 * Route de statut des données
 */
app.get('/status', (req, res) => {
    res.json({
        data_collected: isDataCollected,
        data_file_exists: dataFileExists(),
        is_collecting: isCollecting,
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
        data_ready: isDataCollected && dataFileExists(),
        timestamp: new Date().toISOString(),
        api_key_configured: !!API_KEY,
        cors_enabled: true
    });
});

/**
 * Route de prédiction principale
 */
app.get('/predict_price', async (req, res) => {
    try {
        // Vérifier si les données sont disponibles
        if (!dataFileExists()) {
            console.log('📊 Données manquantes, collecte automatique...');
            const success = await collectDataAutomatically();
            
            if (!success) {
                return res.status(503).json({
                    error: 'Données non disponibles',
                    message: 'Impossible de collecter les données. Veuillez réessayer dans quelques minutes.',
                    timestamp: new Date().toISOString(),
                    help: 'Si le problème persiste, essayez d\'appeler POST /collect_data manuellement'
                });
            }
        }

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
                : 'Les données sont peut-être en cours de collecte. Réessayez dans quelques secondes.'
        });
    }
});

/**
 * Route pour collecter les données historiques
 */
app.post('/collect_data', async (req, res) => {
    if (isCollecting) {
        return res.status(429).json({
            success: false,
            message: 'Collecte déjà en cours',
            timestamp: new Date().toISOString()
        });
    }

    console.log('📊 Démarrage de la collecte de données manuelle...');
    
    const success = await collectDataAutomatically();
    
    if (success) {
        res.json({
            success: true,
            message: 'Données collectées avec succès',
            data_file_exists: dataFileExists(),
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(500).json({
            success: false,
            error: 'Erreur lors de la collecte des données',
            help: 'Attendez quelques minutes et réessayez. Limite API CoinGecko peut-être atteinte.',
            timestamp: new Date().toISOString()
        });
    }
});

// Collecte automatique au démarrage
async function initializeServer() {
    console.log('🔍 Vérification de l\'existence des données...');
    
    if (!dataFileExists()) {
        console.log('❌ Fichier market_data.csv introuvable');
        console.log('📊 Collecte automatique des données au démarrage...');
        
        // Attendre un peu pour éviter les limites de taux si déployé récemment
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const success = await collectDataAutomatically();
        
        if (success) {
            console.log('✅ Données collectées avec succès au démarrage!');
        } else {
            console.log('⚠️  Échec de la collecte au démarrage. Les données seront collectées à la première prédiction.');
        }
    } else {
        console.log('✅ Fichier market_data.csv trouvé');
        isDataCollected = true;
    }
}

// Démarrage du serveur
app.listen(PORT, async () => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🚀 Serveur API de Prédiction Crypto démarré!');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`📡 Port: ${PORT}`);
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`🔮 Prédiction: http://localhost:${PORT}/predict_price`);
    console.log(`🔑 Clé API CoinGecko: ${API_KEY ? '✅ Configurée' : '⚠️  Non configurée (API gratuite)'}`);
    console.log(`✅ CORS: Activé (requêtes depuis n'importe où)`);
    console.log('═══════════════════════════════════════════════════════');
    console.log('💡 Endpoints disponibles:');
    console.log('   GET  / - Page d\'accueil');
    console.log('   GET  /predict_price - Prédiction de prix');
    console.log('   GET  /health - État du serveur');
    console.log('   GET  /status - État des données');
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
    
    // Initialiser les données
    await initializeServer();
    
    console.log('═══════════════════════════════════════════════════════');
    console.log('✅ Serveur prêt à recevoir des requêtes!');
    console.log('═══════════════════════════════════════════════════════');
});

// Gestion des erreurs non capturées
process.on('unhandledRejection', (reason, promise) => {
    console.error('Promesse rejetée non gérée:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('Exception non capturée:', error);
    process.exit(1);
});
