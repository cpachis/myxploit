"""
Blueprint pour les routes API liées aux clients
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_clients_bp = Blueprint('api_clients', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_clients_bp.route('/clients', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_clients():
    """API pour gérer les clients"""
    try:
        # Import des modèles depuis app.py
        from app import Client, db
        
        if request.method == 'GET':
            try:
                clients = Client.query.all()
                clients_data = []
                
                for client in clients:
                    clients_data.append({
                        'id': client.id,
                        'nom': client.nom,
                        'email': client.email,
                        'telephone': client.telephone,
                        'adresse': client.adresse,
                        'siret': client.siret,
                        'site_web': client.site_web,
                        'description': client.description,
                        'statut': client.statut,
                        'created_at': client.created_at.strftime('%Y-%m-%d %H:%M:%S') if client.created_at else None
                    })
                
                return jsonify({
                    'success': True,
                    'clients': clients_data
                })
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des clients: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                
                # Validation des données
                if not data.get('nom') or not data.get('email'):
                    return jsonify({'success': False, 'error': 'Nom et email sont obligatoires'}), 400
                
                # Vérifier si l'email existe déjà
                if Client.query.filter_by(email=data['email']).first():
                    return jsonify({'success': False, 'error': 'Un client avec cet email existe déjà'}), 400
                
                # Créer le nouveau client
                nouveau_client = Client(
                    nom=data.get('nom'),
                    email=data.get('email'),
                    telephone=data.get('telephone'),
                    adresse=data.get('adresse'),
                    siret=data.get('siret'),
                    site_web=data.get('site_web'),
                    description=data.get('description'),
                    statut=data.get('statut', 'actif')
                )
                
                db.session.add(nouveau_client)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Client créé avec succès',
                    'client': {
                        'id': nouveau_client.id,
                        'nom': nouveau_client.nom,
                        'email': nouveau_client.email,
                        'telephone': nouveau_client.telephone,
                        'adresse': nouveau_client.adresse,
                        'siret': nouveau_client.siret,
                        'site_web': nouveau_client.site_web,
                        'description': nouveau_client.description,
                        'statut': nouveau_client.statut
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du client: {str(e)}")
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                client_id = data.get('id')
                
                if not client_id:
                    return jsonify({'success': False, 'error': 'ID du client requis'}), 400
                
                client = Client.query.get(client_id)
                if not client:
                    return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
                
                # Mettre à jour les champs
                if 'nom' in data:
                    client.nom = data['nom']
                if 'email' in data:
                    client.email = data['email']
                if 'telephone' in data:
                    client.telephone = data['telephone']
                if 'adresse' in data:
                    client.adresse = data['adresse']
                if 'siret' in data:
                    client.siret = data['siret']
                if 'site_web' in data:
                    client.site_web = data['site_web']
                if 'description' in data:
                    client.description = data['description']
                if 'statut' in data:
                    client.statut = data['statut']
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Client modifié avec succès',
                    'client': {
                        'id': client.id,
                        'nom': client.nom,
                        'email': client.email,
                        'telephone': client.telephone,
                        'adresse': client.adresse,
                        'siret': client.siret,
                        'site_web': client.site_web,
                        'description': client.description,
                        'statut': client.statut
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur lors de la modification du client: {str(e)}")
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
        
        elif request.method == 'DELETE':
            try:
                data = request.get_json()
                client_id = data.get('id')
                
                if not client_id:
                    return jsonify({'success': False, 'error': 'ID du client requis'}), 400
                
                client = Client.query.get(client_id)
                if not client:
                    return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
                
                db.session.delete(client)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Client supprimé avec succès'
                })
                
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du client: {str(e)}")
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Erreur API clients: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_clients_bp.route('/clients/<int:client_id>', methods=['DELETE'])
def api_client_delete(client_id):
    """API pour supprimer un client spécifique"""
    try:
        # Import des modèles depuis app.py
        from app import Client, db
        
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client supprimé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du client: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_clients_bp.route('/clients/<client_id>/invitation-status')
def api_client_invitation_status(client_id):
    """API pour récupérer le statut d'invitation d'un client"""
    try:
        # Import des modèles depuis app.py
        from app import Client, Invitation, db
        
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Récupérer la dernière invitation
        invitation = Invitation.query.filter_by(client_id=client_id).order_by(Invitation.created_at.desc()).first()
        
        if invitation:
            return jsonify({
                'success': True,
                'client_id': client_id,
                'invitation_status': invitation.statut,
                'invitation_date': invitation.created_at.strftime('%Y-%m-%d %H:%M:%S') if invitation.created_at else None,
                'invitation_id': invitation.id
            })
        else:
            return jsonify({
                'success': True,
                'client_id': client_id,
                'invitation_status': 'non_invite',
                'invitation_date': None,
                'invitation_id': None
            })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'invitation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_clients_bp.route('/clients/<int:client_id>', methods=['GET'])
def api_client_detail(client_id):
    """API pour récupérer les détails d'un client spécifique"""
    try:
        # Import des modèles depuis app.py
        from app import Client, db
        
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        return jsonify({
            'success': True,
            'client': {
                'id': client.id,
                'nom': client.nom,
                'email': client.email,
                'telephone': client.telephone,
                'adresse': client.adresse,
                'siret': client.siret,
                'site_web': client.site_web,
                'description': client.description,
                'statut': client.statut,
                'created_at': client.created_at.strftime('%Y-%m-%d %H:%M:%S') if client.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du client: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_clients_bp.route('/clients', methods=['PUT'])
def api_clients_update():
    """API pour mettre à jour un client (route alternative)"""
    try:
        # Import des modèles depuis app.py
        from app import Client, db
        
        data = request.get_json()
        client_id = data.get('id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'ID du client requis'}), 400
        
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Mettre à jour les champs
        if 'nom' in data:
            client.nom = data['nom']
        if 'email' in data:
            client.email = data['email']
        if 'telephone' in data:
            client.telephone = data['telephone']
        if 'adresse' in data:
            client.adresse = data['adresse']
        if 'siret' in data:
            client.siret = data['siret']
        if 'site_web' in data:
            client.site_web = data['site_web']
        if 'description' in data:
            client.description = data['description']
        if 'statut' in data:
            client.statut = data['statut']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client modifié avec succès',
            'client': {
                'id': client.id,
                'nom': client.nom,
                'email': client.email,
                'telephone': client.telephone,
                'adresse': client.adresse,
                'siret': client.siret,
                'site_web': client.site_web,
                'description': client.description,
                'statut': client.statut
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification du client: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500




