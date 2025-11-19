#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage COMPLET du cache
À exécuter sur Render après déploiement
"""

import os
import glob
from datetime import datetime

def nettoyer_tout():
    """Supprime TOUS les fichiers de cache"""
    print("=" * 60)
    print("🧹 NETTOYAGE COMPLET DU CACHE")
    print("=" * 60)
    print()
    
    # Types de fichiers à supprimer
    patterns = [
        "cache_*.json",           # Cache des données crypto individuelles
        "data_*.json",            # Fichiers de données
        "crypto_list_cache.json"  # Cache de la liste des 250 cryptos
    ]
    
    fichiers_supprimes = []
    
    for pattern in patterns:
        fichiers = glob.glob(pattern)
        for fichier in fichiers:
            try:
                # Afficher l'âge du fichier
                mtime = os.path.getmtime(fichier)
                age = (datetime.now().timestamp() - mtime) / 60  # en minutes
                
                print(f"🗑️  Suppression: {fichier}")
                print(f"   Âge: {age:.1f} minutes")
                
                os.remove(fichier)
                fichiers_supprimes.append(fichier)
                print(f"   ✅ Supprimé!")
                
            except Exception as e:
                print(f"   ❌ Erreur: {str(e)}")
            
            print()
    
    print("=" * 60)
    if fichiers_supprimes:
        print(f"✅ NETTOYAGE TERMINÉ!")
        print(f"📊 {len(fichiers_supprimes)} fichier(s) supprimé(s)")
    else:
        print("✅ Aucun fichier à nettoyer")
    print("=" * 60)
    print()
    print("💡 Actions recommandées:")
    print("1. Redémarrer le serveur")
    print("2. Appeler POST /api/crypto-list/refresh")
    print("3. Tester une prédiction")
    print()

if __name__ == "__main__":
    nettoyer_tout()
