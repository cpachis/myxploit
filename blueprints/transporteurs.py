"""
Blueprint pour les routes liées aux transporteurs
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
transporteurs_bp = Blueprint('transporteurs', __name__)

logger = logging.getLogger(__name__)

@transporteurs_bp.route('/')
@transporteurs_bp.route('/transporteurs')
def transporteurs():
    """Page des transporteurs"""
    try:
        return render_template('transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transporteurs: {str(e)}")
        return render_template('error.html', error=str(e)), 500