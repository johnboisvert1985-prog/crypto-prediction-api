#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte de données crypto avec feature engineering
Basé sur la méthode CoinGecko
"""

import requests
import pandas as pd
import numpy as np
import sys
import json
from datetime import datetime

def fetch_ohlc_data(coin_id, days=30):
    """
    Récupère les données OHLC (Open, High, Low, Close) de CoinGecko
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {
        "vs_currency": "usd",
        "days": days
    }
    
    try:
        print(f"📊 Récupération données OHLC pour {coin_id.upper()}...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 429:
            print("⚠️ Rate limit CoinGecko. Tentative avec données simplifiées...")
            return fetch_simple_data(coin_id, days)
        
        if response.status_code != 200:
            raise Exception(f"Erreur API: {response.status_code}")
        
        data = response.json()
        
        if not data or len(data) < 7:
            raise Exception("Pas assez de données historiques")
        
        # Créer DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"✅ {len(df)} jours de données récupérées")
        return df
        
    except Exception as e:
        print(f"❌ Erreur OHLC: {str(e)}")
        return fetch_simple_data(coin_id, days)

def fetch_simple_data(coin_id, days=30):
    """
    Fallback: utilise market_chart pour obtenir seulement les prix
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    
    try:
        print(f"📈 Fallback: récupération prix simples...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Erreur API: {response.status_code}")
        
        data = response.json()
        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])
        
        if len(prices) < 7:
            raise Exception("Pas assez de données")
        
        # Créer DataFrame avec prix seulement
        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Simuler OHLC à partir du prix
        df['open'] = df['close']
        df['high'] = df['close'] * 1.02  # +2%
        df['low'] = df['close'] * 0.98   # -2%
        
        # Ajouter volumes si disponibles
        if volumes:
            vol_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
            df = df.merge(vol_df, on='timestamp', how='left')
        
        print(f"✅ {len(df)} jours de données (mode simplifié)")
        return df
        
    except Exception as e:
        print(f"❌ Erreur complète: {str(e)}")
        return None

def create_features(df):
    """
    Feature engineering - Méthode CoinGecko
    """
    print("🔧 Création des features...")
    
    # 1. Différences de prix
    df['open_close'] = df['open'] - df['close']
    df['high_low'] = df['high'] - df['low']
    
    # 2. Moyennes mobiles
    df['ma_7'] = df['close'].rolling(window=7, min_periods=1).mean()
    df['ma_14'] = df['close'].rolling(window=14, min_periods=7).mean()
    
    # 3. Volatilité (écart-type sur 7 jours)
    df['volatility'] = df['close'].rolling(window=7, min_periods=1).std()
    
    # 4. Prix relatif (ratio avec max sur 14 jours)
    rolling_max = df['close'].rolling(window=14, min_periods=7).max()
    df['price_ratio'] = df['close'] / rolling_max
    
    # 5. Momentum (changement de prix sur 7 jours)
    df['momentum'] = df['close'].pct_change(periods=7)
    
    # 6. Range ratio (high-low / close)
    df['range_ratio'] = (df['high'] - df['low']) / df['close']
    
    # Remplir les NaN avec des valeurs raisonnables
    df = df.fillna(method='bfill').fillna(method='ffill')
    
    # Vérifier qu'on a assez de données valides
    if len(df) < 7:
        raise Exception("Pas assez de données après feature engineering")
    
    print(f"✅ Features créées: {len(df)} lignes valides")
    
    return df

def save_data(df, coin_id):
    """
    Sauvegarde les données pour le modèle
    """
    filename = f"data_{coin_id}.csv"
    df.to_csv(filename, index=False)
    print(f"💾 Données sauvegardées: {filename}")
    
    # Sauvegarder aussi le dernier prix pour référence
    latest_data = {
        'coin_id': coin_id,
        'latest_close': float(df['close'].iloc[-1]),
        'latest_open': float(df['open'].iloc[-1]),
        'latest_high': float(df['high'].iloc[-1]),
        'latest_low': float(df['low'].iloc[-1]),
        'timestamp': df['timestamp'].iloc[-1].isoformat(),
        'rows': len(df)
    }
    
    with open(f"latest_{coin_id}.json", 'w') as f:
        json.dump(latest_data, f)
    
    return filename

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python collect_data_v2.py <coin_id>")
        sys.exit(1)
    
    coin_id = sys.argv[1].lower()
    
    print("=" * 60)
    print(f"🚀 COLLECTE DE DONNÉES V2: {coin_id.upper()}")
    print("=" * 60)
    print()
    
    try:
        # 1. Récupérer données OHLC
        df = fetch_ohlc_data(coin_id, days=30)
        
        if df is None or len(df) < 7:
            raise Exception("Impossible de récupérer assez de données")
        
        # 2. Créer features
        df = create_features(df)
        
        # 3. Sauvegarder
        filename = save_data(df, coin_id)
        
        print()
        print("=" * 60)
        print("✅ COLLECTE TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print(f"Fichier: {filename}")
        print(f"Lignes: {len(df)}")
        print(f"Features: {len(df.columns)}")
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ÉCHEC DE LA COLLECTE")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
