import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json
import sys

def load_and_prepare_data(coin_id='bitcoin'):
    """
    Charge les données du CSV et prépare les features
    
    Args:
        coin_id (str): ID de la crypto
    """
    try:
        # Lecture du fichier CSV spécifique à la crypto
        filename = f'market_data_{coin_id}.csv'
        df = pd.read_csv(filename)
        
        # Feature Engineering: Créer des features à partir des prix et volumes précédents
        df['prev_price'] = df['price'].shift(1)
        df['prev_volume'] = df['volume'].shift(1)
        df['price_change'] = df['price'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        
        # Supprimer les lignes avec NaN résultant du shift
        df = df.dropna()
        
        return df
        
    except FileNotFoundError:
        print(json.dumps({
            "error": f"Fichier {filename} introuvable. Exécutez d'abord collect_data.py pour {coin_id}"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Erreur lors du chargement des données: {str(e)}"}))
        sys.exit(1)

def train_model(df):
    """
    Entraîne le modèle de régression linéaire
    """
    # Définir les features (X) et la cible (y)
    X = df[['prev_price', 'prev_volume', 'price_change', 'volume_change']]
    y = df['price']
    
    # Division des données (80% entraînement, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Créer et entraîner le modèle
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Évaluation du modèle
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    return model, mse, r2, X_test, y_test, y_pred

def predict_price(coin_id, latest_price, latest_volume, price_change, volume_change):
    """
    Fait une prédiction basée sur les dernières données
    
    Args:
        coin_id (str): ID de la crypto
        latest_price (float): Prix actuel
        latest_volume (float): Volume actuel
        price_change (float): Changement de prix (décimal)
        volume_change (float): Changement de volume (décimal)
    """
    # Charger et préparer les données
    df = load_and_prepare_data(coin_id)
    
    # Entraîner le modèle
    model, mse, r2, _, _, _ = train_model(df)
    
    # Faire la prédiction
    features = np.array([[latest_price, latest_volume, price_change, volume_change]])
    predicted_price = model.predict(features)[0]
    
    # Retourner le résultat en JSON
    result = {
        "coin_id": coin_id,
        "current_price": latest_price,
        "predicted_price": predicted_price,
        "price_change_pct": ((predicted_price - latest_price) / latest_price) * 100,
        "model_metrics": {
            "mse": mse,
            "r2_score": r2
        }
    }
    
    return result

if __name__ == "__main__":
    # Si des arguments sont passés (pour l'API)
    if len(sys.argv) > 5:
        try:
            coin_id = sys.argv[1]
            latest_price = float(sys.argv[2])
            latest_volume = float(sys.argv[3])
            price_change = float(sys.argv[4])
            volume_change = float(sys.argv[5])
            
            result = predict_price(coin_id, latest_price, latest_volume, price_change, volume_change)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        print(json.dumps({"error": "Usage: python ai_model.py <coin_id> <price> <volume> <price_change> <volume_change>"}))
