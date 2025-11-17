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

// Cache pour la liste des cryptos
let cryptoListCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 60 * 60 * 1000; // 1 heure

console.log(`\n${'='.repeat(60)}`);
console.log(`🚀 SERVEUR DE PRÉDICTION CRYPTO V2.1`);
console.log(`${'='.repeat(60)}\n`);

// ============================================================================
// ENDPOINT: Liste des TOP 250 cryptos
// ============================================================================
app.get('/api/crypto-list', async (req, res) => {
    try {
        // Vérifier le cache
        if (cryptoListCache && cacheTimestamp && (Date.now() - cacheTimestamp < CACHE_DURATION)) {
            console.log('📦 Retour de la liste depuis le cache');
            return res.json(cryptoListCache);
        }

        console.log('📥 Récupération TOP 250 cryptos de CoinGecko...');
        
        const fetch = (await import('node-fetch')).default;
        
        const url = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false`;
        
        console.log('🔄 Requête vers CoinGecko (peut prendre 5-10s)...');
        const response = await fetch(url, { timeout: 20000 });
        
        if (!response.ok) {
            if (response.status === 429) {
                throw new Error(`Rate limit CoinGecko. Réessayez dans 1 minute.`);
            }
            throw new Error(`Erreur API CoinGecko: ${response.status}`);
        }
        
        const data = await response.json();

        // Formater la liste
        const cryptoList = data.map((crypto, index) => ({
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

        console.log(`✅ ${cryptoList.length} cryptos en cache`);
        res.json(cryptoListCache);

    } catch (error) {
        console.error('❌ Erreur:', error.message);
        res.status(500).json({
            error: 'Erreur lors de la récupération de la liste',
            message: error.message
        });
    }
});

// ============================================================================
// ENDPOINT: Prédiction
// ============================================================================
app.get('/api/predict/:coinId', async (req, res) => {
    const { coinId } = req.params;
    const startTime = Date.now();
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`📊 PRÉDICTION: ${coinId.toUpperCase()}`);
    console.log(`${'='.repeat(60)}`);

    let collectProcess = null;
    let modelProcess = null;

    try {
        // ====== ÉTAPE 1: COLLECTE DE DONNÉES ======
        console.log(`\n📥 [1/2] COLLECTE DES DONNÉES`);
        console.log(`⏱️  Timeout: 120 secondes`);

        const collectOutput = await new Promise((resolve, reject) => {
            collectProcess = spawn('python3', ['collect_data_v2.py', coinId], {
                timeout: 120000  // 120 secondes
            });
            
            let output = '';
            let error = '';
            
            collectProcess.stdout.on('data', (data) => {
                const text = data.toString().trim();
                output += text + '\n';
                if (text) console.log(`   ${text}`);
            });
            
            collectProcess.stderr.on('data', (data) => {
                const text = data.toString().trim();
                error += text + '\n';
                if (text) console.error(`   ❌ ${text}`);
            });

            const timeout = setTimeout(() => {
                console.error('   ⏱️  TIMEOUT: La collecte a dépassé 120 secondes!');
                collectProcess.kill('SIGTERM');
                reject(new Error('Collecte timeout (>120s)'));
            }, 125000);

            collectProcess.on('close', (code) => {
                clearTimeout(timeout);
                if (code !== 0) {
                    reject(new Error(`Collecte échouée (code ${code}): ${error}`));
                } else {
                    resolve(output);
                }
            });

            collectProcess.on('error', (err) => {
                clearTimeout(timeout);
                reject(err);
            });
        });

        console.log(`✅ Collecte réussie (${Date.now() - startTime}ms)`);

        // ====== ÉTAPE 2: ENTRAÎNEMENT ET PRÉDICTION ======
        console.log(`\n🤖 [2/2] ENTRAÎNEMENT IA + PRÉDICTION`);
        console.log(`⏱️  Timeout: 60 secondes`);

        const prediction = await new Promise((resolve, reject) => {
            modelProcess = spawn('python3', ['ai_model_v2.py'], {
                timeout: 60000  // 60 secondes
            });
            
            let output = '';
            let error = '';
            
            modelProcess.stdout.on('data', (data) => {
                const text = data.toString().trim();
                output += text + '\n';
                if (text) console.log(`   ${text}`);
            });
            
            modelProcess.stderr.on('data', (data) => {
                const text = data.toString().trim();
                error += text + '\n';
                if (text) console.error(`   ❌ ${text}`);
            });

            const timeout = setTimeout(() => {
                console.error('   ⏱️  TIMEOUT: Le modèle a dépassé 60 secondes!');
                modelProcess.kill('SIGTERM');
                reject(new Error('Modèle timeout (>60s)'));
            }, 65000);

            modelProcess.on('close', (code) => {
                clearTimeout(timeout);
                if (code !== 0) {
                    reject(new Error(`Modèle échoué (code ${code}): ${error}`));
                } else {
                    try {
                        // Extraire le JSON
                        const jsonMatch = output.match(/\{[\s\S]*\}/);
                        if (!jsonMatch) {
                            throw new Error('Aucun JSON trouvé en sortie');
                        }
                        const result = JSON.parse(jsonMatch[0]);
                        resolve(result);
                    } catch (e) {
                        reject(new Error(`Erreur parsing JSON: ${e.message}`));
                    }
                }
            });

            modelProcess.on('error', (err) => {
                clearTimeout(timeout);
                reject(err);
            });
        });

        const totalTime = Date.now() - startTime;
        console.log(`\n✅ PRÉDICTION RÉUSSIE en ${totalTime}ms`);
        console.log(`${'='.repeat(60)}\n`);

        res.json(prediction);

    } catch (error) {
        const totalTime = Date.now() - startTime;
        console.error(`\n❌ ERREUR: ${error.message}`);
        console.error(`Temps écoulé: ${totalTime}ms`);
        console.log(`${'='.repeat(60)}\n`);

        // Tuer les process si encore actifs
        if (collectProcess) collectProcess.kill();
        if (modelProcess) modelProcess.kill();

        res.status(500).json({
            error: 'Erreur lors de la prédiction',
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// ============================================================================
// ENDPOINT: Santé du serveur
// ============================================================================
app.get('/api/health', (req, res) => {
    res.json({
        status: 'online',
        timestamp: new Date().toISOString(),
        cache: cryptoListCache ? `${cryptoListCache.total} cryptos` : 'empty',
        version: '2.1 - Linear Regression'
    });
});

// ============================================================================
// ENDPOINT: Page d'accueil
// ============================================================================
app.get('/', (req, res) => {
    res.json({
        name: '🤖 API Prédiction Crypto IA',
        version: '2.1',
        endpoints: {
            '/api/health': 'GET - État du serveur',
            '/api/crypto-list': 'GET - TOP 250 cryptos',
            '/api/predict/:coinId': 'GET - Prédiction pour une crypto'
        },
        examples: {
            health: 'http://localhost:3000/api/health',
            list: 'http://localhost:3000/api/crypto-list',
            predict: 'http://localhost:3000/api/predict/bitcoin'
        }
    });
});

// ============================================================================
// DÉMARRAGE
// ============================================================================
app.listen(PORT, () => {
    console.log(`🌐 Serveur écoute sur: http://localhost:${PORT}`);
    console.log(`📊 Liste cryptos: http://localhost:${PORT}/api/crypto-list`);
    console.log(`🔮 Prédiction: http://localhost:${PORT}/api/predict/bitcoin`);
    console.log(`❤️  Santé: http://localhost:${PORT}/api/health`);
    console.log();
});
