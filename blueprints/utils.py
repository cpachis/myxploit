"""
Blueprint pour les routes utilitaires (import, santé, etc.)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import logout_user
from datetime import datetime
import logging
from sqlalchemy import text

# Créer le blueprint
utils_bp = Blueprint('utils', __name__)

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db
    return db

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
    db = get_models()
    
    try:
        # Test de connexion à la base de données
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@utils_bp.route('/api/transports/calculate-distance', methods=['POST'])
def api_calculate_distance():
    """API pour calculer la distance et les émissions entre deux lieux"""
    try:
        data = request.get_json()
        
        if not data.get('lieu_depart') or not data.get('lieu_arrivee'):
            return jsonify({'success': False, 'error': 'Lieu de départ et lieu d\'arrivée sont obligatoires'}), 400
        
        # Ici, vous pourriez intégrer une API de calcul de distance (Google Maps, etc.)
        # Pour l'instant, on retourne des valeurs simulées
        
        distance_km = 150  # Valeur simulée
        emissions_kg = distance_km * 0.1  # Facteur simulé
        
        return jsonify({
            'success': True,
            'distance_km': distance_km,
            'emissions_kg': emissions_kg,
            'lieu_depart': data['lieu_depart'],
            'lieu_arrivee': data['lieu_arrivee']
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de distance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@utils_bp.route('/api/lieux/autocomplete', methods=['GET'])
def api_lieux_autocomplete():
    """API pour l'autocomplétion des lieux (codes postaux et villes)"""
    try:
        query = request.args.get('q', '')
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'lieux': []
            })
        
        # Ici, vous pourriez intégrer une API de géocodage
        # Pour l'instant, on retourne des suggestions simulées
        
        suggestions = [
            f"{query} - Paris (75001)",
            f"{query} - Lyon (69001)",
            f"{query} - Marseille (13001)",
            f"{query} - Toulouse (31000)",
            f"{query} - Nice (06000)"
        ]
        
        return jsonify({
            'success': True,
            'lieux': suggestions
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'autocomplétion: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'autocomplétion: {str(e)}'
        })