"""
Blueprint pour les routes principales de l'application
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
main_bp = Blueprint('main', __name__)

logger = logging.getLogger(__name__)

@main_bp.route('/')
def index():
    """Page d'accueil"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page d'accueil: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@main_bp.route('/homepage')
def homepage():
    """Page d'accueil principale"""
    try:
        return render_template('homepage.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la homepage: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@main_bp.route('/myxploit')
def myxploit():
    """Page MyXploit"""
    try:
        return render_template('myxploit.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page MyXploit: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@main_bp.route('/administration')
def administration():
    """Page d'administration"""
    try:
        return render_template('administration.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page administration: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@main_bp.route('/dashboard')
def dashboard():
    """Page de tableau de bord"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement du dashboard: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@main_bp.route('/logout')
def logout():
    """Déconnexion"""
    try:
        from flask_login import logout_user
        logout_user()
        flash('Vous avez été déconnecté avec succès.', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        flash('Erreur lors de la déconnexion', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/health')
def health():
    """Endpoint de santé de l'application"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500



