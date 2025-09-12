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
    """API pour récupérer les énergies depuis la base de données"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Charger les énergies depuis la base de données
        result = db.session.execute(text("""
            SELECT id, nom, unite, facteur
            FROM energies 
            ORDER BY nom
        """))
        
        energies = []
        for row in result:
            energies.append({
                'id': row[0],
                'nom': row[1],
                'unite': row[2] or 'kg CO₂e/L',
                'facteur_emission': float(row[3]) if row[3] else 0.0
            })
        
        # Si aucune énergie en base, utiliser les valeurs par défaut
        if not energies:
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
            'message': f'{len(energies)} énergies chargées avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API énergies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500