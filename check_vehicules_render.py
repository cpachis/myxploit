#!/usr/bin/env python3
"""
Script pour vérifier les véhicules dans PostgreSQL sur Render
"""

import psycopg2
import os

def check_vehicules_render():
    """Vérifier les véhicules dans PostgreSQL sur Render"""
    
    # URL de connexion PostgreSQL sur Render
    DATABASE_URL = "postgresql://myxploit_user:HqTbUT77VkyqtlVHSMJPTWTjeLX9xTYs@dpg-d2m55nbipnbc738t8etg-a/myxploit"
    
    try:
        print("🔌 Connexion à PostgreSQL sur Render...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Connexion réussie !")
        
        # Vérifier la structure de la table vehicules
        print("\n📋 Structure de la table vehicules :")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'vehicules' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Compter les véhicules
        print("\n🚛 Nombre de véhicules en base :")
        cursor.execute("SELECT COUNT(*) FROM vehicules")
        count = cursor.fetchone()[0]
        print(f"  Total: {count} véhicules")
        
        if count > 0:
            print("\n📋 Liste des véhicules :")
            cursor.execute("""
                SELECT id, nom, type, consommation, emissions, charge_utile, created_at
                FROM vehicules 
                ORDER BY nom
            """)
            
            vehicules = cursor.fetchall()
            for i, vehicule in enumerate(vehicules, 1):
                print(f"\n  🚛 Véhicule #{i} (ID: {vehicule[0]})")
                print(f"     Nom: {vehicule[1]}")
                print(f"     Type: {vehicule[2]}")
                print(f"     Consommation: {vehicule[3]} L/100km")
                print(f"     Émissions: {vehicule[4]} g CO₂e/t.km")
                print(f"     Charge utile: {vehicule[5]} tonnes")
                print(f"     Créé le: {vehicule[6]}")
        else:
            print("\n❌ Aucun véhicule trouvé dans la base de données")
            
        # Vérifier aussi les énergies
        print("\n⚡ Nombre d'énergies en base :")
        cursor.execute("SELECT COUNT(*) FROM energies")
        count_energies = cursor.fetchone()[0]
        print(f"  Total: {count_energies} énergies")
        
        if count_energies > 0:
            print("\n📋 Liste des énergies :")
            cursor.execute("""
                SELECT id, nom, unite, facteur
                FROM energies 
                ORDER BY nom
            """)
            
            energies = cursor.fetchall()
            for i, energie in enumerate(energies, 1):
                print(f"\n  ⚡ Énergie #{i} (ID: {energie[0]})")
                print(f"     Nom: {energie[1]}")
                print(f"     Unité: {energie[2]}")
                print(f"     Facteur: {energie[3]} kg CO₂e/L")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Vérification terminée !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_vehicules_render()
