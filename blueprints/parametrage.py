"""
Blueprint pour les routes de paramétrage
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
parametrage_bp = Blueprint('parametrage', __name__, url_prefix='/parametrage')

logger = logging.getLogger(__name__)

@parametrage_bp.route('/')
def parametrage_index():
    """Page de paramétrage"""
    try:
        return render_template('parametrage_systeme.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage: {str(e)}")
        return render_template('error.html', error=str(e)), 500