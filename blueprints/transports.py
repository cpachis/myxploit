"""
Blueprint pour les routes liées aux transports
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
transports_bp = Blueprint('transports', __name__)

logger = logging.getLogger(__name__)

@transports_bp.route('/')
@transports_bp.route('/transports')
def transports():
    """Liste des transports"""
    try:
        return render_template('mes_transports.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transports: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@transports_bp.route('/mes_transports')
def mes_transports():
    """Mes transports"""
    try:
        return render_template('mes_transports.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de mes transports: {str(e)}")
        return render_template('error.html', error=str(e)), 500