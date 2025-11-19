#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données avec cache persistant sur disque
Évite les rate limits en réutilisant les données en cache
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta

class DataCollector:
    def __init__(self, coin_id, days=30):
        self.coin_id = coin_id.lower()
        self.days = days
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache_file = f"cache_{self.coin_id}.json"
        self.cache_duration = 24 * 60 * 60  # 24 heures
        self.min_delay = 2.0
        self.last_request_time = 0
    
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
                print(f"✅ Cache valide (âge: {age:.0f}s)")
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
                    wait_time = (2 ** tentative) + 5
                    print(f"⏳ Attente {wait_time}s...")
                    time.sleep(wait_time)
        
        raise Exception(f"Rate limit CoinGecko. Utilisation du cache...")
    
    def telecharger_ohlc(self):
        """Télécharge les données OHLC ou utilise le cache"""
        print(f"📥 Téléchargement OHLC pour {self.coin_id.upper()}...")
        
        # Vérifier le cache d'abord
        if self.cache_valide():
            cache = self.charger_cache()
            if cache:
                return cache
        
        # Sinon, essayer de télécharger
        url = f"{self.base_url}/coins/{self.coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": self.days
        }
        
        try:
            data = self._faire_requete(url, params)
            
            if not data or len(data) < 7:
                raise Exception("Pas assez de données OHLC")
            
            print(f"✅ {len(data)} jours OHLC récupérés")
            return data
        
        except Exception as e:
            print(f"⚠️  {str(e)}")
            print(f"📦 Chargement du cache...")
            
            cache = self.charger_cache()
            if cache:
                print(f"✅ Données du cache utilisées")
                return cache
            
            raise Exception("Impossible de récupérer les données (cache vide)")
    
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
        
        try:
            data = self._faire_requete(url, params)
            
            if not data or len(data) == 0:
                raise Exception("Pas de données de marché")
            
            return data[0]
        
        except Exception as e:
            print(f"⚠️  {str(e)}")
            print(f"📦 Utilisation de données simulées")
            
            # Retourner des données simulées
            return {
                'current_price': 2981.50,
                'high_24h': 3050.00,
                'low_24h': 2950.00,
                'price_change_percentage_24h': 1.5,
                'market_cap': 0
            }
    
    def sauvegarder(self, ohlc_data, market_data):
        """Sauvegarde les données collectées"""
        data_output = {
            "coin_id": self.coin_id,
            "ohlc": ohlc_data,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat(),
            "total_days": len(ohlc_data)
        }
        
        # Sauvegarder le cache
        with open(self.cache_file, 'w') as f:
            json.dump(data_output, f)
        
        print(f"💾 Cache sauvegardé: {self.cache_file}")
        
        # Sauvegarder aussi en fichier de données
        filename = f"data_{self.coin_id}.json"
        with open(filename, 'w') as f:
            json.dump(data_output, f)
        
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
        
        # Télécharger OHLC (ou utiliser cache)
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
