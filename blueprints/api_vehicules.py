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
    """API pour récupérer les véhicules depuis la base de données"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Charger les véhicules depuis la base de données
        result = db.session.execute(text("""
            SELECT id, nom, type, consommation, emissions, charge_utile, created_at
            FROM vehicules 
            ORDER BY nom
        """))
        
        vehicules = []
        for row in result:
            vehicules.append({
                'id': row[0],
                'nom': row[1],
                'type': row[2],
                'consommation': float(row[3]) if row[3] else 0.0,
                'emissions': float(row[4]) if row[4] else 0.0,
                'charge_utile': float(row[5]) if row[5] else 0.0,
                'created_at': row[6].isoformat() if row[6] else None
            })
        
        return jsonify({
            'success': True,
            'vehicules': vehicules,
            'message': f'{len(vehicules)} véhicules chargés avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules/types')
def api_vehicules_types():
    """API pour récupérer les types de véhicules depuis la base de données"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Charger les types de véhicules depuis la base de données
        result = db.session.execute(text("""
            SELECT id, nom, type, consommation, emissions, charge_utile
            FROM vehicules 
            ORDER BY nom
        """))
        
        types_vehicules = []
        for row in result:
            types_vehicules.append({
                'id': row[0],
                'nom': row[1],
                'type': row[2],
                'consommation_base': float(row[3]) if row[3] else 0.0,
                'facteur_emission': float(row[4]) if row[4] else 3.1,
                'charge_utile_max': float(row[5]) if row[5] else 0.0
            })
        
        # Si aucun véhicule en base, utiliser les valeurs par défaut
        if not types_vehicules:
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
            'message': f'{len(types_vehicules)} types de véhicules chargés avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API types véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules', methods=['POST'])
def create_vehicule():
    """API pour créer un nouveau véhicule"""
    try:
        from flask import current_app
        from sqlalchemy import text
        from datetime import datetime
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Récupérer les données de la requête
        data = request.get_json()
        
        # Insérer le nouveau véhicule
        db.session.execute(text("""
            INSERT INTO vehicules (nom, type, consommation, emissions, charge_utile, created_at)
            VALUES (:nom, :type, :consommation, :emissions, :charge_utile, :created_at)
        """), {
            'nom': data.get('nom', ''),
            'type': data.get('type', ''),
            'consommation': float(data.get('consommation', 0)),
            'emissions': float(data.get('emissions', 0)),
            'charge_utile': float(data.get('charge_utile', 0)),
            'created_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        # Récupérer l'ID du véhicule créé
        result = db.session.execute(text("SELECT last_insert_rowid()"))
        vehicule_id = result.fetchone()[0]
        
        return jsonify({
            'success': True,
            'vehicule': {
                'id': vehicule_id,
                'nom': data.get('nom', ''),
                'type': data.get('type', ''),
                'consommation': float(data.get('consommation', 0)),
                'emissions': float(data.get('emissions', 0)),
                'charge_utile': float(data.get('charge_utile', 0))
            },
            'message': 'Véhicule créé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur création véhicule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules/<int:vehicule_id>', methods=['PUT'])
def update_vehicule(vehicule_id):
    """API pour modifier un véhicule"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Récupérer les données de la requête
        data = request.get_json()
        
        # Mettre à jour le véhicule
        db.session.execute(text("""
            UPDATE vehicules 
            SET nom = :nom, type = :type, consommation = :consommation, 
                emissions = :emissions, charge_utile = :charge_utile
            WHERE id = :id
        """), {
            'id': vehicule_id,
            'nom': data.get('nom', ''),
            'type': data.get('type', ''),
            'consommation': float(data.get('consommation', 0)),
            'emissions': float(data.get('emissions', 0)),
            'charge_utile': float(data.get('charge_utile', 0))
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Véhicule modifié avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur modification véhicule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules/<int:vehicule_id>', methods=['DELETE'])
def delete_vehicule(vehicule_id):
    """API pour supprimer un véhicule"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Supprimer le véhicule
        db.session.execute(text("DELETE FROM vehicules WHERE id = :id"), {'id': vehicule_id})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Véhicule supprimé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur suppression véhicule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500