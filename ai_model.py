import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime, timedelta
import json
import requests

def get_current_market_data(coin_id='bitcoin'):
    """
    Récupère les données actuelles du marché depuis CoinGecko
    """
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        market_data = {
            'current_price': data['market_data']['current_price']['usd'],
            'high_24h': data['market_data']['high_24h']['usd'],
            'low_24h': data['market_data']['low_24h']['usd'],
            'price_change_percent': data['market_data']['price_change_percentage_24h'],
            'volume_24h': data['market_data']['total_volume']['usd'],
            'volume_change_percent': data['market_data']['total_volume'].get('usd_24h_change', 0),
            'market_cap': data['market_data']['market_cap']['usd']
        }
        
        return market_data
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération des données actuelles: {e}")
        return None

def train_and_predict():
    """
    Entraîne le modèle IA et fait la prédiction
    """
    print("\n🤖 Démarrage de l'entraînement du modèle IA...")
    
    # 1. Charger les données
    try:
        df = pd.read_csv('market_data.csv')
        print(f"✅ Données chargées: {len(df)} jours d'historique")
    except FileNotFoundError:
        print("❌ Fichier market_data.csv non trouvé")
        return None
    
    # 2. Préparation des features (caractéristiques)
    df['day'] = range(len(df))  # Numéro du jour comme feature
    
    # Features avancées
    df['price_ma_7'] = df['price'].rolling(window=7).mean()  # Moyenne mobile 7 jours
    df['price_ma_30'] = df['price'].rolling(window=30).mean()  # Moyenne mobile 30 jours
    df['volume_ma_7'] = df['volume'].rolling(window=7).mean()  # Volume moyen 7 jours
    df['price_change'] = df['price'].pct_change()  # Variation quotidienne
    df['volatility'] = df['price'].rolling(window=7).std()  # Volatilité sur 7 jours
    
    # Supprimer les NaN créés par rolling
    df = df.dropna()
    
    # Features (X) et Target (y)
    features = ['day', 'volume', 'price_ma_7', 'price_ma_30', 'volume_ma_7', 'volatility']
    X = df[features]
    y = df['price']
    
    print(f"📊 Features utilisées: {features}")
    
    # 3. Division train/test (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    print(f"🎯 Données d'entraînement: {len(X_train)} jours")
    print(f"🧪 Données de test: {len(X_test)} jours")
    
    # 4. Entraînement du modèle
    model = LinearRegression()
    model.fit(X_train, y_train)
    print("✅ Modèle entraîné avec succès!")
    
    # 5. Évaluation du modèle
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📈 Métriques du modèle:")
    print(f"   • MSE (Mean Squared Error): {mse:,.2f}")
    print(f"   • R² Score: {r2:.4f} ({r2*100:.2f}%)")
    
    # 6. Prédiction pour dans 7 jours
    last_day = df['day'].iloc[-1]
    future_day = last_day + 7
    
    # Créer les features pour la prédiction
    last_volume = df['volume'].iloc[-1]
    last_price_ma_7 = df['price_ma_7'].iloc[-1]
    last_price_ma_30 = df['price_ma_30'].iloc[-1]
    last_volume_ma_7 = df['volume_ma_7'].iloc[-1]
    last_volatility = df['volatility'].iloc[-1]
    
    future_features = pd.DataFrame({
        'day': [future_day],
        'volume': [last_volume],
        'price_ma_7': [last_price_ma_7],
        'price_ma_30': [last_price_ma_30],
        'volume_ma_7': [last_volume_ma_7],
        'volatility': [last_volatility]
    })
    
    predicted_price = model.predict(future_features)[0]
    current_price = df['price'].iloc[-1]
    price_change = ((predicted_price - current_price) / current_price) * 100
    
    print(f"\n🔮 Prédiction:")
    print(f"   • Prix actuel: ${current_price:,.2f}")
    print(f"   • Prix prédit (7 jours): ${predicted_price:,.2f}")
    print(f"   • Variation: {price_change:+.2f}%")
    
    # 7. Déterminer le signal de trading
    if price_change > 5:
        signal = "ACHETER"
    elif price_change < -5:
        signal = "VENDRE"
    else:
        signal = "HOLD"
    
    print(f"   • Signal: {signal}")
    
    # 8. Récupérer les données actuelles du marché
    coin_id = 'bitcoin'  # Par défaut, mais sera remplacé par le coin_id réel
    market_data = get_current_market_data(coin_id)
    
    if market_data is None:
        # Utiliser les données du CSV si l'API échoue
        market_data = {
            'current_price': current_price,
            'high_24h': df['price'].iloc[-1],
            'low_24h': df['price'].iloc[-1],
            'price_change_percent': 0,
            'volume_24h': df['volume'].iloc[-1],
            'volume_change_percent': 0,
            'market_cap': 0
        }
    
    # 9. Préparer le résultat JSON
    result = {
        "coin": coin_id,
        "current_price": float(market_data['current_price']),
        "predicted_price": float(predicted_price),
        "price_change": float(price_change),
        "signal": signal,
        "model_metrics": {
            "mse": float(mse),
            "r2_score": float(r2)
        },
        "market_data": {
            "high_24h": float(market_data['high_24h']),
            "low_24h": float(market_data['low_24h']),
            "price_change_percent": float(market_data['price_change_percent']),
            "volume_24h": float(market_data['volume_24h']),
            "volume_change_percent": float(market_data.get('volume_change_percent', 0)),
            "market_cap": float(market_data['market_cap'])
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return result

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("🧠 MODÈLE IA DE PRÉDICTION CRYPTO")
    print(f"{'='*60}")
    
    result = train_and_predict()
    
    if result:
        print(f"\n{'='*60}")
        print("✅ PRÉDICTION TERMINÉE")
        print(f"{'='*60}\n")
        
        # Afficher le résultat JSON
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ Échec de la prédiction")
        exit(1)
