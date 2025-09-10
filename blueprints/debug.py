"""
Blueprint pour les routes de debug et utilitaires
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
debug_bp = Blueprint('debug', __name__)

logger = logging.getLogger(__name__)

@debug_bp.route('/')
@debug_bp.route('/debug')
def debug_page():
    """Page de debug pour diagnostiquer la base de données"""
    return render_template('debug.html')