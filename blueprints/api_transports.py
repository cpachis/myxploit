"""
Blueprint pour les routes API liées aux transports
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_transports_bp = Blueprint('api_transports', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_transports_bp.route('/transports')
def api_transports():
    """API pour récupérer les transports"""
    try:
        from flask import current_app
        from models import create_models
        
        # Récupérer la base de données et les modèles
        db = current_app.extensions['sqlalchemy'].db
        models = create_models(db)
        Transport = models['Transport']
        
        # Récupérer tous les transports
        transports = Transport.query.order_by(Transport.id.desc()).all()
        
        # Convertir en format JSON
        transports_data = []
        for transport in transports:
            transports_data.append({
                'id': transport.id,
                'ref': transport.ref,
                'date': transport.date.isoformat() if transport.date else None,
                'lieu_collecte': transport.lieu_collecte,
                'lieu_livraison': transport.lieu_livraison,
                'poids_tonnes': transport.poids_tonnes,
                'distance_km': transport.distance_km,
                'emis_kg': transport.emis_kg,
                'emis_tkm': transport.emis_tkm,
                'niveau_calcul': transport.niveau_calcul,
                'type_vehicule': transport.type_vehicule,
                'energie': transport.energie,
                'conso_vehicule': transport.conso_vehicule,
                'vehicule_dedie': transport.vehicule_dedie,
                'client': transport.client,
                'type_transport': transport.type_transport
            })
        
        return jsonify({
            'success': True,
            'transports': transports_data,
            'message': f'{len(transports_data)} transports récupérés avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur API transports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/transports', methods=['POST'])
def create_transport():
    """API pour créer un nouveau transport"""
    try:
        from flask import current_app
        from models import create_models
        from datetime import datetime
        
        # Récupérer la base de données et les modèles
        db = current_app.extensions['sqlalchemy'].db
        models = create_models(db)
        Transport = models['Transport']
        
        # Récupérer les données de la requête
        data = request.get_json()
        
        # Créer le nouveau transport
        transport = Transport(
            ref=data.get('ref', f'T{datetime.now().strftime("%Y%m%d%H%M%S")}'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else datetime.now().date(),
            lieu_collecte=data.get('lieu_collecte', ''),
            lieu_livraison=data.get('lieu_livraison', ''),
            poids_tonnes=float(data.get('poids_tonnes', 0)),
            distance_km=float(data.get('distance_km', 0)),
            emis_kg=float(data.get('emis_kg', 0)),
            emis_tkm=float(data.get('emis_tkm', 0)),
            niveau_calcul=data.get('niveau_calcul', ''),
            type_vehicule=data.get('type_vehicule', ''),
            energie=data.get('energie', ''),
            conso_vehicule=float(data.get('conso_vehicule', 0)) if data.get('conso_vehicule') else None,
            vehicule_dedie=bool(data.get('vehicule_dedie', False)),
            client=data.get('client', ''),
            type_transport=data.get('type_transport', 'direct')
        )
        
        # Sauvegarder en base
        db.session.add(transport)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'transport': {
                'id': transport.id,
                'ref': transport.ref,
                'date': transport.date.isoformat(),
                'lieu_collecte': transport.lieu_collecte,
                'lieu_livraison': transport.lieu_livraison,
                'poids_tonnes': transport.poids_tonnes,
                'distance_km': transport.distance_km,
                'emis_kg': transport.emis_kg,
                'emis_tkm': transport.emis_tkm,
                'niveau_calcul': transport.niveau_calcul,
                'type_vehicule': transport.type_vehicule,
                'energie': transport.energie,
                'conso_vehicule': transport.conso_vehicule,
                'vehicule_dedie': transport.vehicule_dedie,
                'client': transport.client,
                'type_transport': transport.type_transport
            },
            'message': 'Transport créé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur création transport: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500