#!/usr/bin/env python3
"""
Script pour tester l'API sur Render
"""

import requests
import json

def test_api_render():
    """Tester l'API sur Render"""
    
    base_url = "https://myxploit-transports.onrender.com"
    
    print("🧪 Test des APIs sur Render")
    print("=" * 50)
    
    # Test API véhicules
    print("\n🚛 Test API véhicules :")
    try:
        response = requests.get(f"{base_url}/api/vehicules", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            print(f"Nombre de véhicules: {len(data.get('vehicules', []))}")
            
            if data.get('vehicules'):
                print("\nVéhicules trouvés :")
                for i, vehicule in enumerate(data['vehicules'], 1):
                    print(f"  {i}. {vehicule.get('nom')} ({vehicule.get('type')})")
            else:
                print("❌ Aucun véhicule trouvé")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test API types de véhicules
    print("\n🚛 Test API types de véhicules :")
    try:
        response = requests.get(f"{base_url}/api/vehicules/types", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            print(f"Nombre de types: {len(data.get('types_vehicules', []))}")
            
            if data.get('types_vehicules'):
                print("\nTypes de véhicules trouvés :")
                for i, type_veh in enumerate(data['types_vehicules'], 1):
                    print(f"  {i}. {type_veh.get('nom')} - {type_veh.get('consommation_base')} L/100km")
            else:
                print("❌ Aucun type de véhicule trouvé")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test API énergies
    print("\n⚡ Test API énergies :")
    try:
        response = requests.get(f"{base_url}/api/energies", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            print(f"Nombre d'énergies: {len(data.get('energies', []))}")
            
            if data.get('energies'):
                print("\nÉnergies trouvées :")
                for i, energie in enumerate(data['energies'], 1):
                    print(f"  {i}. {energie.get('nom')} - {energie.get('facteur_emission')} kg CO₂e/L")
            else:
                print("❌ Aucune énergie trouvée")
        else:
            print(f"❌ Erreur HTTP: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_api_render()
