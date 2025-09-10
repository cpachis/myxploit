"""
Blueprint pour les routes API liées aux transports
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_transports_bp = Blueprint('api_transports', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_transports_bp.route('/transports')
def api_transports():
    """API pour récupérer les transports"""
    try:
        return jsonify({
            'success': True,
            'transports': [],
            'message': 'API transports fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API transports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500