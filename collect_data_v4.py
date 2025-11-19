#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données V5 - 100+ cryptos + Fallback intelligent
CoinGecko → CoinCap (100+ mappings) → Kraken → CoinGecko fallback → Cache
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta

class DataCollectorV5:
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
        
        # ✅ TOP 100+ CRYPTOS - Mapping CoinGecko → CoinCap
        self.coincap_mapping = {
            'bitcoin': 'bitcoin', 'ethereum': 'ethereum', 'tether': 'tether',
            'binancecoin': 'binance-coin', 'solana': 'solana', 'ripple': 'xrp',
            'usd-coin': 'usd-coin', 'cardano': 'cardano', 'dogecoin': 'dogecoin',
            'tron': 'tron', 'avalanche-2': 'avalanche', 'chainlink': 'chainlink',
            'shiba-inu': 'shiba-inu', 'polkadot': 'polkadot', 'bitcoin-cash': 'bitcoin-cash',
            'uniswap': 'uniswap', 'litecoin': 'litecoin', 'near': 'near-protocol',
            'leo-token': 'leo-token', 'polygon': 'polygon', 'dai': 'multi-collateral-dai',
            'wrapped-bitcoin': 'wrapped-bitcoin', 'internet-computer': 'internet-computer',
            'kaspa': 'kaspa', 'ethereum-classic': 'ethereum-classic', 'aptos': 'aptos',
            'monero': 'monero', 'stellar': 'stellar', 'okb': 'okb',
            'render-token': 'render-token', 'immutable-x': 'immutable-x', 'cosmos': 'cosmos',
            'arbitrum': 'arbitrum', 'filecoin': 'filecoin', 'mantle': 'mantle',
            'first-digital-usd': 'first-digital-usd', 'crypto-com-chain': 'crypto-com-coin',
            'hedera-hashgraph': 'hedera-hashgraph', 'vechain': 'vechain', 'blockstack': 'blockstack',
            'optimism': 'optimism', 'injective-protocol': 'injective', 'maker': 'maker',
            'aave': 'aave', 'algorand': 'algorand', 'bittorrent': 'bittorrent',
            'theta-token': 'theta-network', 'sui': 'sui', 'the-graph': 'the-graph',
            'quant-network': 'quant', 'fantom': 'fantom', 'sei-network': 'sei',
            'celestia': 'celestia', 'eos': 'eos', 'tezos': 'tezos',
            'flow': 'flow', 'flare-networks': 'flare', 'kucoin-shares': 'kucoin-token',
            'true-usd': 'trueusd', 'gatetoken': 'gatechain-token', 'thorchain': 'thorchain',
            'beam': 'beam', 'bitget-token': 'bitget-token', 'neo': 'neo',
            'iota': 'iota', 'axie-infinity': 'axie-infinity', 'the-sandbox': 'the-sandbox',
            'kaia': 'kaia', 'zcash': 'zcash', 'decentraland': 'decentraland',
            'elrond-erd-2': 'elrond', 'compound': 'compound-coin', 'ecash': 'ecash',
            'pyth-network': 'pyth-network', 'wemix': 'wemix', 'arweave': 'arweave',
            'jasmycoin': 'jasmy', 'pancakeswap-token': 'pancakeswap', 'helium': 'helium',
            'curve-dao-token': 'curve-dao-token', 'usdd': 'usdd', 'ondo-finance': 'ondo',
            'terra-luna': 'terra-luna', 'conflux-token': 'conflux-network', 'gala': 'gala',
            'pendle': 'pendle', 'fetch-ai': 'fetch', 'raydium': 'raydium',
            'synthetix-network-token': 'synthetix-network-token', 'nexo': 'nexo',
            'ethereum-name-service': 'ethereum-name-service', 'blur': 'blur', 'zilliqa': 'zilliqa',
            'lido-dao': 'lido-dao', 'pax-dollar': 'paxos-standard', 'jito': 'jito',
            'rocket-pool': 'rocket-pool', 'coreum': 'coreum', 'dydx-chain': 'dydx',
            'reserve-rights-token': 'reserve-rights-token', 'jupiter': 'jupiter',
            'trust-wallet-token': 'trust-wallet-token',
        }
        
        # Kraken mappings (30+ cryptos)
        self.kraken_mapping = {
            'bitcoin': 'XXBTZUSD', 'ethereum': 'XETHZUSD', 'tether': 'USDTZUSD',
            'ripple': 'XXRPZUSD', 'cardano': 'ADAUSD', 'solana': 'SOLUSD',
            'dogecoin': 'XDGUSD', 'polkadot': 'DOTUSD', 'polygon': 'MATICUSD',
            'litecoin': 'XLTCZUSD', 'avalanche-2': 'AVAXUSD', 'chainlink': 'LINKUSD',
            'uniswap': 'UNIUSD', 'cosmos': 'ATOMUSD', 'stellar': 'XXLMZUSD',
            'ethereum-classic': 'XETCZUSD', 'algorand': 'ALGOUSD', 'filecoin': 'FILUSD',
            'near': 'NEARUSD', 'optimism': 'OPUSD', 'arbitrum': 'ARBUSD',
            'zcash': 'ZECUSD', 'aave': 'AAVEUSD', 'maker': 'MKRUSD',
            'the-graph': 'GRTUSD', 'tezos': 'XTZUSD', 'eos': 'EOSUSD',
            'compound': 'COMPUSD', 'quant-network': 'QNTUSD', 'injective-protocol': 'INJUSD',
            'render-token': 'RNDRXUSD',
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
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 429:
                    raise Exception("Rate limit")
                
                if response.status_code == 451:
                    raise Exception("Geo-blocked")
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")
                
                return response.json()
                
            except Exception as e:
                if tentative < max_tentatives - 1:
                    time.sleep(2)
                else:
                    raise e
        
        raise Exception(f"{source} indisponible")
    
    # =========================================================================
    # COINCAP API
    # =========================================================================
    def telecharger_ohlc_coincap(self):
        """Télécharge OHLC depuis CoinCap"""
        print(f"📥 [COINCAP] Téléchargement OHLC...")
        
        coincap_id = self.coincap_mapping.get(self.coin_id)
        if not coincap_id:
            raise Exception(f"Non disponible sur CoinCap")
        
        print(f"   ID: {coincap_id}")
        
        end_time = int(time.time() * 1000)
        start_time = end_time - (self.days * 24 * 60 * 60 * 1000)
        
        url = f"{self.coincap_base}/assets/{coincap_id}/history"
        params = {'interval': 'd1', 'start': start_time, 'end': end_time}
        
        data = self._faire_requete(url, params, source="CoinCap")
        
        if 'data' not in data:
            raise Exception("Pas de données")
        
        ohlc_formatted = []
        for item in data['data']:
            price = float(item['priceUsd'])
            ohlc_formatted.append([
                item['time'], price, price * 1.02, price * 0.98, price
            ])
        
        print(f"✅ {len(ohlc_formatted)} jours")
        return ohlc_formatted
    
    def get_prix_actuel_coincap(self):
        """Prix actuel depuis CoinCap"""
        print(f"💰 [COINCAP] Prix actuel...")
        
        coincap_id = self.coincap_mapping.get(self.coin_id)
        if not coincap_id:
            raise Exception("Non disponible")
        
        url = f"{self.coincap_base}/assets/{coincap_id}"
        data = self._faire_requete(url, source="CoinCap")
        
        if 'data' not in data:
            raise Exception("Pas de données")
        
        asset = data['data']
        
        result = {
            'current_price': float(asset['priceUsd']),
            'price_change_percentage_24h': float(asset.get('changePercent24Hr', 0)),
            'market_cap': float(asset.get('marketCapUsd', 0)),
            'volume_24h': float(asset.get('volumeUsd24Hr', 0)),
            'source': 'coincap'
        }
        
        print(f"✅ ${result['current_price']:,.4f}")
        return result
    
    # =========================================================================
    # KRAKEN API
    # =========================================================================
    def telecharger_ohlc_kraken(self):
        """Télécharge OHLC depuis Kraken"""
        print(f"📥 [KRAKEN] Téléchargement OHLC...")
        
        kraken_symbol = self.kraken_mapping.get(self.coin_id)
        if not kraken_symbol:
            raise Exception(f"Non disponible sur Kraken")
        
        print(f"   Symbole: {kraken_symbol}")
        
        url = f"{self.kraken_base}/OHLC"
        params = {'pair': kraken_symbol, 'interval': 1440}
        
        data = self._faire_requete(url, params, source="Kraken")
        
        if 'error' in data and data['error']:
            raise Exception(f"Erreur: {data['error']}")
        
        if 'result' not in data:
            raise Exception("Pas de données")
        
        pair_data = list(data['result'].values())[0]
        
        ohlc_formatted = []
        for candle in pair_data[-self.days:]:
            ohlc_formatted.append([
                int(candle[0]) * 1000,
                float(candle[1]), float(candle[2]),
                float(candle[3]), float(candle[4])
            ])
        
        print(f"✅ {len(ohlc_formatted)} jours")
        return ohlc_formatted
    
    def get_prix_actuel_kraken(self):
        """Prix actuel depuis Kraken"""
        print(f"💰 [KRAKEN] Prix actuel...")
        
        kraken_symbol = self.kraken_mapping.get(self.coin_id)
        if not kraken_symbol:
            raise Exception("Non disponible")
        
        url = f"{self.kraken_base}/Ticker"
        params = {'pair': kraken_symbol}
        
        data = self._faire_requete(url, params, source="Kraken")
        
        if 'result' not in data:
            raise Exception("Pas de données")
        
        ticker = list(data['result'].values())[0]
        current_price = float(ticker['c'][0])
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
        
        print(f"✅ ${result['current_price']:,.2f}")
        return result
    
    # =========================================================================
    # COINGECKO (priorité basse, fallback)
    # =========================================================================
    def telecharger_ohlc_coingecko(self):
        """Télécharge OHLC depuis CoinGecko (fallback)"""
        print(f"📥 [COINGECKO] Téléchargement OHLC...")
        
        url = f"{self.coingecko_base}/coins/{self.coin_id}/ohlc"
        params = {"vs_currency": "usd", "days": self.days}
        
        data = self._faire_requete(url, params, max_tentatives=1, source="CoinGecko")
        
        if not data or len(data) < 7:
            raise Exception("Pas assez de données")
        
        print(f"✅ {len(data)} jours")
        return data
    
    def get_prix_actuel_coingecko(self):
        """Prix actuel depuis CoinGecko (fallback)"""
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
    # ✅ LOGIQUE PRINCIPALE avec FALLBACK INTELLIGENT
    # =========================================================================
    def collecter_donnees(self):
        """Collecte avec fallbacks optimisés"""
        print(f"\n{'='*60}")
        print(f"🔄 COLLECTE V5 - {self.coin_id.upper()}")
        print(f"{'='*60}\n")
        
        # 1. Cache valide?
        if self.cache_valide():
            cache = self.charger_cache()
            if cache and 'ohlc' in cache:
                print(f"✅ Cache utilisé\n")
                return cache
        
        # 2. Ordre des sources (optimisé)
        sources = [
            ('CoinCap', self.telecharger_ohlc_coincap, self.get_prix_actuel_coincap),
            ('Kraken', self.telecharger_ohlc_kraken, self.get_prix_actuel_kraken),
            ('CoinGecko', self.telecharger_ohlc_coingecko, self.get_prix_actuel_coingecko),
        ]
        
        for source_name, get_ohlc, get_price in sources:
            try:
                print(f"🎯 {source_name}...\n")
                ohlc_data = get_ohlc()
                market_data = get_price()
                
                print(f"\n✅ {source_name} OK!\n")
                
                # Sauvegarder
                data_output = {
                    "coin_id": self.coin_id,
                    "ohlc": ohlc_data,
                    "market_data": market_data,
                    "timestamp": datetime.now().isoformat(),
                    "total_days": len(ohlc_data),
                    "source": source_name.lower()
                }
                
                with open(self.cache_file, 'w') as f:
                    json.dump(data_output, f, indent=2)
                
                filename = f"data_{self.coin_id}.json"
                with open(filename, 'w') as f:
                    json.dump(data_output, f, indent=2)
                
                print(f"💾 Sauvegardé")
                print(f"📊 {source_name.upper()}")
                print(f"💰 ${market_data['current_price']:,.4f}\n")
                
                return data_output
                
            except Exception as e:
                print(f"⚠️  {source_name}: {str(e)}\n")
        
        # 3. Cache expiré en dernier recours
        print(f"📦 Cache expiré...\n")
        cache = self.charger_cache()
        if cache and 'ohlc' in cache:
            print(f"⚠️  Cache expiré utilisé\n")
            return cache
        
        raise Exception("Toutes les sources ont échoué")

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v5.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1]
    
    try:
        collector = DataCollectorV5(coin_id, days=30)
        result = collector.collecter_donnees()
        
        print("="*60)
        print("✅ SUCCÈS")
        print("="*60)
        print(f"Jours: {result['total_days']}")
        print(f"Source: {result['source'].upper()}")
        print(f"Prix: ${result['market_data']['current_price']:,.4f}")
        print()
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("="*60)
        print("❌ ERREUR")
        print("="*60)
        print(f"{str(e)}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
