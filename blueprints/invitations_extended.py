"""
Blueprint pour les routes d'invitations étendues
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
invitations_extended_bp = Blueprint('invitations_extended', __name__)

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db, Client, Invitation
    return db, Client, Invitation

@invitations_extended_bp.route('/')
@invitations_extended_bp.route('/invitations')
def invitations():
    """Page de gestion des invitations de clients"""
    try:
        return render_template('invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@invitations_extended_bp.route('/api/clients/<client_id>/invitation-status')
def get_client_invitation_status(client_id):
    """Récupérer le statut d'invitation d'un client"""
    db, Client, Invitation = get_models()
    
    try:
        # Récupérer le client
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Récupérer l'invitation associée
        invitation = Invitation.query.filter_by(client_id=client_id).first()
        
        if invitation:
            return jsonify({
                'success': True,
                'client_id': client_id,
                'invitation_status': invitation.statut,
                'invitation_created': invitation.created_at.isoformat() if invitation.created_at else None,
                'invitation_token': invitation.token
            })
        else:
            return jsonify({
                'success': True,
                'client_id': client_id,
                'invitation_status': 'no_invitation',
                'message': 'Aucune invitation trouvée pour ce client'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'invitation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@invitations_extended_bp.route('/invitation/<token>')
def invitation_accept(token):
    """Page pour accepter/refuser une invitation"""
    db, Client, Invitation = get_models()
    
    try:
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return render_template('error.html', error='Invitation non trouvée ou expirée'), 404
        
        return render_template('invitation_accept.html', invitation=invitation)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'invitation: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@invitations_extended_bp.route('/api/invitation/<token>/reponse', methods=['POST'])
def api_invitation_reponse(token):
    """API pour accepter/refuser une invitation"""
    db, Client, Invitation = get_models()
    
    try:
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        data = request.get_json()
        reponse = data.get('reponse')
        
        if reponse not in ['accepte', 'refuse']:
            return jsonify({'success': False, 'error': 'Réponse invalide'}), 400
        
        # Mettre à jour le statut de l'invitation
        invitation.statut = reponse
        invitation.updated_at = datetime.utcnow()
        
        # Si acceptée, activer le client
        if reponse == 'accepte':
            client = Client.query.get(invitation.client_id)
            if client:
                client.statut = 'actif'
                client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Invitation {reponse}: {invitation.email}")
        
        return jsonify({
            'success': True,
            'message': f'Invitation {reponse} avec succès',
            'statut': reponse
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la réponse à l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@invitations_extended_bp.route('/api/invitations/<int:invitation_id>/resend', methods=['POST'])
def resend_invitation_admin(invitation_id):
    """Relancer une invitation"""
    db, Client, Invitation = get_models()
    
    try:
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

@invitations_extended_bp.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
def delete_invitation(invitation_id):
    """Supprimer une invitation"""
    db, Client, Invitation = get_models()
    
    try:
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


