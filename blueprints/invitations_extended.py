"""
Blueprint pour les routes d'invitations étendues
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
invitations_extended_bp = Blueprint('invitations_extended', __name__)

logger = logging.getLogger(__name__)

@invitations_extended_bp.route('/')
def invitations_extended():
    """Page des invitations étendues"""
    try:
        return render_template('invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations étendues: {str(e)}")
        return render_template('error.html', error=str(e)), 500