"""
Blueprint pour les routes API liées aux véhicules
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_vehicules_bp = Blueprint('api_vehicules', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_vehicules_bp.route('/vehicules')
def api_vehicules():
    """API pour récupérer les véhicules"""
    try:
        return jsonify({
            'success': True,
            'vehicules': [],
            'message': 'API véhicules fonctionnelle'
        })
    except Exception as e:
        logger.error(f"Erreur API véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules/types')
def api_vehicules_types():
    """API pour récupérer les types de véhicules"""
    try:
        # Types de véhicules par défaut
        types_vehicules = [
            {
                'id': 1,
                'nom': 'Camion léger',
                'consommation_base': 15.0,
                'facteur_emission': 3.1,
                'charge_utile_max': 3.5
            },
            {
                'id': 2,
                'nom': 'Camion moyen',
                'consommation_base': 25.0,
                'facteur_emission': 3.1,
                'charge_utile_max': 7.5
            },
            {
                'id': 3,
                'nom': 'Camion lourd',
                'consommation_base': 35.0,
                'facteur_emission': 3.1,
                'charge_utile_max': 26.0
            },
            {
                'id': 4,
                'nom': 'Véhicule utilitaire',
                'consommation_base': 12.0,
                'facteur_emission': 3.1,
                'charge_utile_max': 1.5
            }
        ]
        
        return jsonify({
            'success': True,
            'types_vehicules': types_vehicules,
            'message': 'Types de véhicules chargés avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API types véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500