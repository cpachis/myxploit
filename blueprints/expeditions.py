"""
Blueprint pour les routes liées aux expéditions
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging

# Créer le blueprint
expeditions_bp = Blueprint('expeditions', __name__)

logger = logging.getLogger(__name__)

@expeditions_bp.route('/')
@expeditions_bp.route('/expeditions')
def expeditions():
    """Page des expéditions"""
    try:
        return render_template('expeditions.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des expéditions: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@expeditions_bp.route('/mes_expeditions')
def mes_expeditions():
    """Mes expéditions"""
    try:
        return render_template('expeditions.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de mes expéditions: {str(e)}")
        return render_template('error.html', error=str(e)), 500