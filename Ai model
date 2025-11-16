import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json
import sys

def load_and_prepare_data():
    """
    Charge les données du CSV et prépare les features
    """
    try:
        # Lecture du fichier CSV
        df = pd.read_csv('market_data.csv')
        
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
            "error": "Fichier market_data.csv introuvable. Exécutez d'abord collect_data.py"
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

def predict_price(latest_price, latest_volume, price_change, volume_change):
    """
    Fait une prédiction basée sur les dernières données
    """
    # Charger et préparer les données
    df = load_and_prepare_data()
    
    # Entraîner le modèle
    model, mse, r2, _, _, _ = train_model(df)
    
    # Faire la prédiction
    features = np.array([[latest_price, latest_volume, price_change, volume_change]])
    predicted_price = model.predict(features)[0]
    
    # Retourner le résultat en JSON
    result = {
        "current_price": latest_price,
        "predicted_price": predicted_price,
        "price_change_pct": ((predicted_price - latest_price) / latest_price) * 100,
        "model_metrics": {
            "mse": mse,
            "r2_score": r2
        }
    }
    
    return result

def main():
    """
    Fonction principale pour entraîner et évaluer le modèle
    """
    print("🤖 Chargement des données...")
    df = load_and_prepare_data()
    
    print(f"📊 Données chargées: {len(df)} points")
    
    print("\n🧠 Entraînement du modèle de régression linéaire...")
    model, mse, r2, X_test, y_test, y_pred = train_model(df)
    
    print(f"\n📈 Résultats du modèle:")
    print(f"   - MSE (Mean Squared Error): ${mse:,.2f}")
    print(f"   - R² Score: {r2:.4f}")
    print(f"   - Précision: {r2*100:.2f}%")
    
    # Prédiction avec les dernières données
    latest_data = df.iloc[-1]
    
    print(f"\n🔮 Prédiction basée sur les dernières données:")
    print(f"   - Prix actuel: ${latest_data['price']:,.2f}")
    print(f"   - Volume actuel: ${latest_data['volume']:,.0f}")
    
    prediction = predict_price(
        latest_data['prev_price'],
        latest_data['prev_volume'],
        latest_data['price_change'],
        latest_data['volume_change']
    )
    
    print(f"\n💡 Prédiction du prochain prix: ${prediction['predicted_price']:,.2f}")
    print(f"   - Changement prédit: {prediction['price_change_pct']:+.2f}%")
    
    if prediction['price_change_pct'] > 1:
        print(f"   - Signal: 🟢 ACHAT (hausse prédite > 1%)")
    elif prediction['price_change_pct'] < -1:
        print(f"   - Signal: 🔴 VENTE (baisse prédite > 1%)")
    else:
        print(f"   - Signal: 🟡 HOLD (mouvement < 1%)")

if __name__ == "__main__":
    # Si des arguments sont passés (pour l'API)
    if len(sys.argv) > 1:
        try:
            latest_price = float(sys.argv[1])
            latest_volume = float(sys.argv[2])
            price_change = float(sys.argv[3])
            volume_change = float(sys.argv[4])
            
            result = predict_price(latest_price, latest_volume, price_change, volume_change)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        # Mode interactif
        main()
