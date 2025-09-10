"""
Blueprint pour les routes liées aux invitations
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
invitations_bp = Blueprint('invitations', __name__)

logger = logging.getLogger(__name__)

@invitations_bp.route('/')
@invitations_bp.route('/invitations')
def invitations():
    """Page des invitations"""
    try:
        return render_template('invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations: {str(e)}")
        return render_template('error.html', error=str(e)), 500