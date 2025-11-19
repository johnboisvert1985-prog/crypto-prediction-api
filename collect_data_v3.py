#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données HYBRIDE - CoinGecko + Binance
Fallback automatique vers Binance si rate limit CoinGecko
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta

class DataCollectorHybrid:
    def __init__(self, coin_id, days=30):
        self.coin_id = coin_id.lower()
        self.days = days
        
        # CoinGecko
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # Binance
        self.binance_base = "https://api.binance.com/api/v3"
        
        # Cache
        self.cache_file = f"cache_{self.coin_id}.json"
        self.cache_duration = 5 * 60  # 5 minutes
        
        # Rate limiting
        self.min_delay = 2.0
        self.last_request_time = 0
        
        # Mapping CoinGecko ID → Binance Symbol
        self.symbol_mapping = {
            'bitcoin': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'binancecoin': 'BNBUSDT',
            'ripple': 'XRPUSDT',
            'cardano': 'ADAUSDT',
            'solana': 'SOLUSDT',
            'dogecoin': 'DOGEUSDT',
            'tron': 'TRXUSDT',
            'polkadot': 'DOTUSDT',
            'polygon': 'MATICUSDT',
            'litecoin': 'LTCUSDT',
            'shiba-inu': 'SHIBUSDT',
            'avalanche-2': 'AVAXUSDT',
            'chainlink': 'LINKUSDT',
            'uniswap': 'UNIUSDT',
            'cosmos': 'ATOMUSDT',
            'stellar': 'XLMUSDT',
            'monero': 'XMRUSDT',
            'ethereum-classic': 'ETCUSDT',
            'bitcoin-cash': 'BCHUSDT',
            'algorand': 'ALGOUSDT',
            'vechain': 'VETUSDT',
            'filecoin': 'FILUSDT',
            'aptos': 'APTUSDT',
            'near': 'NEARUSDT',
            'internet-computer': 'ICPUSDT',
            'hedera-hashgraph': 'HBARUSDT',
            'optimism': 'OPUSDT',
            'arbitrum': 'ARBUSDT',
            'zcash': 'ZECUSDT',
            'aave': 'AAVEUSDT',
            'maker': 'MKRUSDT',
            'the-graph': 'GRTUSDT',
            'fantom': 'FTMUSDT',
            'elrond-erd-2': 'EGLDUSDT',
            'tezos': 'XTZUSDT',
            'theta-token': 'THETAUSDT',
            'axie-infinity': 'AXSUSDT',
            'eos': 'EOSUSDT',
            'compound': 'COMPUSDT',
            'decentraland': 'MANAUSDT',
            'the-sandbox': 'SANDUSDT',
            'crypto-com-chain': 'CROUSDT',
        }
    
    def get_binance_symbol(self):
        """Obtient le symbole Binance pour la crypto"""
        return self.symbol_mapping.get(self.coin_id, None)
    
    def cache_valide(self):
        """Vérifie si le cache est valide"""
        if not os.path.exists(self.cache_file):
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            cache_time = datetime.fromisoformat(cache.get('timestamp', ''))
            age = (datetime.now() - cache_time).total_seconds()
            
            if age < self.cache_duration:
                print(f"✅ Cache valide ({int(age)}s / {self.cache_duration}s)")
                return True
            else:
                print(f"⏰ Cache expiré ({int(age)}s)")
        except:
            pass
        
        return False
    
    def charger_cache(self):
        """Charge les données du cache"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _respecter_rate_limit(self):
        """Respecte le rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _faire_requete(self, url, params, max_tentatives=3, source="API"):
        """Fait une requête avec retry automatique"""
        for tentative in range(max_tentatives):
            try:
                self._respecter_rate_limit()
                print(f"🔄 Requête {source}: {url.split('/')[-1]}")
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 429:
                    print(f"⚠️  Rate limit {source} (429)")
                    raise Exception("Rate limit")
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")
                
                print(f"✅ Succès {source}!")
                return response.json()
                
            except Exception as e:
                print(f"⚠️  {source} erreur: {str(e)}")
                if tentative < max_tentatives - 1:
                    wait = 3
                    print(f"⏳ Retry dans {wait}s...")
                    time.sleep(wait)
        
        raise Exception(f"{source} indisponible après {max_tentatives} tentatives")
    
    # =========================================================================
    # BINANCE - OHLC
    # =========================================================================
    def telecharger_ohlc_binance(self):
        """Télécharge OHLC depuis Binance"""
        print(f"📥 [BINANCE] Téléchargement OHLC pour {self.coin_id.upper()}...")
        
        symbol = self.get_binance_symbol()
        if not symbol:
            raise Exception(f"Crypto {self.coin_id} non disponible sur Binance")
        
        print(f"   Symbole Binance: {symbol}")
        
        # Binance utilise des timestamps en millisecondes
        end_time = int(time.time() * 1000)
        start_time = end_time - (self.days * 24 * 60 * 60 * 1000)
        
        url = f"{self.binance_base}/klines"
        params = {
            'symbol': symbol,
            'interval': '1d',  # 1 jour
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1000
        }
        
        data = self._faire_requete(url, params, max_tentatives=3, source="Binance")
        
        # Convertir format Binance → format CoinGecko
        # Binance: [timestamp, open, high, low, close, volume, ...]
        # CoinGecko: [timestamp, open, high, low, close]
        
        ohlc_formatted = []
        for candle in data:
            ohlc_formatted.append([
                candle[0],  # timestamp (ms)
                float(candle[1]),  # open
                float(candle[2]),  # high
                float(candle[3]),  # low
                float(candle[4])   # close
            ])
        
        print(f"✅ {len(ohlc_formatted)} jours OHLC Binance")
        return ohlc_formatted
    
    # =========================================================================
    # BINANCE - Prix actuel
    # =========================================================================
    def get_prix_actuel_binance(self):
        """Récupère le prix actuel depuis Binance"""
        print(f"💰 [BINANCE] Prix actuel temps réel...")
        
        symbol = self.get_binance_symbol()
        if not symbol:
            raise Exception("Symbol non disponible sur Binance")
        
        # Prix actuel
        url_price = f"{self.binance_base}/ticker/price"
        price_data = self._faire_requete(url_price, {'symbol': symbol}, source="Binance")
        
        # Stats 24h
        url_24h = f"{self.binance_base}/ticker/24hr"
        stats_24h = self._faire_requete(url_24h, {'symbol': symbol}, source="Binance")
        
        result = {
            'current_price': float(price_data['price']),
            'high_24h': float(stats_24h['highPrice']),
            'low_24h': float(stats_24h['lowPrice']),
            'price_change_percentage_24h': float(stats_24h['priceChangePercent']),
            'volume_24h': float(stats_24h['volume']),
            'market_cap': 0,  # Binance ne fournit pas le market cap
            'source': 'binance'
        }
        
        print(f"✅ Prix Binance: ${result['current_price']:,.2f}")
        print(f"   Change 24h: {result['price_change_percentage_24h']:+.2f}%")
        
        return result
    
    # =========================================================================
    # COINGECKO - OHLC (avec fallback)
    # =========================================================================
    def telecharger_ohlc_coingecko(self):
        """Télécharge OHLC depuis CoinGecko"""
        print(f"📥 [COINGECKO] Téléchargement OHLC...")
        
        url = f"{self.coingecko_base}/coins/{self.coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": self.days
        }
        
        try:
            data = self._faire_requete(url, params, max_tentatives=2, source="CoinGecko")
            
            if not data or len(data) < 7:
                raise Exception("Pas assez de données")
            
            print(f"✅ {len(data)} jours OHLC CoinGecko")
            return data
            
        except Exception as e:
            print(f"⚠️  CoinGecko OHLC échoué: {str(e)}")
            raise
    
    # =========================================================================
    # COINGECKO - Prix actuel
    # =========================================================================
    def get_prix_actuel_coingecko(self):
        """Récupère prix actuel depuis CoinGecko"""
        print(f"💰 [COINGECKO] Prix actuel temps réel...")
        
        url = f"{self.coingecko_base}/simple/price"
        params = {
            "ids": self.coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        try:
            data = self._faire_requete(url, params, max_tentatives=2, source="CoinGecko")
            
            if self.coin_id not in data:
                raise Exception("Crypto introuvable")
            
            coin_data = data[self.coin_id]
            
            result = {
                'current_price': coin_data.get('usd', 0),
                'price_change_percentage_24h': coin_data.get('usd_24h_change', 0),
                'market_cap': coin_data.get('usd_market_cap', 0),
                'source': 'coingecko'
            }
            
            print(f"✅ Prix CoinGecko: ${result['current_price']:,.2f}")
            
            return result
            
        except Exception as e:
            print(f"⚠️  CoinGecko prix échoué: {str(e)}")
            raise
    
    # =========================================================================
    # LOGIQUE HYBRIDE PRINCIPALE
    # =========================================================================
    def collecter_donnees(self):
        """Collecte hybride avec fallback intelligent"""
        print(f"\n{'='*60}")
        print(f"🔄 COLLECTE HYBRIDE - {self.coin_id.upper()}")
        print(f"{'='*60}\n")
        
        # 1. Vérifier le cache d'abord
        if self.cache_valide():
            cache = self.charger_cache()
            if cache and 'ohlc' in cache:
                print(f"✅ Utilisation du CACHE\n")
                return cache
        
        # 2. Collecter les données
        ohlc_data = None
        market_data = None
        source_used = None
        
        # Essayer CoinGecko en premier
        try:
            print("🎯 Tentative CoinGecko...\n")
            ohlc_data = self.telecharger_ohlc_coingecko()
            market_data = self.get_prix_actuel_coingecko()
            source_used = 'coingecko'
            print(f"\n✅ CoinGecko utilisé avec succès!\n")
            
        except Exception as e:
            print(f"\n⚠️  CoinGecko échoué: {str(e)}")
            print(f"🔄 Fallback vers Binance...\n")
            
            # Fallback vers Binance
            try:
                ohlc_data = self.telecharger_ohlc_binance()
                market_data = self.get_prix_actuel_binance()
                source_used = 'binance'
                print(f"\n✅ Binance utilisé avec succès!\n")
                
            except Exception as binance_error:
                print(f"\n❌ Binance aussi échoué: {str(binance_error)}")
                
                # Dernier recours: cache même expiré
                print(f"📦 Tentative cache expiré...\n")
                cache = self.charger_cache()
                if cache and 'ohlc' in cache:
                    print(f"⚠️  Utilisation cache EXPIRÉ (mieux que rien!)\n")
                    return cache
                
                raise Exception("Toutes les sources ont échoué (CoinGecko + Binance + Cache)")
        
        # 3. Sauvegarder les données
        data_output = {
            "coin_id": self.coin_id,
            "ohlc": ohlc_data,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat(),
            "total_days": len(ohlc_data),
            "source": source_used
        }
        
        # Sauvegarder le cache
        with open(self.cache_file, 'w') as f:
            json.dump(data_output, f, indent=2)
        
        print(f"💾 Cache sauvegardé: {self.cache_file}")
        
        # Sauvegarder aussi en fichier de données
        filename = f"data_{self.coin_id}.json"
        with open(filename, 'w') as f:
            json.dump(data_output, f, indent=2)
        
        print(f"💾 Données sauvegardées: {filename}")
        print(f"📊 Source: {source_used.upper()}")
        print(f"📊 Prix actuel: ${market_data.get('current_price', 0):,.2f}\n")
        
        return data_output

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v3.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1]
    
    try:
        collector = DataCollectorHybrid(coin_id, days=30)
        result = collector.collecter_donnees()
        
        print("="*60)
        print("✅ COLLECTE RÉUSSIE")
        print("="*60)
        print(f"Données: {result['total_days']} jours")
        print(f"Source: {result['source'].upper()}")
        print(f"Prix: ${result['market_data']['current_price']:,.2f}")
        print()
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("="*60)
        print("❌ ERREUR COLLECTE")
        print("="*60)
        print(f"Erreur: {str(e)}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
