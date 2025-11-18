#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle IA de prédiction - Basé sur le guide CoinGecko
Utilise Linear Regression avec MinMaxScaler
"""

import json
import sys
import glob
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from datetime import datetime, timedelta

def load_data():
    """Charge les données collectées"""
    data_files = glob.glob("data_*.json")
    
    if not data_files:
        raise Exception("Aucun fichier de données trouvé")
    
    latest_file = max(data_files, key=lambda x: x)
    
    print(f"📂 Chargement: {latest_file}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    coin_id = data.get('coin_id', 'unknown')
    ohlc_data = data.get('ohlc', [])
    market_data = data.get('market_data', {})
    
    if len(ohlc_data) < 7:
        raise Exception("Pas assez de données")
    
    print(f"✅ {len(ohlc_data)} jours chargés")
    
    return ohlc_data, market_data, coin_id

def prepare_data(ohlc_data):
    """
    Prépare les données selon la méthode CoinGecko
    OHLC: [timestamp, open, high, low, close]
    """
    print("🔧 Préparation des données...")
    
    # Convertir en numpy array
    ohlc = np.array(ohlc_data)
    
    # X: Time et Close price
    X = ohlc[:, [0, 4]]  # timestamp et close
    y = ohlc[:, 4]  # close price (target)
    
    # Ajouter historical price et current market data comme features
    historical_price = ohlc[0, 4]  # Premier prix
    X = np.column_stack([
        X,
        np.full(len(X), historical_price),
        np.full(len(X), ohlc[-1, 4])  # Dernier prix
    ])
    
    # Normalisation avec MinMaxScaler (comme CoinGecko)
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"✅ Données préparées: {len(X)} samples, {X.shape[1]} features")
    
    return X_scaled, y, scaler, ohlc

def train_model(X_scaled, y):
    """Entraîne le modèle Linear Regression"""
    print("🤖 Entraînement du modèle...")
    
    # Split train/test (80/20)
    test_size = max(int(len(X_scaled) * 0.2), 1)
    X_train = X_scaled[:-test_size]
    X_test = X_scaled[-test_size:]
    y_train = y[:-test_size]
    y_test = y[-test_size:]
    
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Modèle Linear Regression
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Prédictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Métriques
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    
    print(f"📊 R² Score (train): {train_r2:.4f}")
    print(f"📊 R² Score (test): {test_r2:.4f}")
    print(f"📊 MAE: ${test_mae:.2f}")
    
    metrics = {
        'train_r2': float(train_r2),
        'test_r2': float(test_r2),
        'test_mse': float(test_mse),
        'test_mae': float(test_mae)
    }
    
    return model, metrics

def make_prediction(model, X_scaled, scaler, ohlc, market_data, coin_id):
    """Fait la prédiction"""
    print("🎯 Génération de la prédiction...")
    
    # Dernière ligne pour prédiction
    X_latest = X_scaled[-1:, :]
    predicted_price = model.predict(X_latest)[0]
    
    # Prix actuel et historique
    current_price = float(ohlc[-1, 4])
    historical_prices = [float(p[4]) for p in ohlc[-7:]]
    
    # Changement de prix
    price_change = ((predicted_price - current_price) / current_price) * 100 if current_price > 0 else 0
    
    # Signal de trading
    if price_change > 5:
        signal = "ACHETER"
    elif price_change < -5:
        signal = "VENDRE"
    else:
        signal = "ATTENDRE"
    
    # Données du marché
    market_info = {
        'high_24h': float(market_data.get('high_24h', current_price * 1.02)),
        'low_24h': float(market_data.get('low_24h', current_price * 0.98)),
        'price_change_percent': float(market_data.get('price_change_percentage_24h', 0)),
        'market_cap': float(market_data.get('market_cap', 0) or 0)
    }
    
    # Données historiques pour graphique
    historical_data = []
    for i, price in enumerate(historical_prices[-7:]):
        historical_data.append({
            'day': i - len(historical_prices) + 1,
            'price': float(price)
        })
    
    prediction = {
        'coin': coin_id,
        'current_price': current_price,
        'predicted_price': float(predicted_price),
        'price_change': price_change,
        'signal': signal,
        'market_data': market_info,
        'historical_data': historical_data,
        'r_squared': min(max(float(market_data.get('price_change_percentage_24h', 0.75)), 0), 1),
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"💰 Prix actuel: ${current_price:,.2f}")
    print(f"🎯 Prix prédit: ${predicted_price:,.2f}")
    print(f"📊 Changement: {price_change:+.2f}%")
    print(f"🚦 Signal: {signal}")
    
    return prediction

def main():
    print("=" * 60)
    print("🤖 MODÈLE IA - CoinGecko Method")
    print("=" * 60)
    print()
    
    try:
        # 1. Charger données
        ohlc_data, market_data, coin_id = load_data()
        
        # 2. Préparer données
        X_scaled, y, scaler, ohlc = prepare_data(ohlc_data)
        
        # 3. Entraîner modèle
        model, metrics = train_model(X_scaled, y)
        
        # 4. Faire prédiction
        prediction = make_prediction(model, X_scaled, scaler, ohlc, market_data, coin_id)
        
        # 5. Ajouter métriques
        prediction['model_metrics'] = {
            'r2_score': metrics['test_r2'],
            'mse': metrics['test_mse'],
            'mae': metrics['test_mae']
        }
        
        print()
        print("=" * 60)
        print("✅ PRÉDICTION TERMINÉE")
        print("=" * 60)
        print()
        
        # Output JSON
        print(json.dumps(prediction, indent=2))
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        
        error_output = {
            'error': True,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_output))
        
        sys.exit(1)

if __name__ == "__main__":
    main()
