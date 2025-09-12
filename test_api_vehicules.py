#!/usr/bin/env python3
"""
Script pour tester l'API des véhicules
"""

import requests
import json

def test_api_vehicules():
    """Tester l'API des véhicules"""
    base_url = "https://myxploit-transports.onrender.com"
    
    print("=== TEST API VÉHICULES ===")
    
    # Test API types de véhicules
    try:
        print("\n1. Test /api/vehicules/types")
        response = requests.get(f"{base_url}/api/vehicules/types", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Types véhicules: {len(data.get('types_vehicules', []))}")
            if data.get('types_vehicules'):
                print("Premier véhicule:", data['types_vehicules'][0])
        else:
            print(f"Erreur: {response.text}")
            
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test API véhicules
    try:
        print("\n2. Test /api/vehicules")
        response = requests.get(f"{base_url}/api/vehicules", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Véhicules: {len(data.get('vehicules', []))}")
            if data.get('vehicules'):
                print("Premier véhicule:", data['vehicules'][0])
        else:
            print(f"Erreur: {response.text}")
            
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test API énergies
    try:
        print("\n3. Test /api/energies")
        response = requests.get(f"{base_url}/api/energies", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Énergies: {len(data.get('energies', []))}")
            if data.get('energies'):
                print("Première énergie:", data['energies'][0])
        else:
            print(f"Erreur: {response.text}")
            
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_api_vehicules()
