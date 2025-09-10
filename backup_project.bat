@echo off
chcp 65001 >nul
title MyXploit - Sauvegarde du Projet

echo.
echo ========================================
echo    🚛 MyXploit - Script de Sauvegarde
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR : Python n'est pas installé ou n'est pas dans le PATH
    echo.
    echo 💡 Solutions :
    echo   1. Installez Python depuis https://python.org
    echo   2. Ajoutez Python au PATH système
    echo   3. Utilisez 'py' au lieu de 'python' si vous avez Python Launcher
    echo.
    pause
    exit /b 1
)

echo ✅ Python détecté
echo.

REM Vérifier si le script de sauvegarde existe
if not exist "backup_project.py" (
    echo ❌ ERREUR : Le fichier backup_project.py est introuvable
    echo.
    echo 💡 Assurez-vous d'être dans le bon répertoire
    echo.
    pause
    exit /b 1
)

echo ✅ Script de sauvegarde trouvé
echo.

REM Menu interactif
:menu
echo 📋 Choisissez une action :
echo.
echo 1. 🔄 Créer une nouvelle sauvegarde
echo 2. 📋 Lister les sauvegardes existantes
echo 3. ❓ Afficher l'aide
echo 4. 🚪 Quitter
echo.
set /p choice="Votre choix (1-4) : "

if "%choice%"=="1" goto backup
if "%choice%"=="2" goto list
if "%choice%"=="3" goto help
if "%choice%"=="4" goto exit
echo.
echo ❌ Choix invalide. Veuillez entrer 1, 2, 3 ou 4.
echo.
goto menu

:backup
echo.
echo 🚀 Démarrage de la sauvegarde...
echo.
python backup_project.py
echo.
echo ✅ Sauvegarde terminée !
echo.
pause
goto menu

:list
echo.
echo 📋 Liste des sauvegardes disponibles :
echo.
python backup_project.py list
echo.
pause
goto menu

:help
echo.
echo 📖 Aide du script de sauvegarde :
echo.
python backup_project.py help
echo.
pause
goto menu

:exit
echo.
echo 👋 Au revoir !
echo.
pause
exit /b 0















