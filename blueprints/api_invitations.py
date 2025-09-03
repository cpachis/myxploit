"""
Blueprint pour les routes API liées aux invitations
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import logging
import secrets

# Créer le blueprint
api_invitations_bp = Blueprint('api_invitations', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_invitations_bp.route('/invitations', methods=['GET', 'POST'])
def api_invitations():
    """API pour gérer les invitations"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, db, envoyer_email_invitation
        
        if request.method == 'GET':
            try:
                invitations = Invitation.query.order_by(Invitation.created_at.desc()).all()
                invitations_data = []
                
                for inv in invitations:
                    invitations_data.append({
                        'id': inv.id,
                        'email': inv.email,
                        'statut': inv.statut,
                        'nom_entreprise': inv.nom_entreprise,
                        'nom_utilisateur': inv.nom_utilisateur,
                        'date_invitation': inv.date_invitation.strftime('%d/%m/%Y %H:%M') if inv.date_invitation else None,
                        'date_reponse': inv.date_reponse.strftime('%d/%m/%Y %H:%M') if inv.date_reponse else None,
                        'message_personnalise': inv.message_personnalise
                    })
                
                return jsonify({
                    'success': True,
                    'invitations': invitations_data
                })
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des invitations: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                email = data.get('email')
                message_personnalise = data.get('message_personnalise', '')
                
                if not email:
                    return jsonify({'success': False, 'error': 'Email requis'}), 400
                
                # Vérifier si l'email n'est pas déjà invité
                existing_invitation = Invitation.query.filter_by(email=email).first()
                if existing_invitation:
                    return jsonify({'success': False, 'error': 'Une invitation existe déjà pour cet email'}), 400
                
                # Générer un token unique
                token = secrets.token_urlsafe(32)
                
                # Créer l'invitation
                invitation = Invitation(
                    email=email,
                    token=token,
                    statut='en_attente',
                    nom_entreprise=data.get('nom_entreprise', ''),
                    nom_utilisateur=data.get('nom_utilisateur', ''),
                    message_personnalise=message_personnalise,
                    date_invitation=datetime.now()
                )
                
                db.session.add(invitation)
                db.session.commit()
                
                # Envoyer l'email d'invitation
                try:
                    envoyer_email_invitation(invitation)
                    logger.info(f"Email d'invitation envoyé à {email}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
                    # Ne pas faire échouer la création de l'invitation si l'email échoue
                
                return jsonify({
                    'success': True,
                    'message': 'Invitation créée et email envoyé avec succès',
                    'invitation': {
                        'id': invitation.id,
                        'email': invitation.email,
                        'statut': invitation.statut,
                        'token': invitation.token
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'invitation: {str(e)}")
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Erreur API invitations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_invitations_bp.route('/invitations/<int:invitation_id>/resend', methods=['POST'])
def api_invitation_resend(invitation_id):
    """API pour renvoyer une invitation"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, db, envoyer_email_invitation
        
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        # Vérifier que l'invitation est en attente
        if invitation.statut != 'en_attente':
            return jsonify({'success': False, 'error': 'Seules les invitations en attente peuvent être renvoyées'}), 400
        
        # Renvoyer l'email
        try:
            envoyer_email_invitation(invitation)
            logger.info(f"Email d'invitation renvoyé à {invitation.email}")
            
            return jsonify({
                'success': True,
                'message': 'Invitation renvoyée avec succès'
            })
        except Exception as e:
            logger.error(f"Erreur lors du renvoi de l'email: {str(e)}")
            return jsonify({'success': False, 'error': f'Erreur lors du renvoi: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Erreur lors du renvoi de l'invitation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_invitations_bp.route('/invitation/<token>')
def api_invitation_by_token(token):
    """API pour récupérer une invitation par son token"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, db
        
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        return jsonify({
            'success': True,
            'invitation': {
                'id': invitation.id,
                'email': invitation.email,
                'statut': invitation.statut,
                'nom_entreprise': invitation.nom_entreprise,
                'nom_utilisateur': invitation.nom_utilisateur,
                'message_personnalise': invitation.message_personnalise,
                'date_invitation': invitation.date_invitation.strftime('%d/%m/%Y %H:%M') if invitation.date_invitation else None,
                'date_reponse': invitation.date_reponse.strftime('%d/%m/%Y %H:%M') if invitation.date_reponse else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'invitation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_invitations_bp.route('/invitation/<token>/reponse', methods=['POST'])
def api_invitation_reponse(token):
    """API pour traiter la réponse à une invitation"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, db
        
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        data = request.get_json()
        reponse = data.get('reponse')
        
        if reponse not in ['accepte', 'refuse']:
            return jsonify({'success': False, 'error': 'Réponse invalide'}), 400
        
        # Mettre à jour l'invitation
        invitation.statut = reponse
        invitation.date_reponse = datetime.now()
        
        if reponse == 'accepte':
            # Créer un utilisateur client
            from app import User
            nouveau_user = User(
                email=invitation.email,
                nom=invitation.nom_utilisateur or invitation.email.split('@')[0],
                role='client',
                statut='actif'
            )
            db.session.add(nouveau_user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Invitation {reponse}e avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la réponse: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_invitations_bp.route('/invitations/<int:invitation_id>', methods=['DELETE'])
def api_invitation_delete(invitation_id):
    """API pour supprimer une invitation"""
    try:
        # Import des modèles depuis app.py
        from app import Invitation, db
        
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        db.session.delete(invitation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Invitation supprimée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



