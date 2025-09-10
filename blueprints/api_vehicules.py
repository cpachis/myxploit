"""
Blueprint pour les routes API liées aux véhicules
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_vehicules_bp = Blueprint('api_vehicules', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_vehicules_bp.route('/vehicules')
def api_vehicules():
    """API pour récupérer les véhicules"""
    try:
        return jsonify({
            'success': True,
            'vehicules': [],
            'message': 'API véhicules fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500