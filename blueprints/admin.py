"""
Blueprint pour les routes d'administration
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

@admin_bp.route('/')
@admin_bp.route('/administration')
def administration():
    """Page d'administration"""
    try:
        return render_template('administration.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page administration: {str(e)}")
        return render_template('error.html', error=str(e)), 500