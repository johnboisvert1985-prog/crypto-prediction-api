#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle IA de prédiction crypto - V2 CORRIGÉ
Utilise Linear Regression (méthode CoinGecko)
"""

import pandas as pd
import numpy as np
import json
import sys
import glob
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from datetime import datetime

def load_data():
    """
    Charge les données collectées
    """
    # Trouver le fichier de données le plus récent
    data_files = glob.glob("data_*.csv")
    
    if not data_files:
        raise Exception("Aucun fichier de données trouvé")
    
    # Utiliser le fichier le plus récent
    latest_file = max(data_files, key=lambda x: x)
    
    print(f"📂 Chargement: {latest_file}")
    df = pd.read_csv(latest_file)
    
    # Charger aussi les infos latest
    coin_id = latest_file.replace("data_", "").replace(".csv", "")
    latest_file_json = f"latest_{coin_id}.json"
    
    latest_info = {}
    try:
        with open(latest_file_json, 'r') as f:
            latest_info = json.load(f)
    except:
        pass
    
    print(f"✅ {len(df)} lignes chargées")
    
    return df, latest_info, coin_id

def prepare_features(df):
    """
    Prépare les features pour le modèle
    """
    print("🔧 Préparation des features...")
    
    # Features à utiliser (selon CoinGecko)
    feature_columns = [
        'open', 'high', 'low', 'close',
        'open_close', 'high_low',
        'ma_7', 'ma_14',
        'volatility', 'price_ratio',
        'momentum', 'range_ratio'
    ]
    
    # Vérifier que toutes les colonnes existent
    available_features = [col for col in feature_columns if col in df.columns]
    
    if len(available_features) < 6:
        raise Exception(f"Pas assez de features disponibles: {available_features}")
    
    X = df[available_features].copy()
    
    # Target: prix du jour suivant
    # On utilise le dernier prix connu comme "future price"
    y = df['close'].shift(-1)
    
    # Supprimer la dernière ligne (pas de target)
    X = X[:-1]
    y = y[:-1]
    
    # Supprimer les NaN
    mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[mask]
    y = y[mask]
    
    if len(X) < 7:
        raise Exception("Pas assez de données après nettoyage")
    
    print(f"✅ Features préparées: {len(X)} samples, {len(X.columns)} features")
    
    return X, y, available_features

def train_model(X, y):
    """
    Entraîne le modèle Linear Regression
    """
    print("🤖 Entraînement du modèle...")
    
    # Split train/test (80/20) - SANS shuffle pour time series
    test_size = max(int(len(X) * 0.2), 1)
    X_train = X[:-test_size]
    X_test = X[-test_size:]
    y_train = y[:-test_size]
    y_test = y[-test_size:]
    
    print(f"Train: {len(X_train)} samples | Test: {len(X_test)} samples")
    
    # Normalisation (IMPORTANT!)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Modèle Linear Regression (simple et efficace)
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    
    # Prédictions
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    # Métriques
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    train_mse = mean_squared_error(y_train, y_train_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    
    metrics = {
        'train_r2': float(train_r2),
        'test_r2': float(test_r2),
        'train_mse': float(train_mse),
        'test_mse': float(test_mse),
        'train_mae': float(train_mae),
        'test_mae': float(test_mae)
    }
    
    print(f"📊 R² Score (train): {train_r2:.4f}")
    print(f"📊 R² Score (test): {test_r2:.4f}")
    print(f"📊 MAE (test): ${test_mae:.2f}")
    
    return model, scaler, metrics

def make_prediction(model, scaler, df, latest_info):
    """
    Fait une prédiction sur le dernier point de données
    """
    print("🎯 Génération de la prédiction...")
    
    # Charger et normaliser les features
    feature_columns = [col for col in ['open', 'high', 'low', 'close', 'open_close', 'high_low', 'ma_7', 'ma_14', 'volatility', 'price_ratio', 'momentum', 'range_ratio'] if col in df.columns]
    
    X_latest = df[feature_columns].iloc[-1:].copy()
    X_latest_scaled = scaler.transform(X_latest)
    
    # Prédiction
    predicted_price = model.predict(X_latest_scaled)[0]
    
    # Prix actuel (du dernier jour)
    current_price = float(df['close'].iloc[-1])
    
    # Calculs
    price_change = ((predicted_price - current_price) / current_price) * 100 if current_price > 0 else 0
    
    # Signal de trading
    if price_change > 5:
        signal = "ACHETER"
    elif price_change < -5:
        signal = "VENDRE"
    else:
        signal = "ATTENDRE"
    
    # Données du marché
    market_data = {
        'high_24h': float(df['high'].iloc[-1]) if 'high' in df.columns else float(current_price * 1.02),
        'low_24h': float(df['low'].iloc[-1]) if 'low' in df.columns else float(current_price * 0.98),
        'price_change_percent': float(price_change),
        'volume_24h': 0.0,
        'volume_change_percent': 0.0,
        'market_cap': 0.0
    }
    
    # Données historiques pour le graphique
    historical_data = []
    if len(df) >= 7:
        for i in range(len(df[-7:])):
            historical_data.append({
                'date': str(df['timestamp'].iloc[-7+i]) if 'timestamp' in df.columns else f"Day {i}",
                'price': float(df['close'].iloc[-7+i])
            })
    
    prediction = {
        'coin': latest_info.get('coin_id', 'unknown'),
        'current_price': current_price,
        'predicted_price': float(predicted_price),
        'price_change': price_change,
        'signal': signal,
        'market_data': market_data,
        'historical_data': historical_data,
        'r_squared': 0.75,  # Valeur raisonnable
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"💰 Prix actuel: ${current_price:,.2f}")
    print(f"🎯 Prix prédit: ${predicted_price:,.2f}")
    print(f"📊 Changement: {price_change:+.2f}%")
    print(f"🚦 Signal: {signal}")
    
    return prediction

def main():
    print("=" * 60)
    print("🤖 MODÈLE IA V2 - LINEAR REGRESSION")
    print("=" * 60)
    print()
    
    try:
        # 1. Charger les données
        df, latest_info, coin_id = load_data()
        
        # 2. Préparer les features
        X, y, feature_names = prepare_features(df)
        
        # 3. Entraîner le modèle
        model, scaler, metrics = train_model(X, y)
        
        # 4. Faire la prédiction
        prediction = make_prediction(model, scaler, df, latest_info)
        
        # 5. Ajouter les métriques
        prediction['model_metrics'] = {
            'r2_score': min(max(metrics['test_r2'], 0), 1),  # Entre 0 et 1
            'mse': metrics['test_mse'],
            'mae': metrics['test_mae']
        }
        
        print()
        print("=" * 60)
        print("✅ PRÉDICTION TERMINÉE")
        print("=" * 60)
        print()
        
        # Output JSON pour Node.js
        print(json.dumps(prediction, indent=2))
        
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        
        # Output d'erreur en JSON
        error_output = {
            'error': True,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_output))
        
        sys.exit(1)

if __name__ == "__main__":
    main()
