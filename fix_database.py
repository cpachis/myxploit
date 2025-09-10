#!/usr/bin/env python3
"""
Script pour forcer la création des colonnes manquantes dans la base de données
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def force_migration():
    """Forcer la migration des colonnes manquantes"""
    
    # Configuration de la base de données
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non définie")
        return False
    
    print(f"🔍 URL de la base de données: {database_url}")
    
    try:
        # Créer la connexion
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Connexion à la base de données réussie")
            
            # Vérifier si la table energies existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'energies'
                )
            """))
            
            if not result.fetchone()[0]:
                print("❌ Table 'energies' n'existe pas")
                return False
            
            print("✅ Table 'energies' trouvée")
            
            # Forcer l'ajout des colonnes manquantes
            print("\n🔄 Ajout des colonnes manquantes...")
            
            # Colonne phase_amont
            try:
                conn.execute(text("ALTER TABLE energies ADD COLUMN phase_amont FLOAT DEFAULT 0.0"))
                print("✅ Colonne 'phase_amont' ajoutée")
            except SQLAlchemyError as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne 'phase_amont' existe déjà")
                else:
                    print(f"⚠️ Erreur avec phase_amont: {str(e)}")
            
            # Colonne phase_fonctionnement
            try:
                conn.execute(text("ALTER TABLE energies ADD COLUMN phase_fonctionnement FLOAT DEFAULT 0.0"))
                print("✅ Colonne 'phase_fonctionnement' ajoutée")
            except SQLAlchemyError as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne 'phase_fonctionnement' existe déjà")
                else:
                    print(f"⚠️ Erreur avec phase_fonctionnement: {str(e)}")
            
            # Colonne donnees_supplementaires
            try:
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE energies ADD COLUMN donnees_supplementaires JSONB DEFAULT '{}'"))
                else:
                    conn.execute(text("ALTER TABLE energies ADD COLUMN donnees_supplementaires TEXT DEFAULT '{}'"))
                print("✅ Colonne 'donnees_supplementaires' ajoutée")
            except SQLAlchemyError as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ Colonne 'donnees_supplementaires' existe déjà")
                else:
                    print(f"⚠️ Erreur avec donnees_supplementaires: {str(e)}")
            
            # Valider les changements
            conn.commit()
            print("\n🎉 Migration forcée terminée avec succès")
            
            # Vérifier le résultat
            print("\n🔍 Vérification de la structure...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'energies'
                ORDER BY ordinal_position
            """))
            
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2],
                    'default': row[3]
                })
            
            print(f"📋 Structure finale de la table 'energies' ({len(columns)} colonnes):")
            for col in columns:
                print(f"   - {col['name']}: {col['type']} (nullable: {col['nullable']}, default: {col['default']})")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Migration forcée de la base de données MyXploit")
    print("=" * 50)
    
    if force_migration():
        print("\n✅ Migration réussie ! L'application devrait maintenant fonctionner correctement.")
    else:
        print("\n❌ Migration échouée. Vérifiez les logs pour plus de détails.")







