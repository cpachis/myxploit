#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état de la base de données
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

def check_database():
    """Vérifier l'état de la base de données"""
    
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
            # Vérifier la connexion
            result = conn.execute(text("SELECT 1"))
            print("✅ Connexion à la base de données réussie")
            
            # Lister les tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables disponibles: {tables}")
            
            if 'energies' in tables:
                print("✅ Table 'energies' trouvée")
                
                # Vérifier les colonnes de la table energies
                columns = inspector.get_columns('energies')
                column_names = [col['name'] for col in columns]
                print(f"📊 Colonnes de la table 'energies': {column_names}")
                
                # Vérifier les colonnes spécifiques
                required_columns = ['phase_amont', 'phase_fonctionnement', 'donnees_supplementaires']
                for col in required_columns:
                    if col in column_names:
                        print(f"✅ Colonne '{col}' présente")
                    else:
                        print(f"❌ Colonne '{col}' manquante")
                
                # Compter les enregistrements
                result = conn.execute(text("SELECT COUNT(*) FROM energies"))
                count = result.fetchone()[0]
                print(f"📈 Nombre d'énergies enregistrées: {count}")
                
                # Afficher un exemple d'énergie
                if count > 0:
                    result = conn.execute(text("SELECT * FROM energies LIMIT 1"))
                    energie = result.fetchone()
                    print(f"📝 Exemple d'énergie: {energie}")
                
            else:
                print("❌ Table 'energies' non trouvée")
                
    except SQLAlchemyError as e:
        print(f"❌ Erreur de base de données: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
        return False
    
    return True

def create_missing_columns():
    """Créer les colonnes manquantes"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non définie")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Vérifier si les colonnes existent
            inspector = inspect(engine)
            columns = inspector.get_columns('energies')
            column_names = [col['name'] for col in columns]
            
            # Ajouter les colonnes manquantes
            if 'phase_amont' not in column_names:
                print("➕ Ajout de la colonne 'phase_amont'...")
                conn.execute(text("ALTER TABLE energies ADD COLUMN phase_amont FLOAT DEFAULT 0.0"))
                print("✅ Colonne 'phase_amont' ajoutée")
            
            if 'phase_fonctionnement' not in column_names:
                print("➕ Ajout de la colonne 'phase_fonctionnement'...")
                conn.execute(text("ALTER TABLE energies ADD COLUMN phase_fonctionnement FLOAT DEFAULT 0.0"))
                print("✅ Colonne 'phase_fonctionnement' ajoutée")
            
            if 'donnees_supplementaires' not in column_names:
                print("➕ Ajout de la colonne 'donnees_supplementaires'...")
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE energies ADD COLUMN donnees_supplementaires JSONB DEFAULT '{}'"))
                else:
                    conn.execute(text("ALTER TABLE energies ADD COLUMN donnees_supplementaires TEXT DEFAULT '{}'"))
                print("✅ Colonne 'donnees_supplementaires' ajoutée")
            
            conn.commit()
            print("🎉 Migration terminée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Diagnostic de la base de données MyXploit")
    print("=" * 50)
    
    # Vérifier l'état actuel
    if check_database():
        print("\n🔧 Voulez-vous créer les colonnes manquantes ? (y/n)")
        response = input().lower()
        
        if response == 'y':
            print("\n🔄 Création des colonnes manquantes...")
            create_missing_columns()
            print("\n🔍 Vérification finale...")
            check_database()
    else:
        print("❌ Impossible de diagnostiquer la base de données")
