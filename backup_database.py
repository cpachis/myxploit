#!/usr/bin/env python3
"""
Script de sauvegarde et restauration de la base de données
"""

import os
import shutil
import sqlite3
from datetime import datetime

def backup_database():
    """Sauvegarder la base de données"""
    print("💾 SAUVEGARDE DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Déterminer le fichier source
    source_db = 'instance/myxploit_dev.db'
    
    if not os.path.exists(source_db):
        print(f"❌ Base de données source non trouvée: {source_db}")
        return False
    
    # Créer le nom de sauvegarde avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = 'backups'
    backup_file = f"{backup_dir}/myxploit_dev_backup_{timestamp}.db"
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Copier le fichier
        shutil.copy2(source_db, backup_file)
        
        # Vérifier la sauvegarde
        if os.path.exists(backup_file):
            source_size = os.path.getsize(source_db)
            backup_size = os.path.getsize(backup_file)
            
            print(f"✅ Sauvegarde créée: {backup_file}")
            print(f"   Taille source: {source_size} octets")
            print(f"   Taille sauvegarde: {backup_size} octets")
            
            if source_size == backup_size:
                print("✅ Sauvegarde vérifiée avec succès")
                return True
            else:
                print("❌ Erreur: Tailles différentes")
                return False
        else:
            print("❌ Erreur: Fichier de sauvegarde non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def restore_database(backup_file=None):
    """Restaurer la base de données"""
    print("🔄 RESTAURATION DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Si aucun fichier spécifié, prendre le plus récent
    if not backup_file:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            print("❌ Aucun dossier de sauvegarde trouvé")
            return False
        
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        if not backup_files:
            print("❌ Aucun fichier de sauvegarde trouvé")
            return False
        
        # Prendre le plus récent
        backup_files.sort(reverse=True)
        backup_file = os.path.join(backup_dir, backup_files[0])
        print(f"📁 Utilisation de la sauvegarde la plus récente: {backup_file}")
    
    if not os.path.exists(backup_file):
        print(f"❌ Fichier de sauvegarde non trouvé: {backup_file}")
        return False
    
    # Créer une sauvegarde de la base actuelle avant restauration
    current_db = 'instance/myxploit_dev.db'
    if os.path.exists(current_db):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = f"backups/myxploit_dev_before_restore_{timestamp}.db"
        shutil.copy2(current_db, current_backup)
        print(f"💾 Sauvegarde de la base actuelle: {current_backup}")
    
    try:
        # Restaurer
        shutil.copy2(backup_file, current_db)
        
        # Vérifier la restauration
        if os.path.exists(current_db):
            backup_size = os.path.getsize(backup_file)
            restored_size = os.path.getsize(current_db)
            
            print(f"✅ Base de données restaurée")
            print(f"   Taille sauvegarde: {backup_size} octets")
            print(f"   Taille restaurée: {restored_size} octets")
            
            if backup_size == restored_size:
                print("✅ Restauration vérifiée avec succès")
                return True
            else:
                print("❌ Erreur: Tailles différentes après restauration")
                return False
        else:
            print("❌ Erreur: Base de données non restaurée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        return False

def list_backups():
    """Lister les sauvegardes disponibles"""
    print("📋 SAUVEGARDES DISPONIBLES")
    print("=" * 50)
    
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        print("❌ Aucun dossier de sauvegarde trouvé")
        return
    
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    if not backup_files:
        print("❌ Aucun fichier de sauvegarde trouvé")
        return
    
    backup_files.sort(reverse=True)
    
    for i, backup_file in enumerate(backup_files):
        file_path = os.path.join(backup_dir, backup_file)
        size = os.path.getsize(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"{i+1}. {backup_file}")
        print(f"   Taille: {size} octets")
        print(f"   Date: {mtime}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup_database()
        elif command == "restore":
            backup_file = sys.argv[2] if len(sys.argv) > 2 else None
            restore_database(backup_file)
        elif command == "list":
            list_backups()
        else:
            print("Usage: python backup_database.py [backup|restore|list] [fichier_sauvegarde]")
    else:
        print("Usage: python backup_database.py [backup|restore|list] [fichier_sauvegarde]")
        print("\nExemples:")
        print("  python backup_database.py backup")
        print("  python backup_database.py restore")
        print("  python backup_database.py restore backups/myxploit_dev_backup_20250101_120000.db")
        print("  python backup_database.py list")
