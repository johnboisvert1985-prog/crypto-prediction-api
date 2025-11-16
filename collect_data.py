import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def collect_market_data(coin_id='bitcoin'):
    """
    Collecte 30 jours de données historiques depuis CoinGecko API
    
    Args:
        coin_id (str): ID de la crypto sur CoinGecko (ex: 'bitcoin', 'ethereum')
    """
    # Configuration
    vs_currency = 'usd'
    days = '30'
    
    # URL de l'API CoinGecko pour les données de marché
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
    
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    
    # Ajouter la clé API si disponible
    headers = {}
    api_key = os.environ.get('COINGECKO_API_KEY')
    if api_key:
        headers['x-cg-demo-api-key'] = api_key
        print(f"🔑 Utilisation de la clé API CoinGecko")
    else:
        print(f"⚠️  Pas de clé API - utilisation de l'API gratuite (limites: 30 appels/min)")
    
    print(f"📊 Collecte des données {coin_id.upper()} pour les {days} derniers jours...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Vérifier si on a bien reçu des données
        if 'prices' not in data or 'total_volumes' not in data:
            print(f"❌ Erreur: Réponse API invalide pour {coin_id}")
            return None
        
        # Extraction des prix et volumes
        prices = data['prices']
        volumes = data['total_volumes']
        
        # Création du DataFrame
        df_prices = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df_volumes = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
        
        # Conversion des timestamps
        df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')
        df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp'], unit='ms')
        
        # Fusion des données
        df = pd.merge(df_prices, df_volumes, on='timestamp')
        
        # Nom du fichier basé sur la crypto
        filename = f'market_data_{coin_id}.csv'
        df.to_csv(filename, index=False)
        
        print(f"✅ Données {coin_id.upper()} collectées avec succès!")
        print(f"📈 Nombre de points de données: {len(df)}")
        print(f"💰 Prix actuel: ${df['price'].iloc[-1]:,.2f}")
        print(f"📊 Volume 24h: ${df['volume'].iloc[-1]:,.0f}")
        print(f"📁 Données sauvegardées dans: {filename}")
        
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"❌ Erreur 429: Trop de requêtes à l'API CoinGecko")
            print(f"💡 Solution 1: Attendez 2-3 minutes et réessayez")
            print(f"💡 Solution 2: Obtenez une clé API gratuite sur https://www.coingecko.com/en/api/pricing")
        elif e.response.status_code == 404:
            print(f"❌ Erreur 404: Crypto '{coin_id}' introuvable sur CoinGecko")
            print(f"💡 Vérifiez l'ID de la crypto sur https://www.coingecko.com/")
        else:
            print(f"❌ Erreur HTTP {e.response.status_code}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la collecte des données: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None

if __name__ == "__main__":
    # Récupérer le coin_id depuis les arguments ou utiliser bitcoin par défaut
    coin_id = sys.argv[1] if len(sys.argv) > 1 else 'bitcoin'
    collect_market_data(coin_id)
