#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données OHLC - Basé sur le guide CoinGecko
Récupère les données directement de CoinGecko API
"""

import requests
import json
import sys
import time
from datetime import datetime

class DataCollector:
    def __init__(self, coin_id, days=30):
        self.coin_id = coin_id.lower()
        self.days = days
        self.base_url = "https://api.coingecko.com/api/v3"
        self.min_delay = 1.5
        self.last_request_time = 0
    
    def _respecter_rate_limit(self):
        """Respecte le rate limit de CoinGecko"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _faire_requete(self, url, params, max_tentatives=3):
        """Fait une requête avec retry automatique"""
        for tentative in range(max_tentatives):
            try:
                self._respecter_rate_limit()
                print(f"🔄 Requête: {url}")
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 429:
                    raise Exception("Rate limit atteint (429)")
                if response.status_code != 200:
                    raise Exception(f"Erreur {response.status_code}")
                
                print(f"✅ Succès!")
                return response.json()
                
            except Exception as e:
                print(f"⚠️  {str(e)} - Tentative {tentative + 1}/{max_tentatives}")
                if tentative < max_tentatives - 1:
                    wait_time = (2 ** tentative) + 3
                    time.sleep(wait_time)
        
        raise Exception(f"Impossible de récupérer les données")
    
    def telecharger_ohlc(self):
        """Télécharge les données OHLC de CoinGecko"""
        print(f"📥 Téléchargement OHLC pour {self.coin_id.upper()}...")
        
        url = f"{self.base_url}/coins/{self.coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": self.days
        }
        
        data = self._faire_requete(url, params)
        
        if not data or len(data) < 7:
            raise Exception("Pas assez de données OHLC")
        
        print(f"✅ {len(data)} jours OHLC récupérés")
        return data
    
    def telecharger_market_data(self):
        """Récupère les données de marché actuelles"""
        print(f"📊 Récupération données de marché...")
        
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": self.coin_id,
            "order": "market_cap_desc",
            "per_page": 1
        }
        
        data = self._faire_requete(url, params)
        
        if not data or len(data) == 0:
            raise Exception("Pas de données de marché")
        
        return data[0]
    
    def sauvegarder(self, ohlc_data, market_data):
        """Sauvegarde les données collectées"""
        data_output = {
            "coin_id": self.coin_id,
            "ohlc": ohlc_data,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat(),
            "total_days": len(ohlc_data)
        }
        
        filename = f"data_{self.coin_id}.json"
        with open(filename, 'w') as f:
            json.dump(data_output, f, indent=2)
        
        print(f"💾 Données sauvegardées: {filename}")
        return filename

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v2.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1]
    
    print("=" * 60)
    print(f"🚀 COLLECTE CoinGecko - {coin_id.upper()}")
    print("=" * 60)
    print()
    
    try:
        collector = DataCollector(coin_id, days=30)
        
        # Télécharger OHLC
        ohlc_data = collector.telecharger_ohlc()
        
        # Télécharger données de marché
        market_data = collector.telecharger_market_data()
        
        # Sauvegarder
        collector.sauvegarder(ohlc_data, market_data)
        
        print()
        print("=" * 60)
        print("✅ COLLECTE RÉUSSIE")
        print("=" * 60)
        print(f"Données: {len(ohlc_data)} jours")
        print()
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR COLLECTE")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
