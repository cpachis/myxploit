from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from .utils import load_json, User

auth_bp = Blueprint('auth', __name__)

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
        user = DBUser.query.filter_by(email=email, statut='actif').first()
        if user and user.check_password(password):
            login_user(user, remember='remember' in request.form)
            
            # Rediriger selon le type d'utilisateur
            if user.type_utilisateur == 'client':
                return redirect(url_for('mon_entreprise'))
            else:
                return redirect(url_for('homepage'))
        
        # Fallback vers l'ancien système JSON (compatibilité)
        try:
            users = load_json('users.json')
            if email in users and users[email]['password'] == password:
                login_user(User(email), remember='remember' in request.form)
                return redirect(url_for('homepage'))
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