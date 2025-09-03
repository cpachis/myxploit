"""
Blueprint pour les routes d'administration
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db, Client, Invitation
    return db, Client, Invitation

@admin_bp.route('/')
@admin_bp.route('/administration')
def administration():
    """Page d'administration"""
    try:
        return render_template('administration.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'administration: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@admin_bp.route('/clients')
def admin_clients():
    """Page d'administration des clients"""
    try:
        return render_template('admin/clients.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page admin clients: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('admin.admin_clients'))

@admin_bp.route('/invitations')
def admin_invitations():
    """Page d'administration des invitations"""
    try:
        return render_template('admin/invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page admin invitations: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('admin.admin_invitations'))

@admin_bp.route('/clients/pending')
def admin_clients_pending():
    """Page des clients en attente d'invitation"""
    try:
        return render_template('admin/clients_pending.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page clients en attente: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('admin.admin_clients_pending'))

@admin_bp.route('/api/invitations/<int:invitation_id>/resend', methods=['POST'])
def resend_invitation_admin(invitation_id):
    """Relancer une invitation"""
    try:
        db, Client, Invitation = get_models()
        
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        # Ici, vous pourriez renvoyer l'email d'invitation
        # Pour l'instant, on met juste à jour la date
        
        invitation.created_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Invitation relancée: {invitation.email}")
        
        return jsonify({
            'success': True,
            'message': 'Invitation relancée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du relancement de l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
def delete_invitation(invitation_id):
    """Supprimer une invitation"""
    try:
        db, Client, Invitation = get_models()
        
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        email_invitation = invitation.email
        db.session.delete(invitation)
        db.session.commit()
        
        logger.info(f"✅ Invitation supprimée: {email_invitation}")
        
        return jsonify({
            'success': True,
            'message': 'Invitation supprimée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client_details(client_id):
    """Récupérer les détails d'un client"""
    try:
        db, Client, Invitation = get_models()
        
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
                'created_at': client.created_at.isoformat() if client.created_at else None,
                'updated_at': client.updated_at.isoformat() if client.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails du client: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/clients', methods=['PUT'])
def update_client():
    """Mettre à jour un client"""
    try:
        db, Client, Invitation = get_models()
        
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        client = Client.query.get(data['id'])
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Mettre à jour les champs
        client.nom = data.get('nom', client.nom)
        client.email = data.get('email', client.email)
        client.telephone = data.get('telephone', client.telephone)
        client.adresse = data.get('adresse', client.adresse)
        client.siret = data.get('siret', client.siret)
        client.site_web = data.get('site_web', client.site_web)
        client.description = data.get('description', client.description)
        client.statut = data.get('statut', client.statut)
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Client mis à jour: {client.nom} (ID: {client.id})")
        return jsonify({
            'success': True,
            'message': f'Client "{client.nom}" mis à jour avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du client: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

