#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données V4 - Multi-API avec fallbacks géo-résistants
CoinGecko → CoinCap → Kraken → Cache
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta

class DataCollectorMultiAPI:
    def __init__(self, coin_id, days=30):
        self.coin_id = coin_id.lower()
        self.days = days
        
        # APIs
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.coincap_base = "https://api.coincap.io/v2"
        self.kraken_base = "https://api.kraken.com/0/public"
        
        # Cache
        self.cache_file = f"cache_{self.coin_id}.json"
        self.cache_duration = 5 * 60  # 5 minutes
        
        # Rate limiting
        self.min_delay = 1.0
        self.last_request_time = 0
        
        # Mapping CoinGecko ID → CoinCap ID
        self.coincap_mapping = {
            'bitcoin': 'bitcoin',
            'ethereum': 'ethereum',
            'binancecoin': 'binance-coin',
            'ripple': 'xrp',
            'cardano': 'cardano',
            'solana': 'solana',
            'dogecoin': 'dogecoin',
            'tron': 'tron',
            'polkadot': 'polkadot',
            'polygon': 'polygon',
            'litecoin': 'litecoin',
            'shiba-inu': 'shiba-inu',
            'avalanche-2': 'avalanche',
            'chainlink': 'chainlink',
            'uniswap': 'uniswap',
            'cosmos': 'cosmos',
            'stellar': 'stellar',
            'monero': 'monero',
        }
        
        # Mapping CoinGecko ID → Kraken Symbol
        self.kraken_mapping = {
            'bitcoin': 'XXBTZUSD',
            'ethereum': 'XETHZUSD',
            'ripple': 'XXRPZUSD',
            'cardano': 'ADAUSD',
            'solana': 'SOLUSD',
            'dogecoin': 'XDGUSD',
            'polkadot': 'DOTUSD',
            'polygon': 'MATICUSD',
            'litecoin': 'XLTCZUSD',
            'avalanche-2': 'AVAXUSD',
            'chainlink': 'LINKUSD',
            'uniswap': 'UNIUSD',
            'cosmos': 'ATOMUSD',
            'stellar': 'XXLMZUSD',
        }
    
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
                print(f"✅ Cache valide ({int(age)}s)")
                return True
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
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def _faire_requete(self, url, params=None, max_tentatives=2, source="API"):
        """Fait une requête avec retry"""
        for tentative in range(max_tentatives):
            try:
                self._respecter_rate_limit()
                print(f"🔄 Requête {source}: {url.split('/')[-1]}")
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 429:
                    print(f"⚠️  Rate limit {source} (429)")
                    raise Exception("Rate limit")
                
                if response.status_code == 451:
                    print(f"⚠️  Geo-blocked {source} (451)")
                    raise Exception("Geo-blocked")
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")
                
                print(f"✅ Succès {source}!")
                return response.json()
                
            except Exception as e:
                print(f"⚠️  {source} erreur: {str(e)}")
                if tentative < max_tentatives - 1:
                    time.sleep(2)
        
        raise Exception(f"{source} indisponible")
    
    # =========================================================================
    # COINCAP API - Gratuite, illimitée, pas de geo-block!
    # =========================================================================
    def telecharger_ohlc_coincap(self):
        """Télécharge OHLC depuis CoinCap"""
        print(f"📥 [COINCAP] Téléchargement OHLC...")
        
        coincap_id = self.coincap_mapping.get(self.coin_id)
        if not coincap_id:
            raise Exception(f"{self.coin_id} non disponible sur CoinCap")
        
        print(f"   ID CoinCap: {coincap_id}")
        
        # CoinCap utilise des intervalles (d1 = 1 jour)
        end_time = int(time.time() * 1000)
        start_time = end_time - (self.days * 24 * 60 * 60 * 1000)
        
        url = f"{self.coincap_base}/assets/{coincap_id}/history"
        params = {
            'interval': 'd1',
            'start': start_time,
            'end': end_time
        }
        
        data = self._faire_requete(url, params, source="CoinCap")
        
        if 'data' not in data:
            raise Exception("Pas de données OHLC")
        
        # Convertir format CoinCap → format CoinGecko
        # CoinCap: {time, priceUsd, date}
        # CoinGecko: [timestamp, open, high, low, close]
        
        ohlc_formatted = []
        prices = [float(item['priceUsd']) for item in data['data']]
        
        for i, item in enumerate(data['data']):
            price = float(item['priceUsd'])
            # Approximation: open=close=high=low (CoinCap ne donne que le prix)
            ohlc_formatted.append([
                item['time'],  # timestamp
                price,         # open (approximation)
                price * 1.02,  # high (approximation +2%)
                price * 0.98,  # low (approximation -2%)
                price          # close
            ])
        
        print(f"✅ {len(ohlc_formatted)} jours CoinCap")
        return ohlc_formatted
    
    def get_prix_actuel_coincap(self):
        """Prix actuel depuis CoinCap"""
        print(f"💰 [COINCAP] Prix actuel...")
        
        coincap_id = self.coincap_mapping.get(self.coin_id)
        if not coincap_id:
            raise Exception("Crypto non disponible")
        
        url = f"{self.coincap_base}/assets/{coincap_id}"
        data = self._faire_requete(url, source="CoinCap")
        
        if 'data' not in data:
            raise Exception("Pas de données prix")
        
        asset = data['data']
        
        result = {
            'current_price': float(asset['priceUsd']),
            'price_change_percentage_24h': float(asset.get('changePercent24Hr', 0)),
            'market_cap': float(asset.get('marketCapUsd', 0)),
            'volume_24h': float(asset.get('volumeUsd24Hr', 0)),
            'source': 'coincap'
        }
        
        print(f"✅ Prix CoinCap: ${result['current_price']:,.2f}")
        return result
    
    # =========================================================================
    # KRAKEN API - Gratuite, illimitée, pas de geo-block!
    # =========================================================================
    def telecharger_ohlc_kraken(self):
        """Télécharge OHLC depuis Kraken"""
        print(f"📥 [KRAKEN] Téléchargement OHLC...")
        
        kraken_symbol = self.kraken_mapping.get(self.coin_id)
        if not kraken_symbol:
            raise Exception(f"{self.coin_id} non disponible sur Kraken")
        
        print(f"   Symbole Kraken: {kraken_symbol}")
        
        # Kraken OHLC endpoint
        url = f"{self.kraken_base}/OHLC"
        params = {
            'pair': kraken_symbol,
            'interval': 1440  # 1440 minutes = 1 jour
        }
        
        data = self._faire_requete(url, params, source="Kraken")
        
        if 'error' in data and data['error']:
            raise Exception(f"Erreur Kraken: {data['error']}")
        
        if 'result' not in data:
            raise Exception("Pas de données OHLC")
        
        # Le résultat est dans data['result'][pair_name]
        pair_data = list(data['result'].values())[0]
        
        # Format Kraken: [time, open, high, low, close, vwap, volume, count]
        # Convertir → [timestamp_ms, open, high, low, close]
        
        ohlc_formatted = []
        for candle in pair_data[-self.days:]:  # Garder seulement les N derniers jours
            ohlc_formatted.append([
                int(candle[0]) * 1000,  # timestamp en ms
                float(candle[1]),       # open
                float(candle[2]),       # high
                float(candle[3]),       # low
                float(candle[4])        # close
            ])
        
        print(f"✅ {len(ohlc_formatted)} jours Kraken")
        return ohlc_formatted
    
    def get_prix_actuel_kraken(self):
        """Prix actuel depuis Kraken"""
        print(f"💰 [KRAKEN] Prix actuel...")
        
        kraken_symbol = self.kraken_mapping.get(self.coin_id)
        if not kraken_symbol:
            raise Exception("Symbol non disponible")
        
        # Ticker endpoint
        url = f"{self.kraken_base}/Ticker"
        params = {'pair': kraken_symbol}
        
        data = self._faire_requete(url, params, source="Kraken")
        
        if 'result' not in data:
            raise Exception("Pas de données ticker")
        
        ticker = list(data['result'].values())[0]
        
        # ticker['c'] = [price, lot volume]
        current_price = float(ticker['c'][0])
        
        # Calculer le changement 24h
        open_price = float(ticker['o'])
        change_24h = ((current_price - open_price) / open_price) * 100
        
        result = {
            'current_price': current_price,
            'high_24h': float(ticker['h'][0]),
            'low_24h': float(ticker['l'][0]),
            'price_change_percentage_24h': change_24h,
            'volume_24h': float(ticker['v'][1]),
            'market_cap': 0,
            'source': 'kraken'
        }
        
        print(f"✅ Prix Kraken: ${result['current_price']:,.2f}")
        return result
    
    # =========================================================================
    # COINGECKO (si pas rate limit)
    # =========================================================================
    def telecharger_ohlc_coingecko(self):
        """Télécharge OHLC depuis CoinGecko"""
        print(f"📥 [COINGECKO] Téléchargement OHLC...")
        
        url = f"{self.coingecko_base}/coins/{self.coin_id}/ohlc"
        params = {"vs_currency": "usd", "days": self.days}
        
        data = self._faire_requete(url, params, max_tentatives=1, source="CoinGecko")
        
        if not data or len(data) < 7:
            raise Exception("Pas assez de données")
        
        print(f"✅ {len(data)} jours CoinGecko")
        return data
    
    def get_prix_actuel_coingecko(self):
        """Prix actuel depuis CoinGecko"""
        print(f"💰 [COINGECKO] Prix actuel...")
        
        url = f"{self.coingecko_base}/simple/price"
        params = {
            "ids": self.coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        data = self._faire_requete(url, params, max_tentatives=1, source="CoinGecko")
        
        if self.coin_id not in data:
            raise Exception("Crypto introuvable")
        
        coin_data = data[self.coin_id]
        
        return {
            'current_price': coin_data.get('usd', 0),
            'price_change_percentage_24h': coin_data.get('usd_24h_change', 0),
            'market_cap': coin_data.get('usd_market_cap', 0),
            'source': 'coingecko'
        }
    
    # =========================================================================
    # LOGIQUE PRINCIPALE avec FALLBACKS
    # =========================================================================
    def collecter_donnees(self):
        """Collecte avec fallbacks intelligents"""
        print(f"\n{'='*60}")
        print(f"🔄 COLLECTE MULTI-API - {self.coin_id.upper()}")
        print(f"{'='*60}\n")
        
        # 1. Vérifier le cache
        if self.cache_valide():
            cache = self.charger_cache()
            if cache and 'ohlc' in cache:
                print(f"✅ Cache utilisé\n")
                return cache
        
        # 2. Essayer les APIs dans l'ordre
        sources = [
            ('CoinGecko', self.telecharger_ohlc_coingecko, self.get_prix_actuel_coingecko),
            ('CoinCap', self.telecharger_ohlc_coincap, self.get_prix_actuel_coincap),
            ('Kraken', self.telecharger_ohlc_kraken, self.get_prix_actuel_kraken),
        ]
        
        for source_name, get_ohlc, get_price in sources:
            try:
                print(f"🎯 Tentative {source_name}...\n")
                ohlc_data = get_ohlc()
                market_data = get_price()
                
                print(f"\n✅ {source_name} utilisé avec succès!\n")
                
                # Sauvegarder
                data_output = {
                    "coin_id": self.coin_id,
                    "ohlc": ohlc_data,
                    "market_data": market_data,
                    "timestamp": datetime.now().isoformat(),
                    "total_days": len(ohlc_data),
                    "source": source_name.lower()
                }
                
                # Cache
                with open(self.cache_file, 'w') as f:
                    json.dump(data_output, f, indent=2)
                
                # Data file
                filename = f"data_{self.coin_id}.json"
                with open(filename, 'w') as f:
                    json.dump(data_output, f, indent=2)
                
                print(f"💾 Données sauvegardées")
                print(f"📊 Source: {source_name.upper()}")
                print(f"📊 Prix: ${market_data['current_price']:,.2f}\n")
                
                return data_output
                
            except Exception as e:
                print(f"⚠️  {source_name} échoué: {str(e)}\n")
        
        # 3. Dernier recours: cache expiré
        print(f"📦 Tentative cache expiré...\n")
        cache = self.charger_cache()
        if cache and 'ohlc' in cache:
            print(f"⚠️  Cache expiré utilisé\n")
            return cache
        
        raise Exception("Toutes les sources ont échoué")

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v4.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1]
    
    try:
        collector = DataCollectorMultiAPI(coin_id, days=30)
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
