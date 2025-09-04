#!/usr/bin/env python3
"""
Script temporaire pour ajouter le champ vehicule_dedie à la table transports
À exécuter une seule fois sur Render
"""

import os
import sys
from sqlalchemy import create_engine, text

def add_vehicule_dedie_column():
    """Ajoute le champ vehicule_dedie à la table transports"""
    try:
        # Récupérer l'URL de la base de données depuis les variables d'environnement
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("❌ Variable d'environnement DATABASE_URL non trouvée")
            return False
        
        # Créer la connexion à la base de données
        engine = create_engine(database_url)
        
        # Vérifier si la colonne existe déjà
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' 
                AND column_name = 'vehicule_dedie'
            """))
            
            if result.fetchone():
                print("✅ La colonne 'vehicule_dedie' existe déjà")
                return True
        
        # Ajouter la colonne
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE transports 
                ADD COLUMN vehicule_dedie BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            
        print("✅ Colonne 'vehicule_dedie' ajoutée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Ajout de la colonne vehicule_dedie...")
    success = add_vehicule_dedie_column()
    
    if success:
        print("🎉 Migration terminée avec succès!")
        sys.exit(0)
    else:
        print("💥 Échec de la migration")
        sys.exit(1)
