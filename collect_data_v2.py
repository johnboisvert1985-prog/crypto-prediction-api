#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données avec cache persistant sur disque
CORRIGÉ: Cache 5 min + Prix actuel en temps réel
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
        self.cache_duration = 5 * 60  # ✅ 5 MINUTES (au lieu de 24h)
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
                print(f"✅ Cache valide (âge: {age:.0f}s / {self.cache_duration}s)")
                return True
            else:
                print(f"⏰ Cache expiré (âge: {age:.0f}s > {self.cache_duration}s)")
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
    
    def get_current_price_realtime(self):
        """✅ NOUVEAU: Récupère TOUJOURS le prix actuel en temps réel"""
        print(f"💰 Récupération du prix actuel en TEMPS RÉEL...")
        
        url = f"{self.base_url}/simple/price"
        params = {
            "ids": self.coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        
        try:
            data = self._faire_requete(url, params)
            
            if self.coin_id not in data:
                raise Exception(f"Crypto {self.coin_id} introuvable")
            
            coin_data = data[self.coin_id]
            
            result = {
                'current_price': coin_data.get('usd', 0),
                'price_change_percentage_24h': coin_data.get('usd_24h_change', 0),
                'market_cap': coin_data.get('usd_market_cap', 0),
                'volume_24h': coin_data.get('usd_24h_vol', 0)
            }
            
            print(f"✅ Prix actuel: ${result['current_price']:,.2f}")
            print(f"   Change 24h: {result['price_change_percentage_24h']:+.2f}%")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Impossible de récupérer le prix actuel: {str(e)}")
            return None
    
    def telecharger_ohlc(self):
        """Télécharge les données OHLC ou utilise le cache"""
        print(f"📥 Téléchargement OHLC pour {self.coin_id.upper()}...")
        
        # Vérifier le cache d'abord
        if self.cache_valide():
            cache = self.charger_cache()
            if cache and 'ohlc' in cache:
                print(f"✅ Utilisation du cache OHLC ({len(cache['ohlc'])} jours)")
                return cache['ohlc']
        
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
            print(f"📦 Chargement du cache OHLC...")
            
            cache = self.charger_cache()
            if cache and 'ohlc' in cache:
                print(f"✅ Données OHLC du cache utilisées")
                return cache['ohlc']
            
            raise Exception("Impossible de récupérer les données OHLC (cache vide)")
    
    def telecharger_market_data(self):
        """✅ CORRIGÉ: Récupère TOUJOURS le prix actuel en temps réel"""
        print(f"📊 Récupération données de marché...")
        
        # D'ABORD: Essayer le prix en temps réel (rapide et précis)
        realtime = self.get_current_price_realtime()
        if realtime and realtime['current_price'] > 0:
            return realtime
        
        # FALLBACK: Essayer l'endpoint /markets
        print(f"⚠️  Fallback sur /markets...")
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
            
            market = data[0]
            return {
                'current_price': market.get('current_price', 0),
                'high_24h': market.get('high_24h', 0),
                'low_24h': market.get('low_24h', 0),
                'price_change_percentage_24h': market.get('price_change_percentage_24h', 0),
                'market_cap': market.get('market_cap', 0),
                'volume_24h': market.get('total_volume', 0)
            }
        
        except Exception as e:
            print(f"⚠️  {str(e)}")
            print(f"❌ ERREUR: Impossible de récupérer le prix actuel!")
            
            # ❌ PLUS DE DONNÉES SIMULÉES - on force l'erreur
            raise Exception("Impossible de récupérer le prix actuel (API indisponible)")
    
    def sauvegarder(self, ohlc_data, market_data):
        """Sauvegarde les données collectées"""
        data_output = {
            "coin_id": self.coin_id,
            "ohlc": ohlc_data,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat(),
            "total_days": len(ohlc_data),
            "cache_duration": self.cache_duration
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
        print(f"📊 Prix actuel dans le fichier: ${market_data.get('current_price', 0):,.2f}")
        return filename

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v2.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1]
    
    print("=" * 60)
    print(f"🚀 COLLECTE CoinGecko - {coin_id.upper()}")
    print(f"⏰ Cache: 5 minutes | Prix: Temps réel")
    print("=" * 60)
    print()
    
    try:
        collector = DataCollector(coin_id, days=30)
        
        # Télécharger OHLC (ou utiliser cache si < 5 min)
        ohlc_data = collector.telecharger_ohlc()
        
        # Télécharger données de marché (TOUJOURS en temps réel)
        market_data = collector.telecharger_market_data()
        
        # Sauvegarder
        collector.sauvegarder(ohlc_data, market_data)
        
        print()
        print("=" * 60)
        print("✅ COLLECTE RÉUSSIE")
        print("=" * 60)
        print(f"OHLC: {len(ohlc_data)} jours")
        print(f"Prix actuel: ${market_data.get('current_price', 0):,.2f}")
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
