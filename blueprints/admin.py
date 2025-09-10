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

@admin_bp.route('/clients')
def admin_clients():
    """Page d'administration des clients"""
    try:
        return render_template('admin_clients_list.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement des clients admin: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@admin_bp.route('/invitations')
def admin_invitations():
    """Page d'administration des invitations"""
    try:
        return render_template('admin_invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement des invitations admin: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@admin_bp.route('/clients-pending')
def admin_clients_pending():
    """Page des clients en attente"""
    try:
        return render_template('admin_clients_pending.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement des clients en attente: {str(e)}")
        return render_template('error.html', error=str(e)), 500