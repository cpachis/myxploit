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

@parametrage_bp.route('/vehicules')
def parametrage_vehicules():
    """Page de paramétrage des véhicules"""
    try:
        return render_template('parametrage_vehicules.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement des véhicules: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@parametrage_bp.route('/energies')
def parametrage_energies():
    """Page de paramétrage des énergies"""
    try:
        return render_template('parametrage_energies.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement des énergies: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@parametrage_bp.route('/impact')
def parametrage_impact():
    """Page de paramétrage de l'impact"""
    try:
        return render_template('parametrage_impact.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'impact: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@parametrage_bp.route('/systeme')
def parametrage_systeme():
    """Page de paramétrage du système"""
    try:
        return render_template('parametrage_systeme.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement du système: {str(e)}")
        return render_template('error.html', error=str(e)), 500