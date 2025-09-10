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
        # Variables par défaut pour le template
        context = {
            'total_orders': 0,
            'total_distance': 0.0,
            'total_emissions': 0.0,
            'recent_orders': []
        }
        return render_template('customer/dashboard.html', **context)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du dashboard client: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@customer_bp.route('/nouveau-bon')
def nouveau_bon():
    """Page de création d'un nouveau bon"""
    try:
        return render_template('customer/nouveau_bon.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement du nouveau bon: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@customer_bp.route('/creer-bon', methods=['POST'])
def creer_bon():
    """Créer un nouveau bon de transport"""
    try:
        # Logique de création du bon
        return jsonify({'success': True, 'message': 'Bon créé avec succès'})
    except Exception as e:
        logger.error(f"Erreur lors de la création du bon: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_bp.route('/voir-bon/<int:bon_id>')
def voir_bon(bon_id):
    """Voir un bon de transport"""
    try:
        return render_template('customer/voir_bon.html', bon_id=bon_id)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du bon: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@customer_bp.route('/imprimer-bon/<int:bon_id>')
def imprimer_bon(bon_id):
    """Imprimer un bon de transport"""
    try:
        return render_template('customer/imprimer_bon.html', bon_id=bon_id)
    except Exception as e:
        logger.error(f"Erreur lors de l'impression du bon: {str(e)}")
        return render_template('error.html', error=str(e)), 500