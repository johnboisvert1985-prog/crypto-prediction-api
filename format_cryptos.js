#!/usr/bin/env node
/**
 * Récupère les 250 cryptos de CoinGecko et les formate en cryptos.json
 * Usage: node format_cryptos.js
 */

const fetch = require('node-fetch');
const fs = require('fs');

async function formatCryptos() {
    console.log('📥 Récupération des 250 cryptos de CoinGecko...');
    
    try {
        const url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false';
        
        const response = await fetch(url, { timeout: 30000 });
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`✅ ${data.length} cryptos reçues de CoinGecko`);
        
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
            total: cryptos.length
        };
        
        // Sauvegarder
        fs.writeFileSync('cryptos.json', JSON.stringify(output, null, 2));
        
        console.log(`✅ Fichier cryptos.json créé avec ${cryptos.length} cryptos!`);
        console.log('📍 Prêt à être poussé sur GitHub!');
        
    } catch (error) {
        console.error(`❌ Erreur: ${error.message}`);
        process.exit(1);
    }
}

formatCryptos();
