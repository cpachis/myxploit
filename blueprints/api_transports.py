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
        from flask_sqlalchemy import SQLAlchemy
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Utiliser une requête SQL directe pour éviter les problèmes d'import
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT id, ref, date, lieu_collecte, lieu_livraison, 
                   poids_tonnes, distance_km, emis_kg, emis_tkm, 
                   niveau_calcul, type_vehicule, energie, conso_vehicule, 
                   vehicule_dedie, client, type_transport
            FROM transports 
            ORDER BY id DESC
        """))
        
        # Convertir en format JSON
        transports_data = []
        for row in result:
            transports_data.append({
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
        from datetime import datetime
        
        # Récupérer la base de données
        db = current_app.extensions['sqlalchemy']
        
        # Récupérer les données de la requête
        data = request.get_json()
        
        # Utiliser une requête SQL directe pour insérer
        from sqlalchemy import text
        ref = data.get('ref', f'T{datetime.now().strftime("%Y%m%d%H%M%S")}')
        date = datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else datetime.now().date()
        
        db.session.execute(text("""
            INSERT INTO transports (ref, date, lieu_collecte, lieu_livraison, poids_tonnes, 
                                  distance_km, emis_kg, emis_tkm, niveau_calcul, type_vehicule, 
                                  energie, conso_vehicule, vehicule_dedie, client, type_transport)
            VALUES (:ref, :date, :lieu_collecte, :lieu_livraison, :poids_tonnes, 
                    :distance_km, :emis_kg, :emis_tkm, :niveau_calcul, :type_vehicule, 
                    :energie, :conso_vehicule, :vehicule_dedie, :client, :type_transport)
        """), {
            'ref': ref,
            'date': date,
            'lieu_collecte': data.get('lieu_collecte', ''),
            'lieu_livraison': data.get('lieu_livraison', ''),
            'poids_tonnes': float(data.get('poids_tonnes', 0)),
            'distance_km': float(data.get('distance_km', 0)),
            'emis_kg': float(data.get('emis_kg', 0)),
            'emis_tkm': float(data.get('emis_tkm', 0)),
            'niveau_calcul': data.get('niveau_calcul', ''),
            'type_vehicule': data.get('type_vehicule', ''),
            'energie': data.get('energie', ''),
            'conso_vehicule': float(data.get('conso_vehicule', 0)) if data.get('conso_vehicule') else None,
            'vehicule_dedie': bool(data.get('vehicule_dedie', False)),
            'client': data.get('client', ''),
            'type_transport': data.get('type_transport', 'direct')
        })
        
        db.session.commit()
        
        # Récupérer l'ID du transport créé
        result = db.session.execute(text("SELECT id FROM transports WHERE ref = :ref"), {'ref': ref})
        transport_id = result.fetchone()[0]
        
        return jsonify({
            'success': True,
            'transport': {
                'id': transport_id,
                'ref': ref,
                'date': date.isoformat(),
                'lieu_collecte': data.get('lieu_collecte', ''),
                'lieu_livraison': data.get('lieu_livraison', ''),
                'poids_tonnes': float(data.get('poids_tonnes', 0)),
                'distance_km': float(data.get('distance_km', 0)),
                'emis_kg': float(data.get('emis_kg', 0)),
                'emis_tkm': float(data.get('emis_tkm', 0)),
                'niveau_calcul': data.get('niveau_calcul', ''),
                'type_vehicule': data.get('type_vehicule', ''),
                'energie': data.get('energie', ''),
                'conso_vehicule': float(data.get('conso_vehicule', 0)) if data.get('conso_vehicule') else 0.0,
                'vehicule_dedie': bool(data.get('vehicule_dedie', False)),
                'client': data.get('client', ''),
                'type_transport': data.get('type_transport', 'direct')
            },
            'message': 'Transport créé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur création transport: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500