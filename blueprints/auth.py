"""
Blueprint pour l'authentification
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
import json
import os

auth_bp = Blueprint('auth', __name__)

def load_json(filename):
    """Charge un fichier JSON depuis le dossier data"""
    try:
        data_path = os.path.join('data', filename)
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de {filename}: {e}")
        return []

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Pour le développement, accepter n'importe quel email/mot de passe
        if email and password:
            flash('Connexion réussie', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Email et mot de passe requis', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté', 'success')
    return redirect(url_for('main.index'))