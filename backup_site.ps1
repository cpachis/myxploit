# Script de sauvegarde avancée du site MyXploit
# PowerShell - Version avancée avec compression

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SAUVEGARDE AVANCEE DU SITE MYXPLOIT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Créer le timestamp de sauvegarde
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupDir = "backup_myxploit_$Timestamp"
$BackupPath = Join-Path (Get-Location) $BackupDir

Write-Host "Timestamp de sauvegarde: $Timestamp" -ForegroundColor Yellow
Write-Host "Dossier de sauvegarde: $BackupPath" -ForegroundColor Yellow
Write-Host ""

# Créer la structure de sauvegarde
try {
    # Dossier principal
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Host "[1/7] Création de la structure de sauvegarde..." -ForegroundColor Green
    
    # Sous-dossiers
    $SubDirs = @(
        "myxploit",
        "myxploit\templates", 
        "myxploit\static",
        "myxploit\static\js",
        "myxploit\data",
        "myxploit\venv"
    )
    
    foreach ($dir in $SubDirs) {
        $fullPath = Join-Path $BackupPath $dir
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
    
    Write-Host "[2/7] Copie des fichiers Python et configuration..." -ForegroundColor Green
    # Copier les fichiers Python et configuration
    $PythonFiles = Get-ChildItem "myxploit\*.py" -ErrorAction SilentlyContinue
    $ConfigFiles = Get-ChildItem "myxploit\*.json" -ErrorAction SilentlyContinue
    $DocFiles = Get-ChildItem "myxploit\*.md" -ErrorAction SilentlyContinue
    $TextFiles = Get-ChildItem "myxploit\*.txt" -ErrorAction SilentlyContinue
    $BatchFiles = Get-ChildItem "myxploit\*.bat" -ErrorAction SilentlyContinue
    $PowerShellFiles = Get-ChildItem "myxploit\*.ps1" -ErrorAction SilentlyContinue
    
    $AllFiles = @($PythonFiles, $ConfigFiles, $DocFiles, $TextFiles, $BatchFiles, $PowerShellFiles)
    foreach ($file in $AllFiles) {
        if ($file) {
            Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\") -Force
        }
    }
    
    Write-Host "[3/7] Copie des templates HTML..." -ForegroundColor Green
    # Copier les templates HTML
    $HtmlFiles = Get-ChildItem "myxploit\templates\*.html" -ErrorAction SilentlyContinue
    foreach ($file in $HtmlFiles) {
        Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\templates\") -Force
    }
    
    Write-Host "[4/7] Copie des fichiers JavaScript..." -ForegroundColor Green
    # Copier les fichiers JavaScript
    $JsFiles = Get-ChildItem "myxploit\static\js\*.js" -ErrorAction SilentlyContinue
    foreach ($file in $JsFiles) {
        Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\static\js\") -Force
    }
    
    Write-Host "[5/7] Copie des fichiers CSS..." -ForegroundColor Green
    # Copier les fichiers CSS
    $CssFiles = Get-ChildItem "myxploit\static\*.css" -ErrorAction SilentlyContinue
    foreach ($file in $CssFiles) {
        Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\static\") -Force
    }
    
    Write-Host "[6/7] Copie des données..." -ForegroundColor Green
    # Copier les données
    $DataFiles = Get-ChildItem "myxploit\data\*" -ErrorAction SilentlyContinue
    foreach ($file in $DataFiles) {
        Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\data\") -Force -Recurse
    }
    
    Write-Host "[7/7] Copie des fichiers de test et documentation..." -ForegroundColor Green
    # Copier les fichiers de test
    $TestFiles = Get-ChildItem "myxploit\test_*.html" -ErrorAction SilentlyContinue
    $CorrectionFiles = Get-ChildItem "myxploit\CORRECTION_*.md" -ErrorAction SilentlyContinue
    
    foreach ($file in @($TestFiles, $CorrectionFiles)) {
        if ($file) {
            Copy-Item $file.FullName -Destination (Join-Path $BackupPath "myxploit\") -Force
        }
    }
    
    # Créer l'inventaire de sauvegarde
    Write-Host "Création de l'inventaire de sauvegarde..." -ForegroundColor Green
    $InventoryPath = Join-Path $BackupPath "INVENTAIRE_SAUVEGARDE.txt"
    
    $InventoryContent = @"
SAUVEGARDE DU SITE MYXPLOIT
============================

Date et heure: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")
Timestamp: $Timestamp
Chemin de sauvegarde: $BackupPath

FICHIERS SAUVEGARDES:
---------------------
"@
    
    $InventoryContent | Out-File -FilePath $InventoryPath -Encoding UTF8
    
    # Lister tous les fichiers sauvegardés
    Get-ChildItem -Path $BackupPath -Recurse | ForEach-Object {
        $relativePath = $_.FullName.Replace($BackupPath, "").TrimStart("\")
        $relativePath | Out-File -FilePath $InventoryPath -Append -Encoding UTF8
    }
    
    # Créer le script de restauration PowerShell
    Write-Host "Création du script de restauration PowerShell..." -ForegroundColor Green
    $RestoreScriptPath = Join-Path $BackupPath "RESTAURER_SAUVEGARDE.ps1"
    
    $RestoreScriptContent = @'
# Script de restauration de la sauvegarde MyXploit
# ATTENTION: Cette opération va remplacer tous les fichiers existants!

Write-Host "========================================" -ForegroundColor Red
Write-Host "   RESTAURATION DE LA SAUVEGARDE" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "ATTENTION: Cette opération va remplacer tous les fichiers existants!" -ForegroundColor Red
Write-Host ""

$confirmation = Read-Host "Êtes-vous sûr de vouloir continuer? (oui/non)"
if ($confirmation -ne "oui") {
    Write-Host "Restauration annulée." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "[1/6] Restauration des fichiers Python et configuration..." -ForegroundColor Green
Copy-Item "*.py" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "*.json" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "*.md" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "*.txt" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "*.bat" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "*.ps1" "..\myxploit\" -Force -ErrorAction SilentlyContinue

Write-Host "[2/6] Restauration des templates HTML..." -ForegroundColor Green
Copy-Item "templates\*.html" "..\myxploit\templates\" -Force -ErrorAction SilentlyContinue

Write-Host "[3/6] Restauration des fichiers JavaScript..." -ForegroundColor Green
Copy-Item "static\js\*.js" "..\myxploit\static\js\" -Force -ErrorAction SilentlyContinue

Write-Host "[4/6] Restauration des fichiers CSS..." -ForegroundColor Green
Copy-Item "static\*.css" "..\myxploit\static\" -Force -ErrorAction SilentlyContinue

Write-Host "[5/6] Restauration des données..." -ForegroundColor Green
Copy-Item "data\*" "..\myxploit\data\" -Force -Recurse -ErrorAction SilentlyContinue

Write-Host "[6/6] Restauration des fichiers de test..." -ForegroundColor Green
Copy-Item "test_*.html" "..\myxploit\" -Force -ErrorAction SilentlyContinue
Copy-Item "CORRECTION_*.md" "..\myxploit\" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   RESTAURATION TERMINEE AVEC SUCCES!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
'@
    
    $RestoreScriptContent | Out-File -FilePath $RestoreScriptPath -Encoding UTF8
    
    # Créer un fichier README
    Write-Host "Création du fichier README..." -ForegroundColor Green
    $ReadmePath = Join-Path $BackupPath "README_SAUVEGARDE.md"
    
    $ReadmeContent = @"
# 📁 Sauvegarde du Site MyXploit

## 📅 Informations de Sauvegarde
- **Date et heure:** $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")
- **Timestamp:** $Timestamp
- **Chemin:** $BackupPath

## 📋 Contenu de la Sauvegarde
Cette sauvegarde contient une copie complète de votre site MyXploit :

### 🔧 Fichiers de Configuration
- Fichiers Python (`.py`)
- Fichiers de configuration (`.json`)
- Documentation (`.md`)
- Scripts (`.bat`, `.ps1`)

### 🌐 Interface Web
- Templates HTML
- Fichiers JavaScript
- Fichiers CSS

### 💾 Données
- Fichiers de données JSON
- Scripts de génération de données
- Fichiers CSV

### 🧪 Tests et Documentation
- Pages de test HTML
- Documentation des corrections
- Fichiers de validation

## 🔄 Restauration

### Option 1: Script PowerShell (Recommandé)
```powershell
# Ouvrir PowerShell dans ce dossier
# Exécuter le script de restauration
.\RESTAURER_SAUVEGARDE.ps1
```

### Option 2: Script Batch
```cmd
# Ouvrir l'invite de commandes dans ce dossier
# Exécuter le script de restauration
RESTAURER_SAUVEGARDE.bat
```

### Option 3: Restauration Manuelle
Copier manuellement les fichiers depuis les sous-dossiers vers votre projet principal.

## ⚠️ Attention
- La restauration remplacera tous les fichiers existants
- Assurez-vous d'avoir sauvegardé vos modifications récentes
- Testez la restauration dans un environnement de développement d'abord

## 📊 Statistiques
- **Nombre de fichiers:** $(Get-ChildItem -Path $BackupPath -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count)
- **Taille totale:** $([math]::Round((Get-ChildItem -Path $BackupPath -Recurse -File | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum) / 1MB, 2)) MB

---
*Sauvegarde créée automatiquement le $(Get-Date -Format "dd/MM/yyyy à HH:mm:ss")*
"@
    
    $ReadmeContent | Out-File -FilePath $ReadmePath -Encoding UTF8
    
    # Calculer la taille de la sauvegarde
    $BackupSize = (Get-ChildItem -Path $BackupPath -Recurse -File | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum)
    $BackupSizeMB = [math]::Round($BackupSize / 1MB, 2)
    $FileCount = (Get-ChildItem -Path $BackupPath -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "    SAUVEGARDE TERMINEE AVEC SUCCES!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dossier de sauvegarde: $BackupPath" -ForegroundColor Yellow
    Write-Host "Taille de la sauvegarde: $BackupSizeMB MB" -ForegroundColor Yellow
    Write-Host "Nombre de fichiers: $FileCount" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Contenu de la sauvegarde:" -ForegroundColor Cyan
    Write-Host "- Fichiers Python et configuration" -ForegroundColor White
    Write-Host "- Templates HTML" -ForegroundColor White
    Write-Host "- Fichiers JavaScript et CSS" -ForegroundColor White
    Write-Host "- Données JSON, CSV" -ForegroundColor White
    Write-Host "- Fichiers de test et documentation" -ForegroundColor White
    Write-Host "- Script de restauration PowerShell" -ForegroundColor White
    Write-Host "- Inventaire complet des fichiers" -ForegroundColor White
    Write-Host "- Fichier README détaillé" -ForegroundColor White
    Write-Host ""
    Write-Host "Pour restaurer:" -ForegroundColor Cyan
    Write-Host "1. Aller dans le dossier $BackupDir" -ForegroundColor White
    Write-Host "2. Exécuter RESTAURER_SAUVEGARDE.ps1 (PowerShell)" -ForegroundColor White
    Write-Host "3. Ou RESTAURER_SAUVEGARDE.bat (Command Prompt)" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "Erreur lors de la sauvegarde: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Appuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")











