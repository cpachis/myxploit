"""
Blueprint pour les routes API liées aux invitations
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import logging

# Créer le blueprint
api_invitations_bp = Blueprint('api_invitations', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_invitations_bp.route('/invitations')
def api_invitations():
    """API pour récupérer les invitations"""
    try:
        return jsonify({
            'success': True,
            'invitations': [],
            'message': 'API invitations fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API invitations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500