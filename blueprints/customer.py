"""
Blueprint pour l'interface client "My Customer Xploit"
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Créer le blueprint
customer_bp = Blueprint('customer', __name__)

logger = logging.getLogger(__name__)

@customer_bp.route('/')
@customer_bp.route('/customer')
def dashboard():
    """Dashboard client"""
    try:
        return render_template('customer/dashboard.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement du dashboard client: {str(e)}")
        return render_template('error.html', error=str(e)), 500