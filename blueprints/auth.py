from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
import json
import os

auth_bp = Blueprint('auth', __name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import User as DBUser
    return DBUser

def load_json(filename):
    """Charge un fichier JSON depuis le dossier data"""
    try:
        data_path = os.path.join('data', filename)
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de {filename}: {e}")
        return {}

class User:
    """Classe utilisateur pour compatibilité avec l'ancien système"""
    def __init__(self, email):
        self.email = email
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return self.email

# --- Route de connexion ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Veuillez remplir tous les champs', 'danger')
            return render_template('login.html')
        
        # Essayer d'abord la base de données (nouveaux utilisateurs)
        DBUser = get_models()
        user = DBUser.query.filter_by(email=email, statut='actif').first()
        if user and user.check_password(password):
            login_user(user, remember='remember' in request.form)
            
            # Rediriger selon le type d'utilisateur
            if user.type_utilisateur == 'client':
                return redirect(url_for('clients.mon_entreprise'))
            else:
                return redirect(url_for('main.homepage'))
        
        # Fallback vers l'ancien système JSON (compatibilité)
        try:
            users = load_json('users.json')
            if email in users and users[email]['password'] == password:
                login_user(User(email), remember='remember' in request.form)
                return redirect(url_for('main.homepage'))
        except:
            pass
        
        flash('Identifiants invalides', 'danger')
    
    return render_template('login.html')

# --- Route de déconnexion ---
@auth_bp.route('/logout')
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('auth.login')) 