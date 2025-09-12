"""
Blueprint pour les routes API liées aux énergies
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_energies_bp = Blueprint('api_energies', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_energies_bp.route('/energies')
def api_energies():
    """API pour récupérer les énergies"""
    try:
        # Énergies par défaut
        energies = [
            {
                'id': 1,
                'nom': 'Gazole routier/B7',
                'facteur_emission': 3.1,
                'unite': 'kg CO₂e/L'
            },
            {
                'id': 2,
                'nom': 'Essence SP95',
                'facteur_emission': 2.3,
                'unite': 'kg CO₂e/L'
            },
            {
                'id': 3,
                'nom': 'Essence SP98',
                'facteur_emission': 2.3,
                'unite': 'kg CO₂e/L'
            },
            {
                'id': 4,
                'nom': 'GPL',
                'facteur_emission': 1.6,
                'unite': 'kg CO₂e/L'
            },
            {
                'id': 5,
                'nom': 'GNV',
                'facteur_emission': 2.0,
                'unite': 'kg CO₂e/m³'
            },
            {
                'id': 6,
                'nom': 'Électricité',
                'facteur_emission': 0.05,
                'unite': 'kg CO₂e/kWh'
            }
        ]
        
        return jsonify({
            'success': True,
            'energies': energies,
            'message': 'Énergies chargées avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API énergies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500