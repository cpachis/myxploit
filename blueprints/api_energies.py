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
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energies = Energie.query.all()
        energies_data = []
        
        for e in energies:
            energies_data.append({
                'id': e.id,
                'nom': e.nom,
                'identifiant': e.identifiant,
                'unite': e.unite,
                'facteur': e.facteur,
                'description': e.description,
                'phase_amont': getattr(e, 'phase_amont', 0.0),
                'phase_fonctionnement': getattr(e, 'phase_fonctionnement', 0.0),
                'donnees_supplementaires': getattr(e, 'donnees_supplementaires', {})
            })
        
        return jsonify({
            'success': True,
            'energies': energies_data
        })
    
    except Exception as e:
        logger.error(f"Erreur API énergies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_energies_bp.route('/energies', methods=['POST'])
def api_energies_create():
    """API pour créer une nouvelle énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        logger.info("=== CRÉATION D'ÉNERGIE ===")
        
        data = request.get_json()
        logger.info(f"📥 Données reçues: {data}")
        
        # Validation des données
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
            
        if not data.get('nom'):
            return jsonify({'success': False, 'error': 'Nom de l\'énergie requis'}), 400
        
        # Créer l'énergie
        nouvelle_energie = Energie(
            nom=data['nom'],
            identifiant=data.get('identifiant', ''),
            unite=data.get('unite', 'kg CO2e'),
            facteur=float(data.get('facteur', 0.0)),
            description=data.get('description', ''),
            phase_amont=float(data.get('phase_amont', 0.0)),
            phase_fonctionnement=float(data.get('phase_fonctionnement', 0.0)),
            donnees_supplementaires=data.get('donnees_supplementaires', {})
        )
        
        db.session.add(nouvelle_energie)
        db.session.commit()
        
        logger.info(f"✅ Énergie créée avec succès: {nouvelle_energie.id}")
        
        return jsonify({
            'success': True,
            'message': 'Énergie créée avec succès',
            'energie': {
                'id': nouvelle_energie.id,
                'nom': nouvelle_energie.nom,
                'identifiant': nouvelle_energie.identifiant,
                'unite': nouvelle_energie.unite,
                'facteur': nouvelle_energie.facteur,
                'description': nouvelle_energie.description,
                'phase_amont': nouvelle_energie.phase_amont,
                'phase_fonctionnement': nouvelle_energie.phase_fonctionnement,
                'donnees_supplementaires': nouvelle_energie.donnees_supplementaires
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur création énergie: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la création: {str(e)}'
        }), 500

@api_energies_bp.route('/energies/<int:energie_id>', methods=['PUT'])
def api_energie_update(energie_id):
    """API pour modifier une énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energie = Energie.query.get(energie_id)
        if not energie:
            return jsonify({'success': False, 'error': 'Énergie non trouvée'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
        
        # Mettre à jour les champs
        if 'nom' in data:
            energie.nom = data['nom']
        if 'identifiant' in data:
            energie.identifiant = data['identifiant']
        if 'unite' in data:
            energie.unite = data['unite']
        if 'facteur' in data:
            energie.facteur = float(data['facteur'])
        if 'description' in data:
            energie.description = data['description']
        if 'phase_amont' in data:
            energie.phase_amont = float(data['phase_amont'])
        if 'phase_fonctionnement' in data:
            energie.phase_fonctionnement = float(data['phase_fonctionnement'])
        if 'donnees_supplementaires' in data:
            energie.donnees_supplementaires = data['donnees_supplementaires']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Énergie modifiée avec succès',
            'energie': {
                'id': energie.id,
                'nom': energie.nom,
                'identifiant': energie.identifiant,
                'unite': energie.unite,
                'facteur': energie.facteur,
                'description': energie.description,
                'phase_amont': energie.phase_amont,
                'phase_fonctionnement': energie.phase_fonctionnement,
                'donnees_supplementaires': energie.donnees_supplementaires
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur modification énergie: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la modification: {str(e)}'
        }), 500

@api_energies_bp.route('/energies/<int:energie_id>', methods=['DELETE'])
def api_energie_delete(energie_id):
    """API pour supprimer une énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energie = Energie.query.get(energie_id)
        if not energie:
            return jsonify({'success': False, 'error': 'Énergie non trouvée'}), 404
        
        db.session.delete(energie)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Énergie supprimée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur suppression énergie: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la suppression: {str(e)}'
        }), 500

@api_energies_bp.route('/energies/<int:energie_id>/facteurs', methods=['PUT'])
def api_energie_facteurs(energie_id):
    """API pour mettre à jour les facteurs d'émission d'une énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energie = Energie.query.get(energie_id)
        if not energie:
            return jsonify({'success': False, 'error': 'Énergie non trouvée'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
        
        # Mettre à jour les facteurs
        if 'facteur' in data:
            energie.facteur = float(data['facteur'])
        if 'phase_amont' in data:
            energie.phase_amont = float(data['phase_amont'])
        if 'phase_fonctionnement' in data:
            energie.phase_fonctionnement = float(data['phase_fonctionnement'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Facteurs d\'émission mis à jour avec succès',
            'energie': {
                'id': energie.id,
                'nom': energie.nom,
                'facteur': energie.facteur,
                'phase_amont': energie.phase_amont,
                'phase_fonctionnement': energie.phase_fonctionnement
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour facteurs: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@api_energies_bp.route('/energies/<int:energie_id>/donnees', methods=['POST'])
def api_energie_donnees_add(energie_id):
    """API pour ajouter des données supplémentaires à une énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energie = Energie.query.get(energie_id)
        if not energie:
            return jsonify({'success': False, 'error': 'Énergie non trouvée'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
        
        # Ajouter les données supplémentaires
        if 'donnees_supplementaires' in data:
            if not energie.donnees_supplementaires:
                energie.donnees_supplementaires = {}
            energie.donnees_supplementaires.update(data['donnees_supplementaires'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Données supplémentaires ajoutées avec succès',
            'energie': {
                'id': energie.id,
                'nom': energie.nom,
                'donnees_supplementaires': energie.donnees_supplementaires
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur ajout données: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'ajout: {str(e)}'
        }), 500

@api_energies_bp.route('/energies/<int:energie_id>/donnees/<nom_donnee>', methods=['DELETE'])
def api_energie_donnees_delete(energie_id, nom_donnee):
    """API pour supprimer une donnée supplémentaire d'une énergie"""
    try:
        # Import des modèles depuis app.py
        from app import Energie, db
        
        energie = Energie.query.get(energie_id)
        if not energie:
            return jsonify({'success': False, 'error': 'Énergie non trouvée'}), 404
        
        # Supprimer la donnée
        if energie.donnees_supplementaires and nom_donnee in energie.donnees_supplementaires:
            del energie.donnees_supplementaires[nom_donnee]
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Donnée "{nom_donnee}" supprimée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Donnée "{nom_donnee}" non trouvée'
            }), 404
        
    except Exception as e:
        logger.error(f"Erreur suppression donnée: {str(e)}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la suppression: {str(e)}'
        }), 500




