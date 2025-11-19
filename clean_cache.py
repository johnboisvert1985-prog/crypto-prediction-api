#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage du cache
Utilise ce script pour forcer un rafraîchissement complet des données
"""

import os
import glob
from datetime import datetime

def nettoyer_cache():
    """Supprime tous les fichiers de cache et de données"""
    print("=" * 60)
    print("🧹 NETTOYAGE DU CACHE")
    print("=" * 60)
    print()
    
    # Trouver tous les fichiers de cache et données
    fichiers_a_supprimer = []
    fichiers_a_supprimer.extend(glob.glob("cache_*.json"))
    fichiers_a_supprimer.extend(glob.glob("data_*.json"))
    
    if not fichiers_a_supprimer:
        print("✅ Aucun fichier de cache trouvé!")
        print()
        return
    
    print(f"📋 Fichiers trouvés: {len(fichiers_a_supprimer)}")
    print()
    
    for fichier in fichiers_a_supprimer:
        try:
            # Afficher l'âge du fichier
            mtime = os.path.getmtime(fichier)
            age = (datetime.now().timestamp() - mtime) / 60  # en minutes
            
            print(f"🗑️  Suppression: {fichier}")
            print(f"   Âge: {age:.1f} minutes")
            
            os.remove(fichier)
            print(f"   ✅ Supprimé!")
            
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("✅ NETTOYAGE TERMINÉ!")
    print("=" * 60)
    print()
    print("💡 Les prochaines prédictions téléchargeront des données fraîches!")
    print()

if __name__ == "__main__":
    nettoyer_cache()
