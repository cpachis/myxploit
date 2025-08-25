# 🔄 Système de Sauvegarde MyXploit

## 📋 Vue d'ensemble

Ce projet dispose d'un système de sauvegarde automatisé complet qui permet de créer des sauvegardes horodatées de l'ensemble du projet, incluant le code source, les templates, les données et la configuration.

## 🚀 Scripts Disponibles

### **1. Script Python Principal (`backup_project.py`)**

Script principal multiplateforme pour la sauvegarde automatique.

#### **Utilisation :**
```bash
# Créer une nouvelle sauvegarde
python backup_project.py

# Lister les sauvegardes existantes
python backup_project.py list

# Afficher l'aide
python backup_project.py help
```

#### **Fonctionnalités :**
- ✅ Sauvegarde complète avec horodatage
- ✅ Création d'archives ZIP compressées
- ✅ Métadonnées et documentation automatiques
- ✅ Exclusion des fichiers temporaires et caches
- ✅ Gestion des erreurs et validation

### **2. Script Batch Windows (`backup_project.bat`)**

Script Windows classique avec interface interactive.

#### **Utilisation :**
```cmd
# Double-cliquer sur le fichier .bat
# Ou exécuter en ligne de commande
backup_project.bat
```

#### **Fonctionnalités :**
- ✅ Interface interactive en français
- ✅ Vérification automatique de Python
- ✅ Menu à choix multiples
- ✅ Gestion des erreurs Windows

### **3. Script PowerShell (`backup_project.ps1`)**

Script PowerShell moderne avec interface colorée.

#### **Utilisation :**
```powershell
# Interface interactive
.\backup_project.ps1

# Commandes directes
.\backup_project.ps1 backup    # Créer une sauvegarde
.\backup_project.ps1 list      # Lister les sauvegardes
.\backup_project.ps1 help      # Afficher l'aide
.\backup_project.ps1 info      # Informations du projet
```

#### **Fonctionnalités :**
- ✅ Interface PowerShell moderne
- ✅ Couleurs et émojis
- ✅ Commandes paramétrées
- ✅ Informations détaillées du projet

## 📁 Contenu Sauvegardé

### **Fichiers et Dossiers Inclus :**
- **`app.py`** - Application Flask principale
- **`models.py`** - Modèles de données
- **`templates/`** - Templates HTML Jinja2
- **`static/`** - Ressources statiques (CSS, JS, images)
- **`data/`** - Fichiers de données JSON
- **`.vscode/`** - Configuration VS Code
- **`*.md`** - Documentation Markdown
- **`*.html`** - Fichiers HTML de test
- **`*.py`** - Scripts Python

### **Fichiers et Dossiers Exclus :**
- **`__pycache__/`** - Cache Python
- **`*.pyc`, `*.pyo`, `*.pyd`** - Fichiers Python compilés
- **`.git/`** - Historique Git
- **`backups/`** - Dossiers de sauvegarde précédents
- **`venv/`, `env/`** - Environnements virtuels
- **`.env`** - Variables d'environnement
- **`*.log`, `*.tmp`, `*.bak`** - Fichiers temporaires

## 🔧 Installation et Configuration

### **Prérequis :**
1. **Python 3.6+** installé et dans le PATH
2. **Permissions d'écriture** dans le dossier du projet
3. **Espace disque** suffisant pour les sauvegardes

### **Vérification de l'installation :**
```bash
# Vérifier Python
python --version

# Vérifier les permissions
python -c "import os; print('Permissions OK' if os.access('.', os.W_OK) else 'Permissions insuffisantes')"
```

## 📊 Structure des Sauvegardes

### **Organisation des fichiers :**
```
backups/
├── myxploit_backup_2025-01-20_15-30-45/
│   ├── app.py
│   ├── models.py
│   ├── templates/
│   ├── static/
│   ├── data/
│   ├── .vscode/
│   ├── backup_metadata.json
│   └── README.md
├── myxploit_backup_2025-01-20_15-30-45.zip
└── ...
```

### **Fichiers de métadonnées :**
- **`backup_metadata.json`** - Informations techniques de la sauvegarde
- **`README.md`** - Documentation de la sauvegarde avec instructions de restauration

## 🎯 Utilisation Recommandée

### **Sauvegarde régulière :**
```bash
# Sauvegarde quotidienne (recommandé)
python backup_project.py

# Sauvegarde avant modifications importantes
python backup_project.py

# Sauvegarde après ajout de fonctionnalités
python backup_project.py
```

### **Gestion des sauvegardes :**
```bash
# Lister toutes les sauvegardes
python backup_project.py list

# Identifier les sauvegardes récentes
# Garder au moins 5 sauvegardes récentes
# Supprimer les sauvegardes anciennes (> 30 jours)
```

## 🔄 Restauration d'une Sauvegarde

### **Procédure de restauration :**
1. **Arrêter** l'application MyXploit si elle est en cours d'exécution
2. **Sauvegarder** l'état actuel (optionnel mais recommandé)
3. **Extraire** l'archive ZIP ou copier le dossier de sauvegarde
4. **Remplacer** les fichiers/dossiers par ceux de la sauvegarde
5. **Redémarrer** l'application

### **Restauration partielle :**
```bash
# Restaurer seulement les templates
cp -r backup/templates/ ./

# Restaurer seulement les données
cp -r backup/data/ ./

# Restaurer seulement la configuration
cp backup/.vscode/ ./
```

## 📈 Surveillance et Maintenance

### **Indicateurs de santé :**
- **Taille des sauvegardes** (doit rester stable)
- **Nombre de sauvegardes** (garder 5-10 sauvegardes)
- **Espace disque** (vérifier régulièrement)
- **Intégrité des archives** (tester la restauration)

### **Maintenance recommandée :**
- **Nettoyer** les sauvegardes anciennes (> 30 jours)
- **Vérifier** l'espace disque disponible
- **Tester** la restauration sur un environnement de test
- **Documenter** les modifications importantes

## 🚨 Dépannage

### **Erreurs courantes :**

#### **Python non trouvé :**
```bash
# Solution 1 : Installer Python
# Télécharger depuis https://python.org

# Solution 2 : Utiliser py (Windows)
py backup_project.py

# Solution 3 : Vérifier le PATH
echo $PATH  # Linux/Mac
echo %PATH% # Windows
```

#### **Permissions insuffisantes :**
```bash
# Solution 1 : Exécuter en tant qu'administrateur
# Solution 2 : Vérifier les permissions du dossier
# Solution 3 : Changer le dossier de destination
```

#### **Espace disque insuffisant :**
```bash
# Solution 1 : Libérer de l'espace
# Solution 2 : Changer le dossier de destination
# Solution 3 : Nettoyer les anciennes sauvegardes
```

### **Logs et diagnostics :**
```bash
# Vérifier les erreurs Python
python backup_project.py 2>&1 | tee backup.log

# Vérifier l'espace disque
df -h  # Linux/Mac
dir     # Windows
```

## 🔐 Sécurité et Bonnes Pratiques

### **Recommandations de sécurité :**
1. **Ne pas sauvegarder** les mots de passe en clair
2. **Chiffrer** les sauvegardes sensibles
3. **Stocker** les sauvegardes sur un support externe
4. **Tester** régulièrement la restauration
5. **Documenter** les procédures de restauration

### **Emplacement des sauvegardes :**
- **Local** : Dossier `backups/` du projet
- **Externe** : Disque dur externe, NAS, cloud
- **Versioning** : Système de contrôle de version (Git)

## 📝 Exemples d'Automatisation

### **Script de sauvegarde automatique (Linux/Mac) :**
```bash
#!/bin/bash
# Sauvegarde automatique quotidienne

cd /chemin/vers/myxploit
python backup_project.py

# Nettoyer les anciennes sauvegardes (> 30 jours)
find backups/ -name "myxploit_backup_*" -type d -mtime +30 -exec rm -rf {} \;
```

### **Tâche planifiée Windows :**
```cmd
# Créer une tâche planifiée
schtasks /create /tn "MyXploit Backup" /tr "C:\chemin\vers\myxploit\backup_project.bat" /sc daily /st 02:00
```

### **Script PowerShell automatisé :**
```powershell
# Sauvegarde automatique avec notification
.\backup_project.ps1 backup
if ($LASTEXITCODE -eq 0) {
    Write-Host "Sauvegarde réussie" | Out-File -FilePath "backup_status.log" -Append
} else {
    Write-Host "Échec de la sauvegarde" | Out-File -FilePath "backup_status.log" -Append
}
```

## 🎉 Conclusion

Le système de sauvegarde MyXploit offre une solution complète et fiable pour protéger votre projet. Utilisez-le régulièrement et maintenez-le correctement pour assurer la sécurité de vos données et la continuité de votre travail.

### **Points clés :**
- ✅ **Sauvegarde automatique** avec horodatage
- ✅ **Interface multiple** (Python, Batch, PowerShell)
- ✅ **Documentation complète** de chaque sauvegarde
- ✅ **Gestion intelligente** des exclusions
- ✅ **Archives compressées** pour économiser l'espace
- ✅ **Procédures de restauration** documentées

---

*Documentation créée automatiquement - MyXploit Backup System v1.0*



