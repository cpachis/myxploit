#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état de la base de données
"""

import os
import sqlite3
from datetime import datetime

def check_database():
    """Vérifier l'état de la base de données"""
    print("🔍 DIAGNOSTIC DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    print("\n📋 Variables d'environnement:")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'non défini')}")
    print(f"DEV_DATABASE_URL: {os.environ.get('DEV_DATABASE_URL', 'non défini')}")
    print(f"SQLALCHEMY_DATABASE_URI: {os.environ.get('SQLALCHEMY_DATABASE_URI', 'non défini')}")
    
    # Vérifier les fichiers de base de données
    print("\n📁 Fichiers de base de données:")
    db_files = [
        'myxploit_dev.db',
        'myxploit_test.db',
        'instance/myxploit_dev.db',
        'instance/myxploit_test.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(db_file))
            print(f"✅ {db_file}: {size} octets, modifié le {mtime}")
        else:
            print(f"❌ {db_file}: N'existe pas")
    
    # Vérifier le contenu de la base de données principale
    print("\n🗄️ Contenu de la base de données principale:")
    main_db = 'instance/myxploit_dev.db'
    
    if os.path.exists(main_db):
        try:
            conn = sqlite3.connect(main_db)
            cursor = conn.cursor()
            
            # Lister les tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables trouvées: {[table[0] for table in tables]}")
            
            # Compter les enregistrements
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} enregistrements")
                
                # Afficher quelques exemples pour les tables importantes
                if table_name in ['energies', 'transports', 'vehicules'] and count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    rows = cursor.fetchall()
                    print(f"    Exemples: {len(rows)} lignes")
            
            conn.close()
            print("✅ Connexion à la base de données réussie")
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture de la base: {e}")
    else:
        print("❌ Base de données principale non trouvée")
    
    print("\n" + "=" * 50)
    print("🔍 DIAGNOSTIC TERMINÉ")

if __name__ == "__main__":
    check_database()
