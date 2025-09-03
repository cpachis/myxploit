"""
Blueprint pour les routes de paramétrage
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
parametrage_bp = Blueprint('parametrage', __name__, url_prefix='/parametrage')

logger = logging.getLogger(__name__)

@parametrage_bp.route('/clients')
def parametrage_clients():
    """Page de paramétrage des clients"""
    try:
        return render_template('parametrage_clients.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage clients: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_clients'))

@parametrage_bp.route('/energies')
def parametrage_energies():
    """Page de paramétrage des énergies"""
    try:
        return render_template('parametrage_energies.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage énergies: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_energies'))

@parametrage_bp.route('/vehicules')
def parametrage_vehicules():
    """Page de paramétrage des véhicules"""
    try:
        return render_template('parametrage_vehicules.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage véhicules: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_vehicules'))

@parametrage_bp.route('/transporteurs')
def parametrage_transporteurs():
    """Page de paramétrage des transporteurs"""
    try:
        return render_template('parametrage_transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage transporteurs: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_transporteurs'))

@parametrage_bp.route('/dashboards')
def parametrage_dashboards():
    """Page de paramétrage des dashboards"""
    try:
        return render_template('parametrage_dashboards.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage dashboards: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_dashboards'))

@parametrage_bp.route('/impact')
def parametrage_impact():
    """Page de paramétrage de l'impact"""
    try:
        return render_template('parametrage_impact.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage impact: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_impact'))

@parametrage_bp.route('/systeme')
def parametrage_systeme():
    """Page de paramétrage du système"""
    try:
        return render_template('parametrage_systeme.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramétrage système: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('parametrage.parametrage_systeme'))



