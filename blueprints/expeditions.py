"""
Blueprint pour les routes liées aux expéditions
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

# Créer le blueprint
expeditions_bp = Blueprint('expeditions', __name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application Flask"""
    from models import create_models
    from flask import current_app
    return create_models(current_app.extensions['sqlalchemy'].db)

@expeditions_bp.route('/expeditions')
@login_required
def mes_expeditions():
    """Page principale des expéditions"""
    try:
        # Récupérer les modèles
        models = get_models()
        Transport = models['Transport']
        Client = models['Client']
        
        # Récupérer les transports de l'utilisateur connecté
        transports = Transport.query.filter_by(user_id=current_user.id).all()
        
        # Calculer les statistiques
        total_transports = len(transports)
        total_emissions = sum(transport.emis_kg or 0 for transport in transports)
        total_distance = sum(transport.distance_km or 0 for transport in transports)
        
        # Grouper par client pour les expéditions
        expeditions_par_client = {}
        for transport in transports:
            client_id = transport.client_id
            if client_id not in expeditions_par_client:
                expeditions_par_client[client_id] = {
                    'client': None,
                    'transports': [],
                    'total_emissions': 0,
                    'total_distance': 0,
                    'total_poids': 0
                }
            
            expeditions_par_client[client_id]['transports'].append(transport)
            expeditions_par_client[client_id]['total_emissions'] += transport.emis_kg or 0
            expeditions_par_client[client_id]['total_distance'] += transport.distance_km or 0
            expeditions_par_client[client_id]['total_poids'] += transport.poids_tonnes or 0
        
        # Récupérer les informations des clients
        for client_id, data in expeditions_par_client.items():
            if client_id:
                client = Client.query.get(client_id)
                data['client'] = client
        
        return render_template('expeditions.html', 
                             expeditions_par_client=expeditions_par_client,
                             total_transports=total_transports,
                             total_emissions=total_emissions,
                             total_distance=total_distance)
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des expéditions: {str(e)}")
        flash('Erreur lors du chargement des expéditions', 'error')
        return redirect(url_for('main.index'))

@expeditions_bp.route('/api/expeditions')
@login_required
def api_expeditions():
    """API pour récupérer les expéditions en JSON"""
    try:
        # Récupérer les modèles
        models = get_models()
        Transport = models['Transport']
        Client = models['Client']
        
        # Récupérer les transports de l'utilisateur connecté
        transports = Transport.query.filter_by(user_id=current_user.id).all()
        
        # Grouper par client
        expeditions_par_client = {}
        for transport in transports:
            client_id = transport.client_id or 'sans_client'
            if client_id not in expeditions_par_client:
                expeditions_par_client[client_id] = {
                    'client_id': client_id,
                    'client_nom': 'Sans client' if client_id == 'sans_client' else None,
                    'transports': [],
                    'total_emissions': 0,
                    'total_distance': 0,
                    'total_poids': 0
                }
            
            expeditions_par_client[client_id]['transports'].append({
                'id': transport.id,
                'ref': transport.ref,
                'date': transport.date.isoformat() if transport.date else None,
                'lieu_collecte': transport.lieu_collecte,
                'lieu_livraison': transport.lieu_livraison,
                'distance_km': transport.distance_km,
                'poids_tonnes': transport.poids_tonnes,
                'emis_kg': transport.emis_kg,
                'emis_tkm': transport.emis_tkm,
                'type_transport': transport.type_transport,
                'niveau_calcul': transport.niveau_calcul
            })
            
            expeditions_par_client[client_id]['total_emissions'] += transport.emis_kg or 0
            expeditions_par_client[client_id]['total_distance'] += transport.distance_km or 0
            expeditions_par_client[client_id]['total_poids'] += transport.poids_tonnes or 0
        
        # Récupérer les informations des clients
        for client_id, data in expeditions_par_client.items():
            if client_id != 'sans_client':
                client = Client.query.get(client_id)
                if client:
                    data['client_nom'] = client.nom
        
        return jsonify({
            'success': True,
            'expeditions': list(expeditions_par_client.values())
        })
    
    except Exception as e:
        logger.error(f"Erreur API expéditions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500