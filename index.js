const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fetch = require('node-fetch');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Cache pour la liste des cryptos
let cryptoListCache = null;
const CRYPTO_LIST_CACHE_FILE = 'crypto_list_cache.json';
const CRYPTO_LIST_CACHE_DURATION = 60 * 60 * 1000; // 1 heure

console.log(`\n${'='.repeat(60)}`);
console.log(`🚀 SERVEUR DE PRÉDICTION CRYPTO V2.3`);
console.log(`${'='.repeat(60)}\n`);

// ✅ Nettoyer les vieux caches de prédiction au démarrage
function nettoyerVieuxCache() {
    console.log('🧹 Nettoyage des vieux caches de prédiction...');
    
    try {
        const fichiers = fs.readdirSync('.');
        const maintenant = Date.now();
        const maxAge = 5 * 60 * 1000; // 5 minutes
        
        let nettoyes = 0;
        
        fichiers.forEach(fichier => {
            // Nettoyer SEULEMENT les caches de données crypto (pas la liste des 250)
            if ((fichier.startsWith('cache_') || fichier.startsWith('data_')) && 
                fichier.endsWith('.json') && 
                fichier !== CRYPTO_LIST_CACHE_FILE) {
                try {
                    const stats = fs.statSync(fichier);
                    const age = maintenant - stats.mtimeMs;
                    
                    if (age > maxAge) {
                        fs.unlinkSync(fichier);
                        console.log(`   🗑️  Supprimé: ${fichier} (${Math.floor(age/1000/60)}min)`);
                        nettoyes++;
                    }
                } catch (e) {
                    // Ignorer les erreurs
                }
            }
        });
        
        if (nettoyes > 0) {
            console.log(`✅ ${nettoyes} cache(s) de prédiction nettoyé(s)`);
        } else {
            console.log(`✅ Pas de vieux cache à nettoyer`);
        }
    } catch (error) {
        console.log(`⚠️  Erreur nettoyage: ${error.message}`);
    }
    
    console.log();
}

// ✅ Charger le cache de la liste des cryptos (1h)
function chargerCryptoListCache() {
    try {
        if (!fs.existsSync(CRYPTO_LIST_CACHE_FILE)) {
            console.log('📦 Aucun cache trouvé');
            return null;
        }
        
        const stats = fs.statSync(CRYPTO_LIST_CACHE_FILE);
        const age = Date.now() - stats.mtimeMs;
        
        if (age > CRYPTO_LIST_CACHE_DURATION) {
            console.log(`⏰ Cache expiré (${Math.floor(age/1000/60)}min > 60min)`);
            fs.unlinkSync(CRYPTO_LIST_CACHE_FILE);
            return null;
        }
        
        const data = JSON.parse(fs.readFileSync(CRYPTO_LIST_CACHE_FILE, 'utf8'));
        console.log(`✅ Cache chargé: ${data.total} cryptos (${Math.floor(age/1000/60)}min)`);
        
        return data;
    } catch (error) {
        console.log(`⚠️  Erreur lecture cache: ${error.message}`);
        return null;
    }
}

// ✅ Sauvegarder le cache de la liste des cryptos
function sauvegarderCryptoListCache(data) {
    try {
        fs.writeFileSync(CRYPTO_LIST_CACHE_FILE, JSON.stringify(data, null, 2));
        console.log(`💾 Cache sauvegardé: ${data.total} cryptos`);
    } catch (error) {
        console.log(`⚠️  Erreur sauvegarde: ${error.message}`);
    }
}

// ✅ Fonction sleep pour les délais
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ✅ AMÉLIORÉ: Récupération des 250 cryptos avec retry intelligent
async function initializeCryptos() {
    console.log('📥 Initialisation des cryptos...');
    
    // 1. Essayer de charger le cache (1h)
    const cachedData = chargerCryptoListCache();
    if (cachedData && cachedData.total >= 250) {
        cryptoListCache = cachedData;
        console.log(`✅ ${cachedData.total} cryptos prêtes!\n`);
        return true;
    }
    
    // 2. Télécharger depuis CoinGecko avec retry
    console.log('🔄 Téléchargement depuis CoinGecko...');
    
    const maxTentatives = 5; // 5 tentatives
    let delai = 2000; // Commence à 2 secondes
    
    for (let tentative = 1; tentative <= maxTentatives; tentative++) {
        try {
            console.log(`   📡 Tentative ${tentative}/${maxTentatives}...`);
            
            // Attendre avant de réessayer (sauf première tentative)
            if (tentative > 1) {
                console.log(`   ⏳ Attente ${delai/1000}s...`);
                await sleep(delai);
                delai = Math.min(delai * 2, 30000); // Max 30 secondes
            }
            
            // Faire la requête avec timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            
            const response = await fetch(
                'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false',
                { 
                    signal: controller.signal,
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                }
            );
            
            clearTimeout(timeoutId);
            
            // Vérifier le statut
            if (response.status === 429) {
                console.log(`   ⚠️  Rate limit (429)`);
                continue; // Retry
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Parser les données
            const data = await response.json();
            
            if (!Array.isArray(data) || data.length < 10) {
                throw new Error(`Données invalides (${data.length} items)`);
            }
            
            // Formater les cryptos
            const cryptos = data.map((crypto, index) => ({
                id: crypto.id,
                symbol: crypto.symbol.toUpperCase(),
                name: crypto.name,
                rank: index + 1,
                price: crypto.current_price || 0,
                market_cap: crypto.market_cap || 0,
                price_change_24h: crypto.price_change_percentage_24h || 0,
                image: crypto.image || ''
            }));
            
            cryptoListCache = {
                cryptos,
                total: cryptos.length,
                timestamp: new Date().toISOString(),
                fallback: false
            };
            
            // Sauvegarder dans le cache
            sauvegarderCryptoListCache(cryptoListCache);
            
            console.log(`   ✅ ${cryptos.length} cryptos téléchargées!`);
            console.log();
            return true;
            
        } catch (error) {
            console.log(`   ❌ Échec: ${error.message}`);
            
            if (tentative === maxTentatives) {
                console.log(`\n⚠️  Toutes les tentatives ont échoué`);
            }
        }
    }
    
    // 3. Si tout échoue, utiliser le fallback (mais alerter l'utilisateur)
    console.log('📦 Utilisation du mode SECOURS (Top 20)...\n');
    
    cryptoListCache = {
        cryptos: [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "rank": 1, "price": 95123, "market_cap": 1884000000000, "price_change_24h": 2.1, "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png"},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "rank": 2, "price": 3104, "market_cap": 373000000000, "price_change_24h": 1.8, "image": "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png"},
            {"id": "tether", "symbol": "USDT", "name": "Tether", "rank": 3, "price": 1.00, "market_cap": 137000000000, "price_change_24h": 0.01, "image": "https://coin-images.coingecko.com/coins/images/325/large/Tether.png"},
            {"id": "binancecoin", "symbol": "BNB", "name": "BNB", "rank": 4, "price": 693, "market_cap": 100000000000, "price_change_24h": -0.5, "image": "https://coin-images.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"},
            {"id": "solana", "symbol": "SOL", "name": "Solana", "rank": 5, "price": 242, "market_cap": 118000000000, "price_change_24h": 3.2, "image": "https://coin-images.coingecko.com/coins/images/4128/large/solana.png"},
            {"id": "ripple", "symbol": "XRP", "name": "XRP", "rank": 6, "price": 1.43, "market_cap": 82000000000, "price_change_24h": -1.2, "image": "https://coin-images.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"},
            {"id": "usd-coin", "symbol": "USDC", "name": "USDC", "rank": 7, "price": 1.00, "market_cap": 42000000000, "price_change_24h": 0.0, "image": "https://coin-images.coingecko.com/coins/images/6319/large/usdc.png"},
            {"id": "cardano", "symbol": "ADA", "name": "Cardano", "rank": 8, "price": 0.98, "market_cap": 34000000000, "price_change_24h": 1.1, "image": "https://coin-images.coingecko.com/coins/images/975/large/cardano.png"},
            {"id": "dogecoin", "symbol": "DOGE", "name": "Dogecoin", "rank": 9, "price": 0.39, "market_cap": 57000000000, "price_change_24h": 2.8, "image": "https://coin-images.coingecko.com/coins/images/5/large/dogecoin.png"},
            {"id": "tron", "symbol": "TRX", "name": "TRON", "rank": 10, "price": 0.24, "market_cap": 21000000000, "price_change_24h": 0.9, "image": "https://coin-images.coingecko.com/coins/images/1094/large/tron-logo.png"},
            {"id": "avalanche-2", "symbol": "AVAX", "name": "Avalanche", "rank": 11, "price": 40.23, "market_cap": 16000000000, "price_change_24h": 1.5},
            {"id": "chainlink", "symbol": "LINK", "name": "Chainlink", "rank": 12, "price": 22.45, "market_cap": 14000000000, "price_change_24h": 2.1},
            {"id": "polkadot", "symbol": "DOT", "name": "Polkadot", "rank": 13, "price": 7.12, "market_cap": 10000000000, "price_change_24h": -0.8},
            {"id": "polygon", "symbol": "MATIC", "name": "Polygon", "rank": 14, "price": 0.48, "market_cap": 4700000000, "price_change_24h": 1.2},
            {"id": "litecoin", "symbol": "LTC", "name": "Litecoin", "rank": 15, "price": 102.34, "market_cap": 7600000000, "price_change_24h": 0.5},
            {"id": "shiba-inu", "symbol": "SHIB", "name": "Shiba Inu", "rank": 16, "price": 0.00002456, "market_cap": 14000000000, "price_change_24h": 3.4},
            {"id": "uniswap", "symbol": "UNI", "name": "Uniswap", "rank": 17, "price": 12.67, "market_cap": 7600000000, "price_change_24h": 1.8},
            {"id": "cosmos", "symbol": "ATOM", "name": "Cosmos", "rank": 18, "price": 6.78, "market_cap": 2600000000, "price_change_24h": 0.9},
            {"id": "stellar", "symbol": "XLM", "name": "Stellar", "rank": 19, "price": 0.38, "market_cap": 11000000000, "price_change_24h": -0.3},
            {"id": "monero", "symbol": "XMR", "name": "Monero", "rank": 20, "price": 187.45, "market_cap": 3400000000, "price_change_24h": 1.1}
        ],
        total: 20,
        timestamp: new Date().toISOString(),
        fallback: true
    };
    
    console.log(`⚠️  MODE SECOURS: ${cryptoListCache.total} cryptos top market cap\n`);
    return false;
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

// ✅ NOUVEAU: Endpoint pour forcer le refresh
app.post('/api/crypto-list/refresh', async (req, res) => {
    try {
        console.log('\n🔄 REFRESH MANUEL demandé...\n');
        
        // Supprimer le cache
        if (fs.existsSync(CRYPTO_LIST_CACHE_FILE)) {
            fs.unlinkSync(CRYPTO_LIST_CACHE_FILE);
            console.log('🗑️  Cache supprimé\n');
        }
        
        // Recharger
        const success = await initializeCryptos();
        
        res.json({
            success,
            total: cryptoListCache.total,
            fallback: cryptoListCache.fallback || false,
            message: success ? `${cryptoListCache.total} cryptos rechargées!` : 'Mode secours activé'
        });
        
    } catch (error) {
        console.error('❌ Erreur refresh:', error.message);
        res.status(500).json({
            error: 'Erreur lors du refresh',
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
            collectProcess = spawn('python3', ['collect_data_v3.py', coinId], {
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
        fallback: cryptoListCache?.fallback || false,
        version: '2.3 - Smart Retry System'
    });
});

// ============================================================================
// Démarrage du serveur
// ============================================================================
async function start() {
    // Nettoyer les vieux caches de prédiction
    nettoyerVieuxCache();
    
    // Initialiser les cryptos (cache 1h + retry)
    await initializeCryptos();
    
    // Démarrer le serveur
    app.listen(PORT, () => {
        console.log(`${'='.repeat(60)}`);
        console.log(`🌐 Serveur: http://localhost:${PORT}`);
        console.log(`📊 Liste: GET /api/crypto-list`);
        console.log(`🔄 Refresh: POST /api/crypto-list/refresh`);
        console.log(`🔮 Prédire: GET /api/predict/bitcoin`);
        console.log(`❤️  Santé: GET /api/health`);
        console.log(`${'='.repeat(60)}\n`);
    });
}

start();
