"""
Blueprint pour les routes liées aux invitations
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
invitations_bp = Blueprint('invitations', __name__)

logger = logging.getLogger(__name__)

@invitations_bp.route('/')
def invitations_list():
    """Page de liste des invitations"""
    try:
        return render_template('invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page invitations: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('invitations.invitations_list'))

@invitations_bp.route('/<token>')
def invitation_detail(token):
    """Page de détail d'une invitation"""
    try:
        return render_template('invitation_detail.html', token=token)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'invitation {token}: {str(e)}")
        flash('Erreur lors du chargement de l\'invitation', 'error')
        return redirect(url_for('invitations.invitations_list'))

@invitations_bp.route('/accept/<token>')
def invitation_accept(token):
    """Page pour accepter/refuser une invitation"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation
        
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return render_template('error.html', error='Invitation non trouvée ou expirée'), 404
        
        return render_template('invitation_accept.html', invitation=invitation)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'invitation: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@invitations_bp.route('/api/<token>/reponse', methods=['POST'])
def api_invitation_reponse(token):
    """API pour accepter/refuser une invitation"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, Client, db
        
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
