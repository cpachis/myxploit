"""
Blueprint pour les routes API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_bp.route('/dashboard', methods=['GET'])
def api_dashboard():
    """API pour récupérer les données du dashboard"""
    try:
        # Simulation de données de dashboard
        dashboard_data = {
            'statistiques': {
                'total_transports': 25,
                'transports_ce_mois': 8,
                'emissions_total': 1250.5,
                'emissions_ce_mois': 320.8,
                'clients_actifs': 12,
                'transporteurs_actifs': 6
            },
            'graphiques': {
                'emissions_par_mois': [
                    {'mois': 'Jan', 'emissions': 280.5},
                    {'mois': 'Fév', 'emissions': 320.8},
                    {'mois': 'Mar', 'emissions': 295.2},
                    {'mois': 'Avr', 'emissions': 354.0}
                ],
                'transports_par_type': [
                    {'type': 'Routier', 'nombre': 15},
                    {'type': 'Ferroviaire', 'nombre': 5},
                    {'type': 'Maritime', 'nombre': 3},
                    {'type': 'Aérien', 'nombre': 2}
                ]
            },
            'transports_recents': [
                {
                    'id': 1,
                    'reference': 'TR-001',
                    'date': '2024-01-15',
                    'client': 'Client Test 1',
                    'emissions': 45.5,
                    'statut': 'terminé'
                },
                {
                    'id': 2,
                    'reference': 'TR-002',
                    'date': '2024-01-16',
                    'client': 'Client Test 2',
                    'emissions': 78.2,
                    'statut': 'en_cours'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données du dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
