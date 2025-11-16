import requests
import pandas as pd
import sys
from datetime import datetime

def collect_market_data(coin_id='bitcoin'):
    """
    Collecte 90 jours de données historiques pour n'importe quelle crypto depuis CoinGecko API
    """
    vs_currency = 'usd'
    days = '90'  # 90 jours pour plus de données d'entraînement
    
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
        market_caps = data.get('market_caps', [])
        
        # Création du DataFrame
        df_prices = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df_volumes = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
        
        # Conversion des timestamps
        df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')
        df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp'], unit='ms')
        
        # Fusion des données
        df = pd.merge(df_prices, df_volumes, on='timestamp')
        
        # Ajouter market cap si disponible
        if market_caps:
            df_market_caps = pd.DataFrame(market_caps, columns=['timestamp', 'market_cap'])
            df_market_caps['timestamp'] = pd.to_datetime(df_market_caps['timestamp'], unit='ms')
            df = pd.merge(df, df_market_caps, on='timestamp', how='left')
        
        # Sauvegarde en CSV
        df.to_csv('market_data.csv', index=False)
        
        print(f"✅ Données collectées avec succès!")
        print(f"📈 Nombre de jours: {len(df)}")
        print(f"💰 Prix le plus récent: ${df['price'].iloc[-1]:,.2f}")
        print(f"📊 Volume moyen 24h: ${df['volume'].mean():,.0f}")
        print(f"📁 Fichier sauvegardé: market_data.csv")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête API: {e}")
        return False
    except KeyError as e:
        print(f"❌ Erreur: Données manquantes dans la réponse API: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    # Récupérer le coin_id depuis les arguments de ligne de commande
    coin_id = sys.argv[1] if len(sys.argv) > 1 else 'bitcoin'
    
    print(f"\n{'='*60}")
    print(f"🚀 Collecte de données pour: {coin_id.upper()}")
    print(f"{'='*60}\n")
    
    success = collect_market_data(coin_id)
    
    if success:
        print(f"\n✅ Collecte terminée avec succès!")
    else:
        print(f"\n❌ Échec de la collecte")
        sys.exit(1)
