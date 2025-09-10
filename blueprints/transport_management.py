"""
Blueprint pour la gestion des transports par les transporteurs
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
transport_management_bp = Blueprint('transport_management', __name__)

logger = logging.getLogger(__name__)

@transport_management_bp.route('/')
@transport_management_bp.route('/transport_management')
def dashboard():
    """Dashboard de gestion des transports"""
    try:
        return render_template('transport_management/dashboard.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement du dashboard de gestion: {str(e)}")
        return render_template('error.html', error=str(e)), 500