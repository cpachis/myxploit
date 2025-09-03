"""
Blueprint pour les routes liées aux clients
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging

# Créer le blueprint
clients_bp = Blueprint('clients', __name__)

logger = logging.getLogger(__name__)

@clients_bp.route('/')
@clients_bp.route('/clients')
def clients():
    """Page de gestion des clients (côté client)"""
    try:
        return render_template('clients.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@clients_bp.route('/transporteurs')
def transporteurs_list():
    """Page de liste des transporteurs"""
    try:
        return render_template('transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page transporteurs: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('clients.transporteurs_list'))

@clients_bp.route('/mon-entreprise')
def mon_entreprise():
    """Page de gestion de l'entreprise"""
    try:
        return render_template('mon_entreprise.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page mon entreprise: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('clients.mon_entreprise'))

@clients_bp.route('/api/<client_id>/invitation-status')
def get_client_invitation_status(client_id):
    """Récupérer le statut d'invitation d'un client"""
    try:
        # Import des modèles depuis app.py
        from app import Client, Invitation
        
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

@clients_bp.route('/api/clients')
def api_clients():
    """API pour récupérer la liste des clients"""
    try:
        import json
        import os
        
        # Charger les clients depuis le fichier JSON
        clients_path = os.path.join('data', 'clients.json')
        
        if not os.path.exists(clients_path):
            return jsonify({
                'success': True,
                'clients': [],
                'message': 'Aucun client configuré'
            })
        
        with open(clients_path, 'r', encoding='utf-8') as f:
            clients_data = json.load(f)
        
        # Convertir en format pour le dropdown
        clients_list = []
        for client_id, client_info in clients_data.items():
            clients_list.append({
                'id': client_id,
                'nom': client_info.get('nom', client_id),
                'adresse': client_info.get('adresse', ''),
                'email': client_info.get('email', '')
            })
        
        return jsonify({
            'success': True,
            'clients': clients_list
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
