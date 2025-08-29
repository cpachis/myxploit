# Script de déploiement automatisé pour Myxploit
# Usage: .\deploy.ps1

Write-Host "🚀 Script de déploiement Myxploit" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# 1. Vérification de la configuration
Write-Host "`n🔍 Étape 1: Vérification de la configuration..." -ForegroundColor Yellow
try {
    & "venv\Scripts\python.exe" "deploy_check.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Configuration vérifiée avec succès!" -ForegroundColor Green
    } else {
        Write-Host "❌ Problèmes de configuration détectés" -ForegroundColor Red
        Write-Host "Corrigez les problèmes avant de continuer" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification: $_" -ForegroundColor Red
    exit 1
}

# 2. Vérification de Git
Write-Host "`n📝 Étape 2: Vérification du statut Git..." -ForegroundColor Yellow
try {
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "⚠️  Fichiers non commités détectés:" -ForegroundColor Yellow
        Write-Host $gitStatus -ForegroundColor Gray
        
        $response = Read-Host "Voulez-vous commiter ces changements? (o/n)"
        if ($response -eq "o" -or $response -eq "O") {
            $commitMessage = Read-Host "Message de commit"
            git add .
            git commit -m $commitMessage
            Write-Host "✅ Changements commités" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Déploiement continué sans commit" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✅ Aucun fichier non commité" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur Git: $_" -ForegroundColor Red
    exit 1
}

# 3. Vérification de la branche
Write-Host "`n🌿 Étape 3: Vérification de la branche..." -ForegroundColor Yellow
try {
    $currentBranch = git branch --show-current
    Write-Host "Branche actuelle: $currentBranch" -ForegroundColor Cyan
    
    if ($currentBranch -ne "main") {
        $response = Read-Host "Vous n'êtes pas sur la branche main. Continuer? (o/n)"
        if ($response -ne "o" -and $response -ne "O") {
            Write-Host "Déploiement annulé" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification de la branche: $_" -ForegroundColor Red
    exit 1
}

# 4. Push vers GitHub
Write-Host "`n📤 Étape 4: Push vers GitHub..." -ForegroundColor Yellow
try {
    $response = Read-Host "Pousser vers GitHub? (o/n)"
    if ($response -eq "o" -or $response -eq "O") {
        git push origin $currentBranch
        Write-Host "✅ Code poussé vers GitHub" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Push annulé" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur lors du push: $_" -ForegroundColor Red
    exit 1
}

# 5. Instructions finales
Write-Host "`n🎯 Étape 5: Instructions de déploiement" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Configuration prête pour le déploiement!" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes sur Render:" -ForegroundColor Cyan
Write-Host "1. Connectez votre repo GitHub à Render" -ForegroundColor White
Write-Host "2. Créez un nouveau Web Service" -ForegroundColor White
Write-Host "3. Sélectionnez votre repo myxploit" -ForegroundColor White
Write-Host "4. Render utilisera automatiquement render.yaml" -ForegroundColor White
Write-Host "5. Surveillez les logs de build et de démarrage" -ForegroundColor White
Write-Host ""
Write-Host "📋 Fichiers de configuration créés:" -ForegroundColor Cyan
Write-Host "- render.yaml (configuration Render)" -ForegroundColor White
Write-Host "- requirements-render.txt (dépendances production)" -ForegroundColor White
Write-Host "- deploy_check.py (vérification pré-déploiement)" -ForegroundColor White
Write-Host "- TROUBLESHOOTING.md (guide de dépannage)" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Documentation Render: https://render.com/docs" -ForegroundColor Blue
Write-Host "📖 Guide de dépannage: TROUBLESHOOTING.md" -ForegroundColor Blue

Write-Host "`n🎉 Déploiement préparé avec succès!" -ForegroundColor Green

