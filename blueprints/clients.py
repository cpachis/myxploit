"""
Blueprint pour les routes liées aux clients
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
clients_bp = Blueprint('clients', __name__)

logger = logging.getLogger(__name__)

@clients_bp.route('/')
@clients_bp.route('/clients')
def clients():
    """Page de gestion des clients"""
    try:
        return render_template('clients.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients: {str(e)}")
        return render_template('error.html', error=str(e)), 500