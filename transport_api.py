from flask import Blueprint, request, jsonify
from models import db, Transport, Vehicule, Energie
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création du Blueprint pour les API de transports
transport_api = Blueprint('transport_api', __name__)

def calculer_emissions_transport(transport):
    """
    Calcule les émissions CO₂e d'un transport selon son niveau de calcul
    """
    try:
        logger.info(f"Calcul des émissions pour le transport {transport.ref}")
        
        # Vérifier les données minimales
        if not transport.poids_tonnes or not transport.distance_km:
            return {
                'success': False,
                'error': 'Poids ou distance manquant',
                'emis_kg': 0,
                'emis_tkm': 0
            }
        
        emis_kg = 0
        emis_tkm = 0
        
        # Niveau 1 : Calcul basé sur le véhicule et l'énergie
        if transport.niveau_calcul and 'niveau_1' in transport.niveau_calcul:
            logger.info(f"Transport {transport.ref}: Calcul niveau 1")
            
            if not transport.type_vehicule:
                return {
                    'success': False,
                    'error': 'Type de véhicule manquant pour niveau 1',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            # Récupérer le véhicule
            vehicule = Vehicule.query.get(transport.type_vehicule)
            if not vehicule:
                return {
                    'success': False,
                    'error': f'Véhicule {transport.type_vehicule} non trouvé',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            if not vehicule.consommation:
                return {
                    'success': False,
                    'error': 'Consommation du véhicule manquante',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            # Calcul avec consommation du véhicule
            consommation_totale = (transport.distance_km / 100) * vehicule.consommation
            
            if transport.energie:
                # Récupérer l'énergie
                energie = Energie.query.get(transport.energie)
                if energie and energie.facteur:
                    # Calcul avec facteur d'émission de l'énergie
                    emis_kg = consommation_totale * energie.facteur
                    logger.info(f"Transport {transport.ref}: Calcul avec facteur énergie {energie.facteur}")
                else:
                    # Fallback sur les émissions du véhicule
                    if vehicule.emissions:
                        emis_kg = (consommation_totale * vehicule.emissions) / 1000
                        logger.info(f"Transport {transport.ref}: Fallback sur émissions véhicule")
                    else:
                        return {
                            'success': False,
                            'error': 'Aucun facteur d\'émission disponible',
                            'emis_kg': 0,
                            'emis_tkm': 0
                        }
            else:
                # Fallback sur les émissions du véhicule
                if vehicule.emissions:
                    emis_kg = (consommation_totale * vehicule.emissions) / 1000
                    logger.info(f"Transport {transport.ref}: Fallback sur émissions véhicule (pas d'énergie)")
                else:
                    return {
                        'success': False,
                        'error': 'Aucun facteur d\'émission disponible',
                        'emis_kg': 0,
                        'emis_tkm': 0
                    }
            
            # kg CO₂e/t.km imposé par le véhicule
            if vehicule.emissions:
                emis_tkm = vehicule.emissions / 1000
            else:
                emis_tkm = 0
                
        else:
            # Niveaux 2, 3, 4 : Calcul basé sur la consommation et l'énergie
            logger.info(f"Transport {transport.ref}: Calcul niveaux 2-4")
            
            if not transport.conso_vehicule:
                return {
                    'success': False,
                    'error': 'Consommation véhicule manquante pour niveaux 2-4',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            if not transport.energie:
                return {
                    'success': False,
                    'error': 'Énergie manquante pour niveaux 2-4',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            # Récupérer l'énergie
            energie = Energie.query.get(transport.energie)
            if not energie or not energie.facteur:
                return {
                    'success': False,
                    'error': 'Facteur d\'émission de l\'énergie manquant',
                    'emis_kg': 0,
                    'emis_tkm': 0
                }
            
            # Calcul avec consommation et facteur d'émission
            consommation_totale = (transport.distance_km / 100) * transport.conso_vehicule
            emis_kg = consommation_totale * energie.facteur
            
            # kg CO₂e/t.km calculé
            masse_distance = transport.poids_tonnes * transport.distance_km
            if masse_distance > 0:
                emis_tkm = emis_kg / masse_distance
            else:
                emis_tkm = 0
        
        # Arrondir les résultats
        emis_kg = round(emis_kg, 2)
        emis_tkm = round(emis_tkm, 3)
        
        logger.info(f"Transport {transport.ref}: Émissions calculées - {emis_kg} kg, {emis_tkm} kg/t.km")
        
        return {
            'success': True,
            'emis_kg': emis_kg,
            'emis_tkm': emis_tkm
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des émissions pour le transport {transport.ref}: {str(e)}")
        return {
            'success': False,
            'error': f'Erreur de calcul: {str(e)}',
            'emis_kg': 0,
            'emis_tkm': 0
        }

@transport_api.route('/api/transports/recalculer-emissions', methods=['POST'])
def recalculer_emissions():
    """
    Endpoint pour recalculer les émissions de tous les transports
    """
    try:
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
            
            for transport in transports:
                try:
                    # Calculer les émissions
                    resultat = calculer_emissions_transport(transport)
                    
                    if resultat['success']:
                        # Mettre à jour le transport en base
                        transport.emis_kg = resultat['emis_kg']
                        transport.emis_tkm = resultat['emis_tkm']
                        succes += 1
                        
                        resultats.append({
                            'ref': transport.ref,
                            'emis_kg': resultat['emis_kg'],
                            'emis_tkm': resultat['emis_tkm'],
                            'success': True
                        })
                        
                        logger.info(f"Transport {transport.ref}: Émissions mises à jour")
                    else:
                        erreurs += 1
                        logger.warning(f"Transport {transport.ref}: {resultat['error']}")
                        
                        resultats.append({
                            'ref': transport.ref,
                            'error': resultat['error'],
                            'success': False
                        })
                        
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

@transport_api.route('/api/transports/liste-mise-a-jour')
def liste_mise_a_jour():
    """
    Endpoint pour récupérer la liste des transports avec les émissions mises à jour
    """
    try:
        # Récupérer tous les transports avec leurs émissions
        transports = Transport.query.all()
        
        transports_data = []
        for transport in transports:
            transports_data.append({
                'ref': transport.ref,
                'emis_kg': transport.emis_kg or 0,
                'emis_tkm': transport.emis_tkm or 0,
                'poids': transport.poids_tonnes,
                'distance': transport.distance_km,
                'energie': transport.energie,
                'niveau_calcul': transport.niveau_calcul
            })
        
        logger.info(f"Liste mise à jour envoyée: {len(transports_data)} transports")
        
        return jsonify({
            'success': True,
            'transports': transports_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@transport_api.route('/api/transports/<int:transport_id>/recalculer-emissions', methods=['POST'])
def recalculer_emissions_transport(transport_id):
    """
    Endpoint pour recalculer les émissions d'un transport spécifique
    """
    try:
        transport = Transport.query.get_or_404(transport_id)
        logger.info(f"Recalcul des émissions pour le transport {transport.ref}")
        
        # Calculer les émissions
        resultat = calculer_emissions_transport(transport)
        
        if resultat['success']:
            # Mettre à jour le transport en base
            transport.emis_kg = resultat['emis_kg']
            transport.emis_tkm = resultat['emis_tkm']
            
            try:
                db.session.commit()
                logger.info(f"Transport {transport.ref}: Émissions mises à jour en base")
                
                return jsonify({
                    'success': True,
                    'ref': transport.ref,
                    'emis_kg': resultat['emis_kg'],
                    'emis_tkm': resultat['emis_tkm'],
                    'message': 'Émissions recalculées avec succès'
                })
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la sauvegarde: {str(e)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': resultat['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Erreur lors du recalcul du transport {transport_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500
