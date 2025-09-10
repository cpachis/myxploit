"""
Blueprint pour les routes API liées aux clients
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_clients_bp = Blueprint('api_clients', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_clients_bp.route('/clients')
def api_clients():
    """API pour récupérer les clients"""
    try:
        return jsonify({
            'success': True,
            'clients': [],
            'message': 'API clients fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API clients: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500