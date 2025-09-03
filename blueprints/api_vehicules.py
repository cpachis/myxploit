"""
Blueprint pour les routes API liées aux véhicules
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_vehicules_bp = Blueprint('api_vehicules', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_vehicules_bp.route('/vehicules', methods=['GET', 'POST'])
def api_vehicules():
    """API pour récupérer et créer des véhicules"""
    if request.method == 'GET':
        try:
            # Import des modèles depuis app.py
            from app import Vehicule, db
            
            vehicules = Vehicule.query.all()
            vehicules_data = []
            
            for v in vehicules:
                # Récupérer le nom de l'énergie si elle existe
                energie_nom = None
                if v.energie_id and v.energie:
                    energie_nom = v.energie.nom
                
                vehicules_data.append({
                    'id': v.id,
                    'nom': v.nom,
                    'type': v.type,
                    'energie_id': v.energie_id,
                    'energie_nom': energie_nom,
                    'consommation': v.consommation,
                    'emissions': v.emissions,
                    'charge_utile': v.charge_utile,
                    'description': v.description
                })
            
            return jsonify({
                'success': True,
                'vehicules': vehicules_data
            })
        
        except Exception as e:
            logger.error(f"Erreur API véhicules GET: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        """Créer un nouveau véhicule"""
        try:
            # Import des modèles depuis app.py
            from app import Vehicule, db
            
            logger.info("=== CRÉATION DE VÉHICULE ===")
            
            data = request.get_json()
            logger.info(f"📥 Données reçues: {data}")
            
            # Validation des données
            if not data:
                return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
            if not data.get('nom'):
                return jsonify({'success': False, 'error': 'Nom du véhicule requis'}), 400
            
            # Créer le véhicule
            nouveau_vehicule = Vehicule(
                nom=data['nom'],
                type=data.get('type', 'PORTEUR'),
                energie_id=data.get('energie_id'),
                charge_utile=float(data.get('capacite', 0)),
                consommation=float(data.get('consommation', 0)),
                emissions=float(data.get('emissions', 0)),
                description=data.get('description', '')
            )
            
            db.session.add(nouveau_vehicule)
            db.session.commit()
            
            logger.info(f"✅ Véhicule créé avec succès: {nouveau_vehicule.id}")
            
            return jsonify({
                'success': True,
                'message': 'Véhicule créé avec succès',
                'vehicule': {
                    'id': nouveau_vehicule.id,
                    'nom': nouveau_vehicule.nom,
                    'type': nouveau_vehicule.type,
                    'energie_id': nouveau_vehicule.energie_id,
                    'consommation': nouveau_vehicule.consommation,
                    'emissions': nouveau_vehicule.emissions,
                    'charge_utile': nouveau_vehicule.charge_utile,
                    'description': nouveau_vehicule.description
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur création véhicule: {str(e)}")
            from app import db
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            }), 500

@api_vehicules_bp.route('/vehicules/<int:vehicule_id>', methods=['PUT', 'DELETE'])
def api_vehicule_detail(vehicule_id):
    """API pour modifier et supprimer un véhicule spécifique"""
    try:
        # Import des modèles depuis app.py
        from app import Vehicule, db
        
        vehicule = Vehicule.query.get(vehicule_id)
        if not vehicule:
            return jsonify({'success': False, 'error': 'Véhicule non trouvé'}), 404
        
        if request.method == 'PUT':
            """Modifier un véhicule"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
                # Mettre à jour les champs
                if 'nom' in data:
                    vehicule.nom = data['nom']
                if 'type' in data:
                    vehicule.type = data['type']
                if 'energie_id' in data:
                    vehicule.energie_id = data['energie_id']
                if 'capacite' in data:
                    vehicule.charge_utile = float(data['capacite'])
                if 'consommation' in data:
                    vehicule.consommation = float(data['consommation'])
                if 'emissions' in data:
                    vehicule.emissions = float(data['emissions'])
                if 'description' in data:
                    vehicule.description = data['description']
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Véhicule modifié avec succès',
                    'vehicule': {
                        'id': vehicule.id,
                        'nom': vehicule.nom,
                        'type': vehicule.type,
                        'energie_id': vehicule.energie_id,
                        'consommation': vehicule.consommation,
                        'emissions': vehicule.emissions,
                        'charge_utile': vehicule.charge_utile,
                        'description': vehicule.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur modification véhicule: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la modification: {str(e)}'
                }), 500
        
        elif request.method == 'DELETE':
            """Supprimer un véhicule"""
            try:
                db.session.delete(vehicule)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Véhicule supprimé avec succès'
                })
                
            except Exception as e:
                logger.error(f"Erreur suppression véhicule: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la suppression: {str(e)}'
                }), 500
    
    except Exception as e:
        logger.error(f"Erreur API véhicule detail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_vehicules_bp.route('/vehicules/types', methods=['GET'])
def api_vehicules_types():
    """API pour récupérer les types de véhicules"""
    try:
        # Import des modèles depuis app.py
        from app import Vehicule, db
        
        # Utiliser une requête SQL directe pour éviter les problèmes de colonnes manquantes
        result = db.session.execute(db.text("SELECT id, nom, type, consommation, emissions, charge_utile FROM vehicules"))
        vehicules = result.fetchall()
        
        vehicules_data = []
        for v in vehicules:
            vehicules_data.append({
                'id': v[0],
                'nom': v[1],
                'type': v[2],
                'consommation': v[3],
                'emissions': v[4],
                'charge_utile': v[5]
            })
        
        if not vehicules_data:
            return jsonify({
                'success': True,
                'vehicules': [],
                'message': 'Aucun véhicule configuré. Veuillez d\'abord configurer des véhicules dans l\'administration.'
            })
        
        return jsonify({
            'success': True,
            'vehicules': vehicules_data
        })
        
    except Exception as e:
        logger.error(f"Erreur API types véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



