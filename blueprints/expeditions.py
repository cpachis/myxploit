"""
Blueprint pour les routes liées aux expéditions
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging

# Créer le blueprint
expeditions_bp = Blueprint('expeditions', __name__)

logger = logging.getLogger(__name__)

@expeditions_bp.route('/')
@expeditions_bp.route('/expeditions')
def expeditions():
    """Page des expéditions"""
    try:
        return render_template('expeditions.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des expéditions: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@expeditions_bp.route('/mes_expeditions')
def mes_expeditions():
    """Mes expéditions"""
    try:
        from flask import current_app
        from sqlalchemy import text
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Charger les transports depuis la base de données
        result = db.session.execute(text("""
            SELECT id, ref, date, lieu_collecte, lieu_livraison, 
                   poids_tonnes, distance_km, emis_kg, emis_tkm, 
                   niveau_calcul, type_vehicule, energie, conso_vehicule, 
                   vehicule_dedie, client, type_transport
            FROM transports 
            ORDER BY client, date DESC
        """))
        
        # Organiser les transports par client
        expeditions_par_client = {}
        total_distance = 0.0
        total_emissions = 0.0
        total_transports = 0
        
        for row in result:
            transport = {
                'id': row[0],
                'ref': row[1],
                'date': row[2].isoformat() if row[2] else None,
                'lieu_collecte': row[3],
                'lieu_livraison': row[4],
                'poids_tonnes': float(row[5]) if row[5] else 0.0,
                'distance_km': float(row[6]) if row[6] else 0.0,
                'emis_kg': float(row[7]) if row[7] else 0.0,
                'emis_tkm': float(row[8]) if row[8] else 0.0,
                'niveau_calcul': row[9],
                'type_vehicule': row[10],
                'energie': row[11],
                'conso_vehicule': float(row[12]) if row[12] else 0.0,
                'vehicule_dedie': bool(row[13]) if row[13] is not None else False,
                'client': row[14],
                'type_transport': row[15]
            }
            
            client_id = transport['client'] or 'sans_client'
            
            if client_id not in expeditions_par_client:
                expeditions_par_client[client_id] = {
                    'client': {'nom': transport['client'] or 'Sans client'},
                    'transports': [],
                    'total_distance': 0.0,
                    'total_poids': 0.0,
                    'total_emissions': 0.0
                }
            
            expeditions_par_client[client_id]['transports'].append(transport)
            expeditions_par_client[client_id]['total_distance'] += transport['distance_km']
            expeditions_par_client[client_id]['total_poids'] += transport['poids_tonnes']
            expeditions_par_client[client_id]['total_emissions'] += transport['emis_kg']
            
            total_distance += transport['distance_km']
            total_emissions += transport['emis_kg']
            total_transports += 1
        
        # Variables pour le template
        context = {
            'total_distance': total_distance,
            'total_emissions': total_emissions,
            'total_transports': total_transports,
            'expeditions_par_client': expeditions_par_client,
            'expeditions': list(expeditions_par_client.values())
        }
        
        return render_template('expeditions.html', **context)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de mes expéditions: {str(e)}")
        return render_template('error.html', error=str(e)), 500