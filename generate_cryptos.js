#!/usr/bin/env node
/**
 * Script pour générer cryptos.json avec les 250 top cryptos
 * Usage: node generate_cryptos.js
 */

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

async function generateCryptos() {
    console.log('📥 Récupération des 250 cryptos de CoinGecko...');
    
    try {
        const url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false';
        
        console.log('🔄 Requête vers CoinGecko...');
        const response = await fetch(url, { timeout: 30000 });
        
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`✅ ${data.length} cryptos reçues`);
        
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
        
        // Créer le fichier JSON
        const output = {
            cryptos,
            total: cryptos.length,
            timestamp: new Date().toISOString()
        };
        
        // Sauvegarder
        const filePath = path.join(__dirname, 'cryptos.json');
        fs.writeFileSync(filePath, JSON.stringify(output, null, 2));
        
        console.log(`✅ Fichier cryptos.json créé avec ${cryptos.length} cryptos!`);
        console.log(`📍 Fichier: ${filePath}`);
        console.log('🚀 Prêt à être poussé sur GitHub!');
        
    } catch (error) {
        console.error(`❌ Erreur: ${error.message}`);
        process.exit(1);
    }
}

// Exécuter
generateCryptos();
