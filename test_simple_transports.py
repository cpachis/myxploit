#!/usr/bin/env python3
"""
Script de test pour les transports simplifiés
"""

import json
import os

def test_transports_simple():
    """Teste le chargement des transports simplifiés"""
    
    # Chemin vers le fichier de données
    data_dir = 'data'
    transports_file = os.path.join(data_dir, 'transports_simple.json')
    
    print("🧪 Test des transports simplifiés")
    print("=" * 40)
    
    # Vérifier que le fichier existe
    if not os.path.exists(transports_file):
        print(f"❌ Fichier {transports_file} non trouvé")
        return False
    
    print(f"✅ Fichier {transports_file} trouvé")
    
    # Charger les données
    try:
        with open(transports_file, 'r', encoding='utf-8') as f:
            transports = json.load(f)
        print(f"✅ Données chargées avec succès: {len(transports)} transports")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return False
    
    # Vérifier la structure des données
    print("\n📋 Structure des transports:")
    for ref, transport in transports.items():
        print(f"\n🚛 {ref}:")
        required_fields = ['client', 'ville_depart', 'ville_arrivee', 'distance_km', 'energie', 'poids_tonnes', 'date']
        
        for field in required_fields:
            if field in transport:
                value = transport[field]
                print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: MANQUANT")
        
        # Vérifier les émissions
        if 'emis_kg' in transport and 'emis_tkm' in transport:
            print(f"  ✅ émissions: {transport['emis_kg']} kg CO₂e, {transport['emis_tkm']} kg CO₂e/t.km")
        else:
            print(f"  ⚠️  émissions: MANQUANTES")
    
    print("\n🎯 Test terminé avec succès!")
    return True

if __name__ == "__main__":
    test_transports_simple()












