const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fetch = require('node-fetch');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Cache pour la liste des cryptos
let cryptoListCache = null;

console.log(`\n${'='.repeat(60)}`);
console.log(`🚀 SERVEUR DE PRÉDICTION CRYPTO V2.1`);
console.log(`${'='.repeat(60)}\n`);

// Générer les 250 cryptos au démarrage
async function initializeCryptos() {
    console.log('📥 Initialisation des cryptos...');
    
    try {
        console.log('🔄 Récupération des 250 cryptos de CoinGecko...');
        
        const response = await fetch(
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false',
            { timeout: 30000 }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Formater les données
        const cryptos = data.map((crypto, index) => ({
            id: crypto.id,
            symbol: crypto.symbol.toUpperCase(),
            name: crypto.name,
            rank: index + 1,
            price: crypto.current_price,
            market_cap: crypto.market_cap,
            price_change_24h: crypto.price_change_percentage_24h,
            image: crypto.image
        }));
        
        cryptoListCache = {
            cryptos,
            total: cryptos.length
        };
        
        console.log(`✅ ${cryptos.length} cryptos chargées avec succès!`);
        return true;
        
    } catch (error) {
        console.error(`⚠️  Erreur: ${error.message}`);
        console.log('📦 Utilisation du cache de secours (5 cryptos)...');
        
        // Fallback: 5 cryptos
        cryptoListCache = {
            cryptos: [
                {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "rank": 1, "price": 91471.52, "market_cap": 1824134320935, "price_change_24h": -3.42, "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png?1696501400"},
                {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "rank": 2, "price": 3065.81, "market_cap": 369763275504, "price_change_24h": -3.03, "image": "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png?1696501628"},
                {"id": "tether", "symbol": "USDT", "name": "Tether", "rank": 3, "price": 0.998937, "market_cap": 183838708667, "price_change_24h": -0.02, "image": "https://coin-images.coingecko.com/coins/images/325/large/Tether.png?1696501661"},
                {"id": "ripple", "symbol": "XRP", "name": "XRP", "rank": 4, "price": 2.18, "market_cap": 131220666511, "price_change_24h": -3.98, "image": "https://coin-images.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png?1696501442"},
                {"id": "binancecoin", "symbol": "BNB", "name": "BNB", "rank": 5, "price": 917.27, "market_cap": 126446199641, "price_change_24h": -0.17, "image": "https://coin-images.coingecko.com/coins/images/825/large/bnb-icon2_2x.png?1696501970"}
            ],
            total: 5
        };
        
        return false;
    }
}

// ============================================================================
// ENDPOINT: Liste des cryptos
// ============================================================================
app.get('/api/crypto-list', (req, res) => {
    try {
        if (cryptoListCache) {
            return res.json(cryptoListCache);
        }
        
        throw new Error('Cache non disponible');
        
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
                timeout: 120000
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
                timeout: 60000
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
        version: '2.1 - Gradient Boosting'
    });
});

// ============================================================================
// Démarrage du serveur
// ============================================================================
async function start() {
    // Initialiser les cryptos au démarrage
    await initializeCryptos();
    
    // Démarrer le serveur
    app.listen(PORT, () => {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`🌐 Serveur écoute sur: http://localhost:${PORT}`);
        console.log(`📊 Liste cryptos: http://localhost:${PORT}/api/crypto-list`);
        console.log(`🔮 Prédiction: http://localhost:${PORT}/api/predict/bitcoin`);
        console.log(`❤️  Santé: http://localhost:${PORT}/api/health`);
        console.log(`${'='.repeat(60)}\n`);
    });
}

start();
