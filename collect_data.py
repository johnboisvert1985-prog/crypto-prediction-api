import requests
import pandas as pd
from datetime import datetime, timedelta
import os

def collect_market_data():
    """
    Collecte 30 jours de données historiques Bitcoin depuis CoinGecko API
    """
    # Configuration
    coin_id = 'bitcoin'
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
    
    print(f"📊 Collecte des données {coin_id} pour les {days} derniers jours...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Vérifier si on a bien reçu des données
        if 'prices' not in data or 'total_volumes' not in data:
            print(f"❌ Erreur: Réponse API invalide")
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
        
        # Sauvegarde en CSV
        df.to_csv('market_data.csv', index=False)
        
        print(f"✅ Données collectées avec succès!")
        print(f"📈 Nombre de points de données: {len(df)}")
        print(f"💰 Prix actuel: ${df['price'].iloc[-1]:,.2f}")
        print(f"📊 Volume 24h: ${df['volume'].iloc[-1]:,.0f}")
        print(f"📁 Données sauvegardées dans: market_data.csv")
        
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"❌ Erreur 429: Trop de requêtes à l'API CoinGecko")
            print(f"💡 Solution 1: Attendez 2-3 minutes et réessayez")
            print(f"💡 Solution 2: Obtenez une clé API gratuite sur https://www.coingecko.com/en/api/pricing")
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
    collect_market_data()
