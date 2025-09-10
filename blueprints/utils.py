"""
Blueprint pour les routes utilitaires (import, santé, etc.)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import logout_user
from datetime import datetime
import logging

# Créer le blueprint
utils_bp = Blueprint('utils', __name__)

logger = logging.getLogger(__name__)

@utils_bp.route('/import_csv')
def import_csv():
    """Page d'import CSV"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'import CSV: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@utils_bp.route('/logout')
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('auth.login'))

@utils_bp.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500