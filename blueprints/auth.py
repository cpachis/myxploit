from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from .utils import load_json, User

auth_bp = Blueprint('auth', __name__)

# --- Route de connexion ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_json('users.json')
        u, p = request.form['username'], request.form['password']
        if u in users and users[u]['password'] == p:
            login_user(User(u), remember='remember' in request.form)
            return redirect(url_for('operations.index'))
        flash('Identifiants invalides', 'danger')
    return render_template('login.html')

# --- Route de déconnexion ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 