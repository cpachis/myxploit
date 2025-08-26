#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sauvegarde automatique du projet MyXploit
Crée une sauvegarde complète avec horodatage
"""

import os
import shutil
import zipfile
import json
from datetime import datetime
import sys

def create_backup():
    """Crée une sauvegarde complète du projet"""
    
    # Configuration
    project_root = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(project_root, "backups")
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"✅ Dossier de sauvegarde créé : {backup_dir}")
    
    # Horodatage pour le nom de la sauvegarde
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"myxploit_backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Dossiers et fichiers à sauvegarder
    items_to_backup = [
        "app.py",
        "models.py",
        "templates/",
        "static/",
        "data/",
        ".vscode/",
        "*.md",
        "*.html",
        "*.py"
    ]
    
    # Fichiers et dossiers à exclure
    exclude_patterns = [
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".git/",
        "backups/",
        "venv/",
        "env/",
        ".env",
        "*.log",
        "*.tmp",
        "*.bak"
    ]
    
    print(f"🚀 Début de la sauvegarde : {backup_name}")
    print(f"📁 Dossier source : {project_root}")
    print(f"📁 Dossier de destination : {backup_path}")
    print("-" * 50)
    
    try:
        # Créer le dossier de sauvegarde
        os.makedirs(backup_path)
        
        # Copier les fichiers et dossiers
        copied_items = []
        skipped_items = []
        
        for item in items_to_backup:
            source_path = os.path.join(project_root, item)
            
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    # Copier un fichier
                    dest_path = os.path.join(backup_path, item)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    copied_items.append(f"📄 {item}")
                    
                elif os.path.isdir(source_path):
                    # Copier un dossier
                    dest_path = os.path.join(backup_path, item)
                    if not os.path.exists(dest_path):
                        shutil.copytree(source_path, dest_path, ignore=shutil.ignore_patterns(*exclude_patterns))
                        copied_items.append(f"📁 {item}/")
                    else:
                        skipped_items.append(f"⚠️ {item}/ (déjà existant)")
            else:
                skipped_items.append(f"❌ {item} (introuvable)")
        
        # Créer un fichier de métadonnées de sauvegarde
        metadata = {
            "backup_name": backup_name,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "project_root": project_root,
            "backup_path": backup_path,
            "copied_items": copied_items,
            "skipped_items": skipped_items,
            "total_files": len(copied_items),
            "version": "1.0"
        }
        
        metadata_file = os.path.join(backup_path, "backup_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Créer un fichier README de la sauvegarde
        readme_content = f"""# 🔄 Sauvegarde MyXploit - {backup_name}

## 📋 Informations de la sauvegarde

- **Date et heure :** {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}
- **Nom de la sauvegarde :** {backup_name}
- **Chemin :** {backup_path}

## 📁 Contenu sauvegardé

### Fichiers et dossiers copiés :
"""
        
        for item in copied_items:
            readme_content += f"- {item}\n"
        
        if skipped_items:
            readme_content += "\n### Éléments ignorés :\n"
            for item in skipped_items:
                readme_content += f"- {item}\n"
        
        readme_content += f"""
## 🔧 Restauration

Pour restaurer cette sauvegarde :

1. **Arrêter** l'application MyXploit si elle est en cours d'exécution
2. **Sauvegarder** l'état actuel (optionnel mais recommandé)
3. **Remplacer** les fichiers/dossiers par ceux de cette sauvegarde
4. **Redémarrer** l'application

## 📊 Statistiques

- **Total des éléments sauvegardés :** {len(copied_items)}
- **Taille de la sauvegarde :** À calculer après compression

## ⚠️ Notes importantes

- Cette sauvegarde contient tous les fichiers de configuration
- Les données utilisateur et transports sont incluses
- Vérifiez l'intégrité avant restauration
- Conservez plusieurs sauvegardes pour la sécurité

---
*Sauvegarde créée automatiquement par backup_project.py*
"""
        
        readme_file = os.path.join(backup_path, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Créer une archive ZIP de la sauvegarde
        zip_path = f"{backup_path}.zip"
        print(f"📦 Création de l'archive ZIP : {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        # Calculer la taille de la sauvegarde
        backup_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                         for dirpath, dirnames, filenames in os.walk(backup_path)
                         for filename in filenames)
        
        zip_size = os.path.getsize(zip_path)
        
        print("-" * 50)
        print("✅ SAUVEGARDE TERMINÉE AVEC SUCCÈS !")
        print(f"📁 Dossier de sauvegarde : {backup_path}")
        print(f"📦 Archive ZIP : {zip_path}")
        print(f"📊 Taille du dossier : {backup_size / 1024 / 1024:.2f} MB")
        print(f"📊 Taille de l'archive : {zip_size / 1024 / 1024:.2f} MB")
        print(f"📄 Éléments sauvegardés : {len(copied_items)}")
        
        if skipped_items:
            print(f"⚠️ Éléments ignorés : {len(skipped_items)}")
        
        print("\n📋 Métadonnées de la sauvegarde :")
        print(f"   - Nom : {backup_name}")
        print(f"   - Horodatage : {timestamp}")
        print(f"   - Chemin : {backup_path}")
        
        return True, backup_path, zip_path
        
    except Exception as e:
        print(f"❌ ERREUR lors de la sauvegarde : {str(e)}")
        return False, None, None

def list_backups():
    """Liste toutes les sauvegardes disponibles"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(project_root, "backups")
    
    if not os.path.exists(backup_dir):
        print("❌ Aucun dossier de sauvegarde trouvé")
        return
    
    print(f"📁 Sauvegardes disponibles dans : {backup_dir}")
    print("-" * 50)
    
    backups = []
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path):
            # Dossier de sauvegarde
            metadata_file = os.path.join(item_path, "backup_metadata.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append({
                        'name': item,
                        'type': 'folder',
                        'timestamp': metadata.get('timestamp', 'N/A'),
                        'size': sum(os.path.getsize(os.path.join(dirpath, filename))
                                   for dirpath, dirnames, filenames in os.walk(item_path)
                                   for filename in filenames)
                    })
                except:
                    backups.append({
                        'name': item,
                        'type': 'folder',
                        'timestamp': 'N/A',
                        'size': 0
                    })
        elif item.endswith('.zip'):
            # Archive ZIP
            backups.append({
                'name': item,
                'type': 'zip',
                'timestamp': item.replace('myxploit_backup_', '').replace('.zip', ''),
                'size': os.path.getsize(item_path)
            })
    
    # Trier par timestamp (plus récent en premier)
    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    
    if not backups:
        print("❌ Aucune sauvegarde trouvée")
        return
    
    for i, backup in enumerate(backups, 1):
        size_mb = backup['size'] / 1024 / 1024
        print(f"{i:2d}. 📁 {backup['name']}")
        print(f"    📅 {backup['timestamp']}")
        print(f"    📊 {size_mb:.2f} MB")
        print(f"    🏷️  {backup['type']}")
        print()

def main():
    """Fonction principale"""
    print("🚛 MyXploit - Script de Sauvegarde")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list" or command == "ls":
            list_backups()
        elif command == "help" or command == "h":
            print("""
📖 Utilisation du script de sauvegarde :

python backup_project.py          # Créer une nouvelle sauvegarde
python backup_project.py list     # Lister les sauvegardes existantes
python backup_project.py help     # Afficher cette aide

🔧 Fonctionnalités :
- Sauvegarde complète du projet avec horodatage
- Création d'archives ZIP compressées
- Métadonnées et documentation automatiques
- Exclusion des fichiers temporaires et caches
- Gestion des erreurs et validation

📁 Dossiers sauvegardés :
- app.py, models.py (code principal)
- templates/ (interfaces utilisateur)
- static/ (ressources statiques)
- data/ (données JSON)
- .vscode/ (configuration VS Code)
- Documentation (*.md, *.html)

⚠️ Exclusions :
- __pycache__/, *.pyc (fichiers Python compilés)
- .git/ (historique Git)
- backups/ (sauvegardes précédentes)
- venv/, env/ (environnements virtuels)
- *.log, *.tmp (fichiers temporaires)
            """)
        else:
            print(f"❌ Commande inconnue : {command}")
            print("💡 Utilisez 'python backup_project.py help' pour l'aide")
    else:
        # Créer une nouvelle sauvegarde
        success, backup_path, zip_path = create_backup()
        
        if success:
            print("\n🎉 Sauvegarde terminée avec succès !")
            print(f"💾 Dossier : {backup_path}")
            print(f"📦 Archive : {zip_path}")
        else:
            print("\n❌ Échec de la sauvegarde")
            sys.exit(1)

if __name__ == "__main__":
    main()






