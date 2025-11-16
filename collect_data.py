import requests
import pandas as pd
from datetime import datetime, timedelta

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
    
    print(f"📊 Collecte des données {coin_id} pour les {days} derniers jours...")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
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
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la collecte des données: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None

if __name__ == "__main__":
    collect_market_data()
