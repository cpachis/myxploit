# MyXploit - Script de Sauvegarde PowerShell
# Compatible Windows 10/11 avec PowerShell 5.1+

param(
    [Parameter(Position=0)]
    [ValidateSet("backup", "list", "help", "info")]
    [string]$Command = "backup"
)

# Configuration des couleurs et de l'interface
$Host.UI.RawUI.WindowTitle = "🚛 MyXploit - Sauvegarde du Projet"

# Fonction pour afficher des messages colorés
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️ $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️ $Message" "Yellow" }

# En-tête
Clear-Host
Write-ColorOutput "========================================" "Magenta"
Write-ColorOutput "    🚛 MyXploit - Script de Sauvegarde" "Magenta"
Write-ColorOutput "========================================" "Magenta"
Write-Host ""

# Vérifier la version de PowerShell
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "PowerShell 5.1 ou supérieur est requis"
    Write-Info "Version actuelle : $($PSVersionTable.PSVersion)"
    exit 1
}

Write-Success "PowerShell $($PSVersionTable.PSVersion) détecté"
Write-Host ""

# Vérifier si Python est disponible
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python détecté : $pythonVersion"
    } else {
        throw "Python non disponible"
    }
} catch {
    Write-Error "Python n'est pas installé ou n'est pas dans le PATH"
    Write-Info "Solutions :"
    Write-Info "  1. Installez Python depuis https://python.org"
    Write-Info "  2. Ajoutez Python au PATH système"
    Write-Info "  3. Utilisez 'py' au lieu de 'python' si vous avez Python Launcher"
    Write-Host ""
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

# Vérifier si le script de sauvegarde existe
$scriptPath = Join-Path $PSScriptRoot "backup_project.py"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Le fichier backup_project.py est introuvable"
    Write-Info "Assurez-vous d'être dans le bon répertoire"
    Write-Host ""
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Success "Script de sauvegarde trouvé"
Write-Host ""

# Fonction pour exécuter la sauvegarde
function Start-Backup {
    Write-Info "🚀 Démarrage de la sauvegarde..."
    Write-Host ""
    
    try {
        python backup_project.py
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Sauvegarde terminée avec succès !"
        } else {
            Write-Error "Erreur lors de la sauvegarde"
        }
    } catch {
        Write-Error "Erreur lors de l'exécution : $($_.Exception.Message)"
    }
}

# Fonction pour lister les sauvegardes
function Get-BackupList {
    Write-Info "📋 Liste des sauvegardes disponibles :"
    Write-Host ""
    
    try {
        python backup_project.py list
    } catch {
        Write-Error "Erreur lors de la liste des sauvegardes : $($_.Exception.Message)"
    }
}

# Fonction pour afficher l'aide
function Show-Help {
    Write-Info "📖 Aide du script de sauvegarde :"
    Write-Host ""
    
    try {
        python backup_project.py help
    } catch {
        Write-Error "Erreur lors de l'affichage de l'aide : $($_.Exception.Message)"
    }
}

# Fonction pour afficher les informations du projet
function Show-ProjectInfo {
    Write-Info "📊 Informations du projet MyXploit :"
    Write-Host ""
    
    $projectRoot = $PSScriptRoot
    $templatesCount = (Get-ChildItem -Path "$projectRoot\templates" -Filter "*.html" -Recurse -ErrorAction SilentlyContinue).Count
    $staticCount = (Get-ChildItem -Path "$projectRoot\static" -Recurse -ErrorAction SilentlyContinue).Count
    $dataCount = (Get-ChildItem -Path "$projectRoot\data" -Filter "*.json" -Recurse -ErrorAction SilentlyContinue).Count
    $pythonCount = (Get-ChildItem -Path "$projectRoot" -Filter "*.py" -Recurse -ErrorAction SilentlyContinue).Count
    
    Write-ColorOutput "📁 Répertoire du projet : $projectRoot" "White"
    Write-ColorOutput "🎨 Templates HTML : $templatesCount" "Cyan"
    Write-ColorOutput "⚡ Fichiers statiques : $staticCount" "Cyan"
    Write-ColorOutput "💾 Fichiers de données : $dataCount" "Cyan"
    Write-ColorOutput "🐍 Fichiers Python : $pythonCount" "Cyan"
    
    # Calculer la taille totale
    $totalSize = (Get-ChildItem -Path $projectRoot -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-ColorOutput "📊 Taille totale : $totalSizeMB MB" "Yellow"
    
    Write-Host ""
}

# Menu interactif si aucune commande n'est spécifiée
if ($Command -eq "backup" -and $args.Count -eq 0) {
    do {
        Write-ColorOutput "📋 Choisissez une action :" "White"
        Write-Host ""
        Write-ColorOutput "1. 🔄 Créer une nouvelle sauvegarde" "Green"
        Write-ColorOutput "2. 📋 Lister les sauvegardes existantes" "Cyan"
        Write-ColorOutput "3. ❓ Afficher l'aide" "Yellow"
        Write-ColorOutput "4. 📊 Informations du projet" "Magenta"
        Write-ColorOutput "5. 🚪 Quitter" "Red"
        Write-Host ""
        
        $choice = Read-Host "Votre choix (1-5)"
        
        switch ($choice) {
            "1" { 
                Start-Backup
                Write-Host ""
                Read-Host "Appuyez sur Entrée pour continuer"
            }
            "2" { 
                Get-BackupList
                Write-Host ""
                Read-Host "Appuyez sur Entrée pour continuer"
            }
            "3" { 
                Show-Help
                Write-Host ""
                Read-Host "Appuyez sur Entrée pour continuer"
            }
            "4" { 
                Show-ProjectInfo
                Write-Host ""
                Read-Host "Appuyez sur Entrée pour continuer"
            }
            "5" { 
                Write-ColorOutput "👋 Au revoir !" "Green"
                exit 0
            }
            default { 
                Write-Warning "Choix invalide. Veuillez entrer 1, 2, 3, 4 ou 5."
                Write-Host ""
            }
        }
        
        Clear-Host
        Write-ColorOutput "========================================" "Magenta"
        Write-ColorOutput "    🚛 MyXploit - Script de Sauvegarde" "Magenta"
        Write-ColorOutput "========================================" "Magenta"
        Write-Host ""
        
    } while ($true)
} else {
    # Exécuter la commande spécifiée
    switch ($Command) {
        "backup" { Start-Backup }
        "list" { Get-BackupList }
        "help" { Show-Help }
        "info" { Show-ProjectInfo }
        default { 
            Write-Error "Commande inconnue : $Command"
            Write-Info "Commandes disponibles : backup, list, help, info"
        }
    }
}

Write-Host ""
Read-Host "Appuyez sur Entrée pour fermer"








