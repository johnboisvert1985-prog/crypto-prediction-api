#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle IA PRO - Gradient Boosting
Prédiction 7 jours avec features avancées
"""

import json
import sys
import glob
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

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
    
    if len(ohlc_data) < 30:
        raise Exception(f"Pas assez de données ({len(ohlc_data)} jours, minimum 30)")
    
    print(f"✅ {len(ohlc_data)} jours chargés")
    return ohlc_data, market_data, coin_id

def calculate_rsi(prices, period=14):
    """Calcule le RSI (Relative Strength Index)"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calcule le MACD"""
    ema_fast = pd.Series(prices).ewm(span=fast).mean().values
    ema_slow = pd.Series(prices).ewm(span=slow).mean().values
    macd = ema_fast - ema_slow
    macd_signal = pd.Series(macd).ewm(span=signal).mean().values
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def prepare_data(ohlc_data):
    """Prépare les données avec features avancées"""
    print("🔧 Préparation des données avec features avancées...")
    
    ohlc = np.array(ohlc_data)
    
    # Extraire OHLCV
    open_prices = ohlc[:, 1]
    high_prices = ohlc[:, 2]
    low_prices = ohlc[:, 3]
    close_prices = ohlc[:, 4]
    
    # Créer DataFrame
    df = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices
    })
    
    # Features techniques
    print("   📊 Calcul des features techniques...")
    
    # 1. Moyennes mobiles
    df['sma_7'] = df['close'].rolling(window=7).mean()
    df['sma_14'] = df['close'].rolling(window=14).mean()
    df['sma_30'] = df['close'].rolling(window=30).mean()
    
    # 2. RSI
    df['rsi'] = calculate_rsi(close_prices, 14)
    
    # 3. MACD
    macd, macd_signal, macd_hist = calculate_macd(close_prices)
    df['macd'] = macd
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist
    
    # 4. Bandes de Bollinger
    sma_20 = df['close'].rolling(window=20).mean()
    std_20 = df['close'].rolling(window=20).std()
    df['bb_upper'] = sma_20 + (std_20 * 2)
    df['bb_lower'] = sma_20 - (std_20 * 2)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # 5. Volatilité
    df['volatility'] = df['close'].pct_change().rolling(window=14).std()
    
    # 6. Momentum
    df['momentum'] = df['close'].pct_change(periods=7)
    
    # 7. ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    df['atr'] = pd.Series(tr).rolling(window=14).mean()
    
    # 8. Changes
    df['price_change_1d'] = df['close'].pct_change(1)
    df['price_change_7d'] = df['close'].pct_change(7)
    
    # Remplir les NaN
    df = df.fillna(method='bfill').fillna(method='ffill')
    
    # Préparer X et y pour PRÉDICTION 7 JOURS
    feature_cols = ['open', 'high', 'low', 'close', 'sma_7', 'sma_14', 'sma_30',
                   'rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower',
                   'bb_width', 'volatility', 'momentum', 'atr', 'price_change_1d', 'price_change_7d']
    
    X = df[feature_cols].values
    
    # y: Prix 7 jours dans le futur (shift de -7)
    y = df['close'].shift(-7).values
    
    # Enlever les derniers jours (pas de target)
    X = X[:-7]
    y = y[:-7]
    
    # Enlever les NaN
    mask = ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) < 30:
        raise Exception(f"Pas assez de samples après préparation ({len(X)}, minimum 30)")
    
    print(f"   ✅ {len(X)} samples, {len(feature_cols)} features")
    print(f"   Prix actuel: ${close_prices[-1]:,.2f}")
    
    return X, y, feature_cols, close_prices, df

def train_model(X, y):
    """Entraîne Gradient Boosting"""
    print("🤖 Entraînement du modèle Gradient Boosting...")
    
    # Split 80/20 (time series - pas de shuffle)
    split_idx = int(len(X) * 0.8)
    
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    
    print(f"   Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Normalisation
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Gradient Boosting (meilleur que Linear Regression!)
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Prédictions
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    # Métriques
    r2_train = r2_score(y_train, y_train_pred)
    r2_test = r2_score(y_test, y_test_pred)
    mape_test = mean_absolute_percentage_error(y_test, y_test_pred)
    mae_test = mean_absolute_error(y_test, y_test_pred)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
    
    print(f"   R² Train: {r2_train:.4f}")
    print(f"   R² Test: {r2_test:.4f}")
    print(f"   MAPE Test: {mape_test:.2f}%")
    print(f"   MAE: ${mae_test:.2f}")
    print(f"   RMSE: ${rmse_test:.2f}")
    
    return model, scaler, {
        'r2_train': r2_train,
        'r2_test': r2_test,
        'mape': mape_test,
        'mae': mae_test,
        'rmse': rmse_test
    }

def make_prediction(model, scaler, X, close_prices, market_data, coin_id, metrics):
    """Prédit 7 jours dans le futur"""
    print("🎯 Génération de la prédiction 7 jours...")
    
    # Utiliser les dernières données
    X_latest = X[-1:, :]
    X_latest_scaled = scaler.transform(X_latest)
    
    predicted_price_7d = float(model.predict(X_latest_scaled)[0])
    
    # Prix actuel
    current_price = float(close_prices[-1])
    
    # S'assurer que la prédiction est raisonnable
    # Limiter à ±15% du prix actuel
    min_pred = current_price * 0.85
    max_pred = current_price * 1.15
    predicted_price_7d = np.clip(predicted_price_7d, min_pred, max_pred)
    
    # Variation
    price_change_7d = ((predicted_price_7d - current_price) / current_price) * 100
    
    # Signal
    if price_change_7d > 5:
        signal = "ACHETER"
    elif price_change_7d < -5:
        signal = "VENDRE"
    else:
        signal = "ATTENDRE"
    
    # Données historiques
    historical_data = []
    for i, price in enumerate(close_prices[-7:]):
        historical_data.append({
            'day': i - 7 + 1,
            'price': float(price)
        })
    
    # Ajouter la prédiction (jour 7)
    historical_data.append({
        'day': 7,
        'price': float(predicted_price_7d)
    })
    
    # Confiance basée sur R² test
    confidence = max(0, min(1, metrics['r2_test']))
    
    prediction = {
        'coin': coin_id,
        'current_price': current_price,
        'predicted_price': predicted_price_7d,
        'price_change': price_change_7d,
        'timeframe': '7 days',
        'signal': signal,
        'market_data': {
            'high_24h': float(market_data.get('high_24h', current_price * 1.05)),
            'low_24h': float(market_data.get('low_24h', current_price * 0.95)),
            'price_change_percent': float(market_data.get('price_change_percentage_24h', 0)),
            'market_cap': float(market_data.get('market_cap', 0) or 0)
        },
        'historical_data': historical_data,
        'r_squared': confidence,
        'model_type': 'Gradient Boosting',
        'features_count': 19,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"   💰 Prix actuel: ${current_price:,.2f}")
    print(f"   🎯 Prix dans 7 jours: ${predicted_price_7d:,.2f}")
    print(f"   📊 Variation: {price_change_7d:+.2f}%")
    print(f"   🚦 Signal: {signal}")
    print(f"   📈 Confiance: {confidence*100:.1f}%")
    
    return prediction

def main():
    print("=" * 60)
    print("🤖 MODÈLE IA PRO - Gradient Boosting")
    print("=" * 60)
    print()
    
    try:
        ohlc_data, market_data, coin_id = load_data()
        X, y, feature_cols, close_prices, df = prepare_data(ohlc_data)
        model, scaler, metrics = train_model(X, y)
        prediction = make_prediction(model, scaler, X, close_prices, market_data, coin_id, metrics)
        
        prediction['model_metrics'] = {
            'r2_score': metrics['r2_test'],
            'mape': metrics['mape'],
            'mae': metrics['mae'],
            'rmse': metrics['rmse']
        }
        
        print()
        print("=" * 60)
        print("✅ PRÉDICTION TERMINÉE")
        print("=" * 60)
        print()
        
        print(json.dumps(prediction, indent=2))
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        print()
        
        print(json.dumps({
            'error': True,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }))
        
        sys.exit(1)

if __name__ == "__main__":
    main()
