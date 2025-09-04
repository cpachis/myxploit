"""
Blueprint pour les routes API liées aux transports
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Créer le blueprint
api_transports_bp = Blueprint('api_transports', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

def calculer_emissions_transport(distance_km, consommation_l_100km, facteur_emission):
    """
    Calcule les émissions CO2e d'un transport
    
    Formule: Émissions CO2e (kg) = (distance/100) × consommation × facteur d'émissions
    
    Args:
        distance_km (float): Distance en kilomètres
        consommation_l_100km (float): Consommation en L/100km
        facteur_emission (float): Facteur d'émission en kg CO2e/L
    
    Returns:
        dict: {'emis_kg': float, 'emis_tkm': float}
    """
    try:
        # Calcul de la consommation totale en litres
        consommation_totale = (distance_km / 100) * consommation_l_100km
        
        # Calcul des émissions en kg CO2e
        emis_kg = consommation_totale * facteur_emission
        
        return {
            'success': True,
            'emis_kg': emis_kg,
            'consommation_totale': consommation_totale
        }
    except Exception as e:
        logger.error(f"Erreur lors du calcul des émissions: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def charger_facteurs_emission():
    """Charge les facteurs d'émission depuis le fichier energies.json"""
    try:
        import json
        import os
        
        energies_path = os.path.join('data', 'energies.json')
        if not os.path.exists(energies_path):
            logger.warning("Fichier energies.json non trouvé")
            return {}
        
        with open(energies_path, 'r', encoding='utf-8') as f:
            energies_data = json.load(f)
        
        # Extraire les facteurs d'émission
        facteurs = {}
        for energie_id, energie_info in energies_data.items():
            facteur = energie_info.get('facteur', 2.7)  # Valeur par défaut
            # Convertir en float si c'est une chaîne
            if isinstance(facteur, str):
                try:
                    facteur = float(facteur)
                except ValueError:
                    facteur = 2.7
            facteurs[energie_id] = facteur
        
        return facteurs
    except Exception as e:
        logger.error(f"Erreur lors du chargement des facteurs d'émission: {str(e)}")
        return {}

@api_transports_bp.route('/transports/recalculer-emissions', methods=['POST'])
def recalculer_emissions():
    """Endpoint pour recalculer les émissions de tous les transports"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        data = request.get_json()
        action = data.get('action', 'recalculer_tous')
        
        logger.info(f"Recalcul des émissions - Action: {action}")
        
        if action == 'recalculer_tous':
            # Récupérer tous les transports
            transports = Transport.query.all()
            logger.info(f"Recalcul de {len(transports)} transports")
            
            succes = 0
            erreurs = 0
            resultats = []
            
            # Charger les facteurs d'émission
            facteurs_emission = charger_facteurs_emission()
            
            for transport in transports:
                try:
                    # Calculer les émissions si les données sont disponibles
                    if (transport.distance_km and transport.conso_vehicule and 
                        transport.energie and transport.poids_tonnes):
                        
                        # Récupérer le facteur d'émission
                        facteur = facteurs_emission.get(transport.energie, 2.7)
                        
                        # Calculer les émissions
                        resultat_calcul = calculer_emissions_transport(
                            transport.distance_km,
                            transport.conso_vehicule,
                            facteur
                        )
                        
                        if resultat_calcul['success']:
                            # Mettre à jour les émissions
                            transport.emis_kg = resultat_calcul['emis_kg']
                            transport.emis_tkm = resultat_calcul['emis_kg'] / (transport.poids_tonnes * transport.distance_km)
                            
                            succes += 1
                            
                            resultats.append({
                                'ref': transport.ref,
                                'emis_kg': transport.emis_kg,
                                'emis_tkm': transport.emis_tkm,
                                'success': True
                            })
                            
                            logger.info(f"Transport {transport.ref}: Émissions recalculées - {transport.emis_kg:.2f} kg CO2e")
                        else:
                            erreurs += 1
                            resultats.append({
                                'ref': transport.ref,
                                'error': resultat_calcul['error'],
                                'success': False
                            })
                    else:
                        # Données insuffisantes, conserver les émissions existantes
                        succes += 1
                        
                        resultats.append({
                            'ref': transport.ref,
                            'emis_kg': transport.emis_kg or 0,
                            'emis_tkm': transport.emis_tkm or 0,
                            'success': True,
                            'message': 'Données insuffisantes, émissions conservées'
                        })
                        
                        logger.info(f"Transport {transport.ref}: Données insuffisantes, émissions conservées")
                        
                except Exception as e:
                    erreurs += 1
                    logger.error(f"Erreur pour le transport {transport.ref}: {str(e)}")
                    
                    resultats.append({
                        'ref': transport.ref,
                        'error': str(e),
                        'success': False
                    })
            
            # Sauvegarder toutes les modifications
            try:
                db.session.commit()
                logger.info(f"Base de données mise à jour: {succes} succès, {erreurs} erreurs")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la sauvegarde: {str(e)}'
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Recalcul terminé: {succes} succès, {erreurs} erreurs',
                'succes': succes,
                'erreurs': erreurs,
                'resultats': resultats
            })
            
        else:
            return jsonify({
                'success': False,
                'error': f'Action non reconnue: {action}'
            }), 400
            
    except Exception as e:
        logger.error(f"Erreur lors du recalcul des émissions: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@api_transports_bp.route('/transports/liste-mise-a-jour')
def liste_transports_mise_a_jour():
    """Endpoint pour récupérer la liste des transports avec les émissions mises à jour"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        logger.info("Récupération de la liste des transports mise à jour")
        
        # Récupérer tous les transports
        transports = Transport.query.all()
        transports_data = []
        
        for transport in transports:
            transports_data.append({
                'id': transport.id,
                'ref': transport.ref,
                'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                'date_iso': transport.date.strftime('%Y-%m-%d') if transport.date else None,  # Format ISO pour les champs date
                'lieu_collecte': transport.lieu_collecte,
                'lieu_livraison': transport.lieu_livraison,
                'poids_tonnes': transport.poids_tonnes,
                'distance_km': transport.distance_km,
                'emis_kg': transport.emis_kg,
                'emis_tkm': transport.emis_tkm,
                'type_transport': transport.type_transport,
                'niveau_calcul': transport.niveau_calcul,
                'type_vehicule': transport.type_vehicule,
                'energie': transport.energie,
                'conso_vehicule': transport.conso_vehicule,
                'vehicule_dedie': transport.vehicule_dedie,
                'client': transport.client,
                'transporteur': transport.transporteur,
                'description': transport.description,
                'created_at': transport.created_at.strftime('%d/%m/%Y %H:%M') if transport.created_at else None,
                'updated_at': transport.updated_at.strftime('%d/%m/%Y %H:%M') if transport.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'transports': transports_data,
            'total': len(transports_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des transports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/transports', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_transports():
    """API pour gérer les transports"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        if request.method == 'GET':
            """Récupérer tous les transports"""
            try:
                transports = Transport.query.all()
                transports_data = []
                
                for transport in transports:
                    transports_data.append({
                        'id': transport.id,
                        'ref': transport.ref,
                        'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                        'date_iso': transport.date.strftime('%Y-%m-%d') if transport.date else None,  # Format ISO pour les champs date
                        'lieu_collecte': transport.lieu_collecte,
                        'lieu_livraison': transport.lieu_livraison,
                        'poids_tonnes': transport.poids_tonnes,
                        'distance_km': transport.distance_km,
                        'emis_kg': transport.emis_kg,
                        'emis_tkm': transport.emis_tkm,
                        'type_transport': transport.type_transport,
                        'niveau_calcul': transport.niveau_calcul,
                        'type_vehicule': transport.type_vehicule,
                        'energie': transport.energie,
                        'conso_vehicule': transport.conso_vehicule,
                        'vehicule_dedie': transport.vehicule_dedie,
                        'client': transport.client,
                        'transporteur': transport.transporteur,
                        'description': transport.description,
                        'created_at': transport.created_at.strftime('%d/%m/%Y %H:%M') if transport.created_at else None,
                        'updated_at': transport.updated_at.strftime('%d/%m/%Y %H:%M') if transport.updated_at else None
                    })
                
                return jsonify({
                    'success': True,
                    'transports': transports_data
                })
                
            except Exception as e:
                logger.error(f"Erreur API transports GET: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        elif request.method == 'POST':
            """Créer un nouveau transport"""
            try:
                data = request.get_json()
                logger.info(f"📥 Données reçues pour création transport: {data}")
                
                # Validation des données
                if not data:
                    return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
                # Créer le transport
                nouveau_transport = Transport(
                    ref=data.get('ref', f'TR-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                    date=datetime.strptime(data['date'], '%Y-%m-%d') if data.get('date') else None,
                    lieu_collecte=data.get('lieu_collecte', ''),
                    lieu_livraison=data.get('lieu_livraison', ''),
                    poids_tonnes=float(data.get('poids_tonnes', 0)),
                    distance_km=float(data.get('distance_km', 0)),
                    type_transport=data.get('type_transport', 'direct'),
                    niveau_calcul=data.get('niveau_calcul', 'niveau1'),
                    type_vehicule=data.get('type_vehicule', ''),
                    energie=data.get('energie', ''),
                    conso_vehicule=float(data.get('conso_vehicule', 0)),
                    vehicule_dedie=bool(data.get('vehicule_dedie', False)),
                    client=data.get('client', ''),
                    transporteur=data.get('transporteur', ''),
                    description=data.get('description', '')
                )
                
                # Calculer les émissions
                resultat_emissions = calculer_emissions_transport(nouveau_transport)
                if resultat_emissions['success']:
                    nouveau_transport.emis_kg = resultat_emissions['emis_kg']
                    nouveau_transport.emis_tkm = resultat_emissions['emis_tkm']
                
                db.session.add(nouveau_transport)
                db.session.commit()
                
                logger.info(f"✅ Transport créé avec succès: {nouveau_transport.id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Transport créé avec succès',
                    'transport': {
                        'id': nouveau_transport.id,
                        'ref': nouveau_transport.ref,
                        'date': nouveau_transport.date.strftime('%d/%m/%Y') if nouveau_transport.date else None,
                        'lieu_collecte': nouveau_transport.lieu_collecte,
                        'lieu_livraison': nouveau_transport.lieu_livraison,
                        'poids_tonnes': nouveau_transport.poids_tonnes,
                        'distance_km': nouveau_transport.distance_km,
                        'emis_kg': nouveau_transport.emis_kg,
                        'emis_tkm': nouveau_transport.emis_tkm,
                        'type_transport': nouveau_transport.type_transport,
                        'niveau_calcul': nouveau_transport.niveau_calcul,
                        'type_vehicule': nouveau_transport.type_vehicule,
                        'energie': nouveau_transport.energie,
                        'conso_vehicule': nouveau_transport.conso_vehicule,
                        'client': nouveau_transport.client,
                        'transporteur': nouveau_transport.transporteur,
                        'description': nouveau_transport.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur création transport: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la création: {str(e)}'
                }), 500
        
        elif request.method == 'PUT':
            """Modifier un transport existant"""
            try:
                data = request.get_json()
                transport_id = data.get('id')
                
                if not transport_id:
                    return jsonify({'success': False, 'error': 'ID du transport requis'}), 400
                
                transport = Transport.query.get(transport_id)
                if not transport:
                    return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
                
                # Mettre à jour les champs
                if 'ref' in data:
                    transport.ref = data['ref']
                if 'date' in data:
                    transport.date = datetime.strptime(data['date'], '%Y-%m-%d') if data['date'] else None
                if 'lieu_collecte' in data:
                    transport.lieu_collecte = data['lieu_collecte']
                if 'lieu_livraison' in data:
                    transport.lieu_livraison = data['lieu_livraison']
                if 'poids_tonnes' in data:
                    transport.poids_tonnes = float(data['poids_tonnes'])
                if 'distance_km' in data:
                    transport.distance_km = float(data['distance_km'])
                if 'type_transport' in data:
                    transport.type_transport = data['type_transport']
                if 'niveau_calcul' in data:
                    transport.niveau_calcul = data['niveau_calcul']
                if 'type_vehicule' in data:
                    transport.type_vehicule = data['type_vehicule']
                if 'energie' in data:
                    transport.energie = data['energie']
                if 'conso_vehicule' in data:
                    transport.conso_vehicule = float(data['conso_vehicule'])
                if 'vehicule_dedie' in data:
                    transport.vehicule_dedie = bool(data['vehicule_dedie'])
                if 'client' in data:
                    transport.client = data['client']
                if 'transporteur' in data:
                    transport.transporteur = data['transporteur']
                if 'description' in data:
                    transport.description = data['description']
                
                # Recalculer les émissions
                resultat_emissions = calculer_emissions_transport(transport)
                if resultat_emissions['success']:
                    transport.emis_kg = resultat_emissions['emis_kg']
                    transport.emis_tkm = resultat_emissions['emis_tkm']
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Transport modifié avec succès',
                    'transport': {
                        'id': transport.id,
                        'ref': transport.ref,
                        'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                        'lieu_collecte': transport.lieu_collecte,
                        'lieu_livraison': transport.lieu_livraison,
                        'poids_tonnes': transport.poids_tonnes,
                        'distance_km': transport.distance_km,
                        'emis_kg': transport.emis_kg,
                        'emis_tkm': transport.emis_tkm,
                        'type_transport': transport.type_transport,
                        'niveau_calcul': transport.niveau_calcul,
                        'type_vehicule': transport.type_vehicule,
                        'energie': transport.energie,
                        'conso_vehicule': transport.conso_vehicule,
                        'vehicule_dedie': transport.vehicule_dedie,
                        'client': transport.client,
                        'transporteur': transport.transporteur,
                        'description': transport.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur modification transport: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la modification: {str(e)}'
                }), 500
        
        elif request.method == 'DELETE':
            """Supprimer un transport"""
            try:
                data = request.get_json()
                transport_id = data.get('id')
                
                if not transport_id:
                    return jsonify({'success': False, 'error': 'ID du transport requis'}), 400
                
                transport = Transport.query.get(transport_id)
                if not transport:
                    return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
                
                db.session.delete(transport)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Transport supprimé avec succès'
                })
                
            except Exception as e:
                logger.error(f"Erreur suppression transport: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la suppression: {str(e)}'
                }), 500
    
    except Exception as e:
        logger.error(f"Erreur API transports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/transports-v2', methods=['GET', 'POST'])
def api_transports_v2():
    """API v2 pour gérer les transports"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        if request.method == 'GET':
            """Récupérer tous les transports avec pagination"""
            try:
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 10, type=int)
                
                transports = Transport.query.paginate(
                    page=page, per_page=per_page, error_out=False
                )
                
                transports_data = []
                for transport in transports.items:
                    transports_data.append({
                        'id': transport.id,
                        'ref': transport.ref,
                        'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                        'lieu_collecte': transport.lieu_collecte,
                        'lieu_livraison': transport.lieu_livraison,
                        'poids_tonnes': transport.poids_tonnes,
                        'distance_km': transport.distance_km,
                        'emis_kg': transport.emis_kg,
                        'emis_tkm': transport.emis_tkm,
                        'type_transport': transport.type_transport,
                        'niveau_calcul': transport.niveau_calcul,
                        'type_vehicule': transport.type_vehicule,
                        'energie': transport.energie,
                        'conso_vehicule': transport.conso_vehicule,
                        'vehicule_dedie': transport.vehicule_dedie,
                        'client': transport.client,
                        'transporteur': transport.transporteur,
                        'description': transport.description,
                        'created_at': transport.created_at.strftime('%d/%m/%Y %H:%M') if transport.created_at else None,
                        'updated_at': transport.updated_at.strftime('%d/%m/%Y %H:%M') if transport.updated_at else None
                    })
                
                return jsonify({
                    'success': True,
                    'transports': transports_data,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': transports.total,
                        'pages': transports.pages,
                        'has_next': transports.has_next,
                        'has_prev': transports.has_prev
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur API transports v2 GET: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        elif request.method == 'POST':
            """Créer un nouveau transport avec validation avancée"""
            try:
                data = request.get_json()
                logger.info(f"📥 Données reçues pour création transport v2: {data}")
                
                # Validation des données
                if not data:
                    return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
                # Validation des champs requis
                required_fields = ['date', 'lieu_collecte', 'lieu_livraison', 'poids_tonnes']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'success': False, 'error': f'Champ requis manquant: {field}'}), 400
                
                # Créer le transport
                nouveau_transport = Transport(
                    ref=data.get('ref', f'TR-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                    date=datetime.strptime(data['date'], '%Y-%m-%d') if data.get('date') else None,
                    lieu_collecte=data['lieu_collecte'],
                    lieu_livraison=data['lieu_livraison'],
                    poids_tonnes=float(data['poids_tonnes']),
                    distance_km=float(data.get('distance_km', 0)),
                    type_transport=data.get('type_transport', 'direct'),
                    niveau_calcul=data.get('niveau_calcul', 'niveau1'),
                    type_vehicule=data.get('type_vehicule', ''),
                    energie=data.get('energie', ''),
                    conso_vehicule=float(data.get('conso_vehicule', 0)),
                    client=data.get('client', ''),
                    transporteur=data.get('transporteur', ''),
                    description=data.get('description', '')
                )
                
                # Calculer les émissions
                resultat_emissions = calculer_emissions_transport(nouveau_transport)
                if resultat_emissions['success']:
                    nouveau_transport.emis_kg = resultat_emissions['emis_kg']
                    nouveau_transport.emis_tkm = resultat_emissions['emis_tkm']
                
                db.session.add(nouveau_transport)
                db.session.commit()
                
                logger.info(f"✅ Transport v2 créé avec succès: {nouveau_transport.id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Transport créé avec succès',
                    'transport': {
                        'id': nouveau_transport.id,
                        'ref': nouveau_transport.ref,
                        'date': nouveau_transport.date.strftime('%d/%m/%Y') if nouveau_transport.date else None,
                        'lieu_collecte': nouveau_transport.lieu_collecte,
                        'lieu_livraison': nouveau_transport.lieu_livraison,
                        'poids_tonnes': nouveau_transport.poids_tonnes,
                        'distance_km': nouveau_transport.distance_km,
                        'emis_kg': nouveau_transport.emis_kg,
                        'emis_tkm': nouveau_transport.emis_tkm,
                        'type_transport': nouveau_transport.type_transport,
                        'niveau_calcul': nouveau_transport.niveau_calcul,
                        'type_vehicule': nouveau_transport.type_vehicule,
                        'energie': nouveau_transport.energie,
                        'conso_vehicule': nouveau_transport.conso_vehicule,
                        'client': nouveau_transport.client,
                        'transporteur': nouveau_transport.transporteur,
                        'description': nouveau_transport.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur création transport v2: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la création: {str(e)}'
                }), 500
    
    except Exception as e:
        logger.error(f"Erreur API transports v2: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/transports-v2/<int:transport_id>', methods=['PUT', 'DELETE'])
def api_transport_v2_detail(transport_id):
    """API v2 pour modifier et supprimer un transport spécifique"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        transport = Transport.query.get(transport_id)
        if not transport:
            return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
        
        if request.method == 'PUT':
            """Modifier un transport"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
                # Mettre à jour les champs
                if 'ref' in data:
                    transport.ref = data['ref']
                if 'date' in data:
                    transport.date = datetime.strptime(data['date'], '%Y-%m-%d') if data['date'] else None
                if 'lieu_collecte' in data:
                    transport.lieu_collecte = data['lieu_collecte']
                if 'lieu_livraison' in data:
                    transport.lieu_livraison = data['lieu_livraison']
                if 'poids_tonnes' in data:
                    transport.poids_tonnes = float(data['poids_tonnes'])
                if 'distance_km' in data:
                    transport.distance_km = float(data['distance_km'])
                if 'type_transport' in data:
                    transport.type_transport = data['type_transport']
                if 'niveau_calcul' in data:
                    transport.niveau_calcul = data['niveau_calcul']
                if 'type_vehicule' in data:
                    transport.type_vehicule = data['type_vehicule']
                if 'energie' in data:
                    transport.energie = data['energie']
                if 'conso_vehicule' in data:
                    transport.conso_vehicule = float(data['conso_vehicule'])
                if 'vehicule_dedie' in data:
                    transport.vehicule_dedie = bool(data['vehicule_dedie'])
                if 'client' in data:
                    transport.client = data['client']
                if 'transporteur' in data:
                    transport.transporteur = data['transporteur']
                if 'description' in data:
                    transport.description = data['description']
                
                # Recalculer les émissions
                resultat_emissions = calculer_emissions_transport(transport)
                if resultat_emissions['success']:
                    transport.emis_kg = resultat_emissions['emis_kg']
                    transport.emis_tkm = resultat_emissions['emis_tkm']
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Transport modifié avec succès',
                    'transport': {
                        'id': transport.id,
                        'ref': transport.ref,
                        'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                        'lieu_collecte': transport.lieu_collecte,
                        'lieu_livraison': transport.lieu_livraison,
                        'poids_tonnes': transport.poids_tonnes,
                        'distance_km': transport.distance_km,
                        'emis_kg': transport.emis_kg,
                        'emis_tkm': transport.emis_tkm,
                        'type_transport': transport.type_transport,
                        'niveau_calcul': transport.niveau_calcul,
                        'type_vehicule': transport.type_vehicule,
                        'energie': transport.energie,
                        'conso_vehicule': transport.conso_vehicule,
                        'vehicule_dedie': transport.vehicule_dedie,
                        'client': transport.client,
                        'transporteur': transport.transporteur,
                        'description': transport.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur modification transport v2: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la modification: {str(e)}'
                }), 500
        
        elif request.method == 'DELETE':
            """Supprimer un transport"""
            try:
                db.session.delete(transport)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Transport supprimé avec succès'
                })
                
            except Exception as e:
                logger.error(f"Erreur suppression transport v2: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la suppression: {str(e)}'
                }), 500
    
    except Exception as e:
        logger.error(f"Erreur API transport v2 detail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/transports/calculate-distance', methods=['POST'])
def calculate_distance():
    """API pour calculer la distance entre deux lieux"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
        
        lieu_collecte = data.get('lieu_collecte')
        lieu_livraison = data.get('lieu_livraison')
        
        if not lieu_collecte or not lieu_livraison:
            return jsonify({'success': False, 'error': 'Lieu de collecte et lieu de livraison requis'}), 400
        
        # Pour l'instant, retourner une distance par défaut
        # TODO: Implémenter le calcul de distance réel avec une API externe
        distance_km = 50.0  # Distance par défaut
        
        return jsonify({
            'success': True,
            'distance_km': distance_km,
            'lieu_collecte': lieu_collecte,
            'lieu_livraison': lieu_livraison,
            'message': 'Distance calculée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur calcul distance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_transports_bp.route('/lieux/autocomplete', methods=['GET'])
def lieux_autocomplete():
    """API pour l'autocomplétion des lieux (codes postaux et villes)"""
    try:
        query = request.args.get('q', '')
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'lieux': []
            })
        
        # Ici, vous pourriez intégrer une API de géocodage
        # Pour l'instant, on retourne des suggestions simulées
        
        suggestions = [
            f"{query} - Paris (75001)",
            f"{query} - Lyon (69001)",
            f"{query} - Marseille (13001)",
            f"{query} - Toulouse (31000)",
            f"{query} - Nice (06000)"
        ]
        
        return jsonify({
            'success': True,
            'lieux': suggestions
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'autocomplétion: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'autocomplétion: {str(e)}'
        })

@api_transports_bp.route('/transports/<int:transport_id>', methods=['PUT', 'DELETE'])
def api_transport_by_id(transport_id):
    """API pour modifier ou supprimer un transport spécifique"""
    try:
        # Import des modèles depuis app.py
        from app import Transport, db
        
        if request.method == 'PUT':
            """Modifier un transport existant"""
            try:
                data = request.get_json()
                logger.info(f"📥 Données reçues pour modification transport {transport_id}: {data}")
                
                if not data:
                    return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
                transport = Transport.query.get(transport_id)
                if not transport:
                    return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
                
                # Mettre à jour les champs
                if 'ref' in data:
                    transport.ref = data['ref']
                if 'date' in data:
                    transport.date = datetime.strptime(data['date'], '%Y-%m-%d') if data['date'] else None
                if 'lieu_collecte' in data:
                    transport.lieu_collecte = data['lieu_collecte']
                if 'lieu_livraison' in data:
                    transport.lieu_livraison = data['lieu_livraison']
                if 'poids_tonnes' in data:
                    transport.poids_tonnes = float(data['poids_tonnes'])
                if 'distance_km' in data:
                    transport.distance_km = float(data['distance_km'])
                if 'type_transport' in data:
                    transport.type_transport = data['type_transport']
                if 'niveau_calcul' in data:
                    transport.niveau_calcul = data['niveau_calcul']
                if 'type_vehicule' in data:
                    transport.type_vehicule = data['type_vehicule']
                if 'energie' in data:
                    transport.energie = data['energie']
                if 'conso_vehicule' in data:
                    transport.conso_vehicule = float(data['conso_vehicule']) if data['conso_vehicule'] else None
                if 'vehicule_dedie' in data:
                    transport.vehicule_dedie = bool(data['vehicule_dedie'])
                if 'client' in data:
                    transport.client = data['client']
                if 'transporteur' in data:
                    transport.transporteur = data['transporteur']
                if 'description' in data:
                    transport.description = data['description']
                if 'emis_kg' in data:
                    transport.emis_kg = float(data['emis_kg']) if data['emis_kg'] else None
                if 'emis_tkm' in data:
                    transport.emis_tkm = float(data['emis_tkm']) if data['emis_tkm'] else None
                
                # Mettre à jour la date de modification
                transport.updated_at = datetime.now()
                
                db.session.commit()
                
                logger.info(f"✅ Transport {transport_id} modifié avec succès")
                
                return jsonify({
                    'success': True,
                    'message': 'Transport modifié avec succès',
                    'transport': {
                        'id': transport.id,
                        'ref': transport.ref,
                        'date': transport.date.strftime('%d/%m/%Y') if transport.date else None,
                        'date_iso': transport.date.strftime('%Y-%m-%d') if transport.date else None,
                        'lieu_collecte': transport.lieu_collecte,
                        'lieu_livraison': transport.lieu_livraison,
                        'poids_tonnes': transport.poids_tonnes,
                        'distance_km': transport.distance_km,
                        'emis_kg': transport.emis_kg,
                        'emis_tkm': transport.emis_tkm,
                        'type_transport': transport.type_transport,
                        'niveau_calcul': transport.niveau_calcul,
                        'type_vehicule': transport.type_vehicule,
                        'energie': transport.energie,
                        'conso_vehicule': transport.conso_vehicule,
                        'vehicule_dedie': transport.vehicule_dedie,
                        'client': transport.client,
                        'transporteur': transport.transporteur,
                        'description': transport.description
                    }
                })
                
            except Exception as e:
                logger.error(f"Erreur modification transport {transport_id}: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la modification: {str(e)}'
                }), 500
        
        elif request.method == 'DELETE':
            """Supprimer un transport"""
            try:
                transport = Transport.query.get(transport_id)
                if not transport:
                    return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
                
                ref_transport = transport.ref
                db.session.delete(transport)
                db.session.commit()
                
                logger.info(f"✅ Transport {transport_id} ({ref_transport}) supprimé avec succès")
                
                return jsonify({
                    'success': True,
                    'message': f'Transport "{ref_transport}" supprimé avec succès'
                })
                
            except Exception as e:
                logger.error(f"Erreur suppression transport {transport_id}: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la suppression: {str(e)}'
                }), 500
        
    except Exception as e:
        logger.error(f"Erreur API transport {transport_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



