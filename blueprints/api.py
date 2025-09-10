"""
Blueprint pour les routes API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_bp.route('/')
def api_index():
    """API index"""
    return jsonify({
        'message': 'API MyXploit',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })