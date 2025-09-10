"""
Blueprint pour les routes d'import CSV
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
import logging

# Créer le blueprint
import_csv_bp = Blueprint('import_csv', __name__)

logger = logging.getLogger(__name__)

@import_csv_bp.route('/')
@import_csv_bp.route('/import_csv')
def import_csv():
    """Page d'import CSV"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'import CSV: {str(e)}")
        return render_template('error.html', error=str(e)), 500