@echo off
echo === LANCEMENT DE MYXPLOIT ===
echo.
echo Naviguez vers: http://localhost:5000
echo Arreter avec Ctrl+C
echo.
cd /d "%~dp0"
venv\Scripts\python.exe app.py
pause
