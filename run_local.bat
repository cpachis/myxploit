@echo off
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo Installation des dependances...
pip install -r requirements.txt

echo Demarrage de l'application...
python app.py

pause
