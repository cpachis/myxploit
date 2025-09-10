"""
Blueprint pour les routes API liées aux énergies
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_energies_bp = Blueprint('api_energies', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_energies_bp.route('/energies')
def api_energies():
    """API pour récupérer les énergies"""
    try:
        return jsonify({
            'success': True,
            'energies': [],
            'message': 'API énergies fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API énergies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500