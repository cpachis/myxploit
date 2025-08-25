@echo off
echo ========================================
echo    SAUVEGARDE COMPLETE DU SITE MYXPLOIT
echo ========================================
echo.

:: Créer le dossier de sauvegarde avec timestamp
set TIMESTAMP=%date:~-4,4%-%date:~-7,2%-%date:~-10,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=backup_myxploit_%TIMESTAMP%

echo Timestamp de sauvegarde: %TIMESTAMP%
echo Dossier de sauvegarde: %BACKUP_DIR%
echo.

:: Créer le dossier de sauvegarde
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%BACKUP_DIR%\myxploit" mkdir "%BACKUP_DIR%\myxploit"

echo [1/6] Copie des fichiers Python et configuration...
:: Copier les fichiers Python et configuration
copy "myxploit\*.py" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\*.json" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\*.md" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\*.txt" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\*.bat" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\*.ps1" "%BACKUP_DIR%\myxploit\" >nul 2>&1

echo [2/6] Copie des templates HTML...
:: Copier les templates
if not exist "%BACKUP_DIR%\myxploit\templates" mkdir "%BACKUP_DIR%\myxploit\templates"
xcopy "myxploit\templates\*.html" "%BACKUP_DIR%\myxploit\templates\" /Y /Q >nul 2>&1

echo [3/6] Copie des fichiers JavaScript...
:: Copier les fichiers JavaScript
if not exist "%BACKUP_DIR%\myxploit\static" mkdir "%BACKUP_DIR%\myxploit\static"
if not exist "%BACKUP_DIR%\myxploit\static\js" mkdir "%BACKUP_DIR%\myxploit\static\js"
xcopy "myxploit\static\js\*.js" "%BACKUP_DIR%\myxploit\static\js\" /Y /Q >nul 2>&1

echo [4/6] Copie des fichiers CSS...
:: Copier les fichiers CSS
xcopy "myxploit\static\*.css" "%BACKUP_DIR%\myxploit\static\" /Y /Q >nul 2>&1

echo [5/6] Copie des données...
:: Copier les données
if not exist "%BACKUP_DIR%\myxploit\data" mkdir "%BACKUP_DIR%\myxploit\data"
xcopy "myxploit\data\*.json" "%BACKUP_DIR%\myxploit\data\" /Y /Q >nul 2>&1
xcopy "myxploit\data\*.py" "%BACKUP_DIR%\myxploit\data\" /Y /Q >nul 2>&1
xcopy "myxploit\data\*.csv" "%BACKUP_DIR%\myxploit\data\" /Y /Q >nul 2>&1

echo [6/6] Copie des fichiers de test et documentation...
:: Copier les fichiers de test
copy "myxploit\test_*.html" "%BACKUP_DIR%\myxploit\" >nul 2>&1
copy "myxploit\CORRECTION_*.md" "%BACKUP_DIR%\myxploit\" >nul 2>&1

:: Créer un fichier d'inventaire de la sauvegarde
echo Création de l'inventaire de sauvegarde...
echo Sauvegarde du site MyXploit > "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo ================================ >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo. >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo Date et heure: %date% %time% >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo Timestamp: %TIMESTAMP% >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo. >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo Fichiers sauvegardés: >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
echo --------------------- >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"
dir /s /b "%BACKUP_DIR%" >> "%BACKUP_DIR%\INVENTAIRE_SAUVEGARDE.txt"

:: Créer un fichier de restauration
echo Création du script de restauration...
echo @echo off > "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo ======================================== >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo    RESTAURATION DE LA SAUVEGARDE >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo ======================================== >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo. >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo ATTENTION: Cette opération va remplacer tous les fichiers existants! >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo. >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo pause >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo. >> "%BACK_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo [1/5] Restauration des fichiers Python et configuration... >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.py" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.json" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.md" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.txt" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.bat" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo copy "*.ps1" "..\myxploit\" /Y ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo [2/5] Restauration des templates HTML... >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "templates\*.html" "..\myxploit\templates\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo [3/5] Restauration des fichiers JavaScript... >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "static\js\*.js" "..\myxploit\static\js\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo [4/5] Restauration des fichiers CSS... >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "static\*.css" "..\myxploit\static\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo [5/5] Restauration des données... >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "data\*.json" "..\myxploit\data\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "data\*.py" "..\myxploit\data\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo xcopy "data\*.csv" "..\myxploit\data\" /Y /Q ^>nul 2^>^&1 >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo. >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo echo Restauration terminee avec succes! >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"
echo pause >> "%BACKUP_DIR%\RESTAURER_SAUVEGARDE.bat"

echo.
echo ========================================
echo    SAUVEGARDE TERMINEE AVEC SUCCES!
echo ========================================
echo.
echo Dossier de sauvegarde: %BACKUP_DIR%
echo.
echo Contenu de la sauvegarde:
echo - Fichiers Python et configuration
echo - Templates HTML
echo - Fichiers JavaScript et CSS
echo - Données JSON, CSV
echo - Fichiers de test et documentation
echo - Script de restauration automatique
echo - Inventaire complet des fichiers
echo.
echo Pour restaurer: aller dans le dossier %BACKUP_DIR% et executer RESTAURER_SAUVEGARDE.bat
echo.
pause








