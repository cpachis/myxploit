#!/usr/bin/env python3
"""
Script simple pour vérifier PostgreSQL sur Render
"""

import os
from sqlalchemy import create_engine, text

def check_render_simple():
    """Vérifier PostgreSQL sur Render avec URL complète"""
    
    # URL PostgreSQL de Render
    database_url = "postgresql://myxploit_user:HqTbUT77VkyqtlVHSMJPTWTjeLX9xTYs@dpg-d2m55nbipnbc738t8etg-a.frankfurt-postgres.render.com/myxploit"
    
    print(f"🔍 Connexion à PostgreSQL sur Render...")
    print(f"URL: {database_url[:50]}...")
    
    try:
        # Créer la connexion
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Vérifier la connexion
            result = conn.execute(text("SELECT 1"))
            print("✅ Connexion à PostgreSQL réussie")
            
            # Lister les tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tables disponibles: {tables}")
            
            # Vérifier la table transports
            if 'transports' in tables:
                print("\n🚛 === TABLE TRANSPORTS ===")
                
                # Compter les transports
                result = conn.execute(text("SELECT COUNT(*) FROM transports"))
                count = result.fetchone()[0]
                print(f"📊 Nombre total de transports: {count}")
                
                if count > 0:
                    # Afficher tous les transports
                    result = conn.execute(text("""
                        SELECT id, ref, date, lieu_collecte, lieu_livraison, 
                               poids_tonnes, distance_km, emis_kg, emis_tkm,
                               niveau_calcul, type_vehicule, energie, conso_vehicule,
                               vehicule_dedie, client, type_transport
                        FROM transports 
                        ORDER BY id DESC
                    """))
                    transports = result.fetchall()
                    
                    print(f"\n📋 Détails des {len(transports)} transports:")
                    for i, transport in enumerate(transports, 1):
                        print(f"\n  🚛 Transport #{i} (ID: {transport[0]})")
                        print(f"     Référence: {transport[1]}")
                        print(f"     Date: {transport[2]}")
                        print(f"     Collecte: {transport[3]}")
                        print(f"     Livraison: {transport[4]}")
                        print(f"     Poids: {transport[5]} tonnes")
                        print(f"     Distance: {transport[6]} km")
                        print(f"     Émissions: {transport[7]} kg CO₂e")
                        print(f"     Émissions/t.km: {transport[8]} kg CO₂e/t.km")
                        print(f"     Niveau: {transport[9]}")
                        print(f"     Type véhicule: {transport[10]}")
                        print(f"     Énergie: {transport[11]}")
                        print(f"     Consommation: {transport[12]} L/100km")
                        print(f"     Véhicule dédié: {transport[13]}")
                        print(f"     Client: {transport[14]}")
                        print(f"     Type transport: {transport[15]}")
                else:
                    print("❌ Aucun transport trouvé dans la base de données PostgreSQL")
            else:
                print("❌ Table 'transports' non trouvée")
            
            print("\n✅ Vérification terminée avec succès")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Vérification des données PostgreSQL sur Render...")
    print("=" * 60)
    success = check_render_simple()
    print("=" * 60)
    if success:
        print("🎉 Vérification terminée avec succès !")
    else:
        print("❌ Erreur lors de la vérification")
