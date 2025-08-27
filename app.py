from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text
import os
import logging
from datetime import datetime
from config import get_config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('emissions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialisation de Flask
app = Flask(__name__)

# Configuration
config = get_config()
app.config.from_object(config)

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Configuration des extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
CORS(app)

# Configuration du login manager
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données"""
    # Pour l'instant, retourner None (pas d'authentification)
    return None

@login_manager.request_loader
def load_user_from_request(request):
    """Charge un utilisateur depuis la requête"""
    # Pour l'instant, retourner None (pas d'authentification)
    return None

# Définition des modèles directement dans app.py
class Transport(db.Model):
    """Modèle pour les transports"""
    __tablename__ = 'transports'
    
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(50), unique=True, nullable=False)
    type_transport = db.Column(db.String(50))
    niveau_calcul = db.Column(db.String(50))
    type_vehicule = db.Column(db.String(50))
    energie = db.Column(db.String(50))
    conso_vehicule = db.Column(db.Float)
    poids_tonnes = db.Column(db.Float)
    distance_km = db.Column(db.Float)
    emis_kg = db.Column(db.Float, default=0.0)
    emis_tkm = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Vehicule(db.Model):
    """Modèle pour les véhicules"""
    __tablename__ = 'vehicules'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    consommation = db.Column(db.Float)  # L/100km
    emissions = db.Column(db.Float)     # g CO2e/km
    charge_utile = db.Column(db.Float)  # tonnes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Energie(db.Model):
    """Modèle pour les énergies"""
    __tablename__ = 'energies'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    identifiant = db.Column(db.String(50), unique=True)
    unite = db.Column(db.String(20), default='L')  # Unité de mesure (L, kg, kWh)
    facteur = db.Column(db.Float)       # kg CO2e/L (total)
    phase_amont = db.Column(db.Float, default=0.0)      # kg CO2e/L (phase amont)
    phase_fonctionnement = db.Column(db.Float, default=0.0)  # kg CO2e/L (phase fonctionnement)
    description = db.Column(db.Text)
    donnees_supplementaires = db.Column(db.JSON, default={})  # Données supplémentaires en JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialiser la base de données APRÈS la définition des modèles
with app.app_context():
    try:
        db.create_all()
        logger.info("✅ Base de données initialisée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base: {str(e)}")
        # Ne pas lever l'erreur pour permettre le démarrage

# Les modèles sont maintenant définis directement dans app.py
# Plus besoin d'importer transport_api

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    try:
        # Récupérer les statistiques
        total_transports = Transport.query.count()
        total_clients = 0
        if hasattr(Transport, 'client_id'):
            try:
                result = db.session.query(db.func.count(db.distinct(Transport.client_id))).scalar()
                total_clients = result if result is not None else 0
            except Exception:
                total_clients = 0
        
        logger.info(f"Affichage du dashboard - {total_transports} transports")
        
        return render_template('dashboard.html', 
                            total_transports=total_transports,
                            total_clients=total_clients)
                        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du dashboard: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/transports')
def transports():
    """Liste des transports"""
    try:
        # Récupérer tous les transports
        transports = Transport.query.all()
        
        # Récupérer les véhicules et énergies pour l'affichage
        vehicules = {v.id: v for v in Vehicule.query.all()}
        energies = {e.id: e for e in Energie.query.all()}
        
        logger.info(f"Affichage de {len(transports)} transports")
        
        return render_template('liste_transports.html', 
                            transports=transports,
                            vehicules=vehicules,
                            energies=energies,
                            clients={})
                        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transports: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/vehicules')
def api_vehicules():
    """API pour récupérer les véhicules"""
    try:
        vehicules = Vehicule.query.all()
        vehicules_data = []
        
        for v in vehicules:
            vehicules_data.append({
                'id': v.id,
                'nom': v.nom,
                'type': v.type,
                'consommation': v.consommation,
                'emissions': v.emissions,
                'charge_utile': v.charge_utile
            })
        
        return jsonify({
            'success': True,
            'vehicules': vehicules_data
        })
    
    except Exception as e:
        logger.error(f"Erreur API véhicules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/energies')
def api_energies():
    """API pour récupérer les énergies"""
    try:
        energies = Energie.query.all()
        energies_data = []
        
        for e in energies:
            energies_data.append({
                'id': e.id,
                'nom': e.nom,
                'identifiant': e.identifiant,
                'facteur': e.facteur,
                'description': e.description
            })
        
        return jsonify({
            'success': True,
            'energies': energies_data
        })
    
    except Exception as e:
        logger.error(f"Erreur API énergies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/administration')
def administration():
    """Page d'administration"""
    try:
        return render_template('administration.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'administration: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/parametrage_clients')
def parametrage_clients():
    """Page de paramétrage des clients"""
    try:
        return render_template('clients.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/parametrage_energies')
def parametrage_energies():
    """Page de paramétrage des énergies"""
    try:
        # Récupérer toutes les énergies pour l'affichage
        energies = Energie.query.all()
        return render_template('parametrage_energies.html', energies=energies)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des énergies: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/energies', methods=['POST'])
def creer_energie():
    """Créer une nouvelle énergie"""
    try:
        data = request.get_json()
        
        # Validation des données
        if not data.get('nom') or not data.get('identifiant'):
            return jsonify({'success': False, 'error': 'Nom et identifiant requis'}), 400
        
        # Vérifier si l'identifiant existe déjà
        if Energie.query.filter_by(identifiant=data['identifiant']).first():
            return jsonify({'success': False, 'error': 'Cet identifiant existe déjà'}), 400
        
        # Créer la nouvelle énergie
        nouvelle_energie = Energie(
            nom=data['nom'],
            identifiant=data['identifiant'],
            unite=data.get('unite', 'L'),
            facteur=float(data.get('facteur', 0)) if data.get('facteur') else None,
            description=data.get('description', '')
        )
        
        db.session.add(nouvelle_energie)
        db.session.commit()
        
        logger.info(f"✅ Nouvelle énergie créée: {nouvelle_energie.nom}")
        return jsonify({'success': True, 'message': 'Énergie créée avec succès'})
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de l'énergie: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>', methods=['PUT'])
def modifier_energie(energie_id):
    """Modifier une énergie existante"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        data = request.get_json()
        
        # Validation des données
        if not data.get('nom') or data.get('facteur') is None:
            return jsonify({'success': False, 'error': 'Nom et facteur requis'}), 400
        
        # Vérifier si l'identifiant existe déjà (sauf pour cette énergie)
        if data.get('identifiant') and data['identifiant'] != energie.identifiant:
            if Energie.query.filter_by(identifiant=data['identifiant']).first():
                return jsonify({'success': False, 'error': 'Cet identifiant existe déjà'}), 400
        
        # Mettre à jour l'énergie
        energie.nom = data['nom']
        if data.get('identifiant'):
            energie.identifiant = data['identifiant']
        if data.get('unite'):
            energie.unite = data['unite']
        energie.facteur = float(data['facteur'])
        energie.description = data.get('description', '')
        
        db.session.commit()
        
        logger.info(f"✅ Énergie modifiée: {energie.nom}")
        return jsonify({'success': True, 'message': 'Énergie modifiée avec succès'})
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la modification de l'énergie: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>', methods=['DELETE'])
def supprimer_energie(energie_id):
    """Supprimer une énergie"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        
        # Vérifier si l'énergie est utilisée dans des transports
        transports_utilisant_energie = Transport.query.filter_by(energie=str(energie_id)).count()
        if transports_utilisant_energie > 0:
            return jsonify({
                'success': False, 
                'error': f'Cette énergie est utilisée par {transports_utilisant_energie} transport(s). Impossible de la supprimer.'
            }), 400
        
        nom_energie = energie.nom
        db.session.delete(energie)
        db.session.commit()
        
        logger.info(f"✅ Énergie supprimée: {nom_energie}")
        return jsonify({'success': True, 'message': 'Énergie supprimée avec succès'})
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression de l'énergie: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>/facteurs', methods=['PUT'])
def modifier_facteurs_energie(energie_id):
    """Modifier les facteurs d'émission d'une énergie"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        data = request.get_json()
        
        # Validation des données
        if not data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        # Mettre à jour les facteurs
        if 'phase_amont' in data:
            energie.phase_amont = float(data['phase_amont'])
        if 'phase_fonctionnement' in data:
            energie.phase_fonctionnement = float(data['phase_fonctionnement'])
        if 'total' in data:
            energie.facteur = float(data['total'])
        
        # Mettre à jour les données supplémentaires
        if 'donnees_supplementaires' in data:
            energie.donnees_supplementaires = data['donnees_supplementaires']
        
        db.session.commit()
        
        logger.info(f"✅ Facteurs mis à jour pour l'énergie {energie.nom}")
        return jsonify({
            'success': True, 
            'message': 'Facteurs mis à jour avec succès',
            'energie': {
                'id': energie.id,
                'nom': energie.nom,
                'phase_amont': getattr(energie, 'phase_amont', 0),
                'phase_fonctionnement': getattr(energie, 'phase_fonctionnement', 0),
                'total': energie.facteur,
                'donnees_supplementaires': getattr(energie, 'donnees_supplementaires', {})
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour des facteurs: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>/donnees', methods=['POST'])
def ajouter_donnee_energie(energie_id):
    """Ajouter une nouvelle donnée à une énergie"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        data = request.get_json()
        
        # Validation des données
        if not data.get('nom') or data.get('valeur') is None:
            return jsonify({'success': False, 'error': 'Nom et valeur requis'}), 400
        
        # Récupérer ou créer les données supplémentaires
        donnees_supp = getattr(energie, 'donnees_supplementaires', {}) or {}
        
        # Ajouter la nouvelle donnée
        donnees_supp[data['nom']] = {
            'valeur': float(data['valeur']),
            'unite': data.get('unite', 'kg éq. CO₂'),
            'description': data.get('description', ''),
            'date_ajout': datetime.utcnow().isoformat()
        }
        
        # Mettre à jour l'énergie
        energie.donnees_supplementaires = donnees_supp
        db.session.commit()
        
        logger.info(f"✅ Donnée ajoutée à l'énergie {energie.nom}: {data['nom']}")
        return jsonify({
            'success': True,
            'message': 'Donnée ajoutée avec succès',
            'donnee': donnees_supp[data['nom']]
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de la donnée: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>/donnees/<nom_donnee>', methods=['DELETE'])
def supprimer_donnee_energie(energie_id, nom_donnee):
    """Supprimer une donnée d'une énergie"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        
        # Récupérer les données supplémentaires
        donnees_supp = getattr(energie, 'donnees_supplementaires', {}) or {}
        
        if nom_donnee not in donnees_supp:
            return jsonify({'success': False, 'error': 'Donnée non trouvée'}), 404
        
        # Supprimer la donnée
        del donnees_supp[nom_donnee]
        energie.donnees_supplementaires = donnees_supp
        db.session.commit()
        
        logger.info(f"✅ Donnée supprimée de l'énergie {energie.nom}: {nom_donnee}")
        return jsonify({'success': True, 'message': 'Donnée supprimée avec succès'})
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression de la donnée: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/parametrage_vehicules')
def parametrage_vehicules():
    """Page de paramétrage des véhicules"""
    try:
        return render_template('parametrage_vehicules.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des véhicules: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/parametrage_impact')
def parametrage_impact():
    """Page de paramétrage des impacts environnementaux"""
    try:
        return render_template('parametrage_impact.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des impacts: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/import_csv')
def import_csv():
    """Page d'import CSV"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'import CSV: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/nouveau_transport')
def nouveau_transport():
    """Page de sélection du mode de création de transport"""
    try:
        return render_template('nouveau_transport.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du choix de création: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/transport')
@app.route('/transport/<int:transport_id>')
def transport(transport_id=None):
    """Page de création/modification d'un transport"""
    try:
        transport = None
        if transport_id:
            transport = Transport.query.get_or_404(transport_id)
        
        # Récupérer les véhicules et énergies pour le formulaire
        vehicules = Vehicule.query.all()
        energies = Energie.query.all()
        
        return render_template('transport.html', 
                            transport=transport,
                            vehicules=vehicules,
                            energies=energies)
                            
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du transport: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/import_transports_csv', methods=['POST'])
def import_transports_csv():
    """Import de transports depuis un fichier CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Le fichier doit être au format CSV'}), 400
        
        # Lire le fichier CSV
        import csv
        from io import StringIO
        
        # Décoder le contenu du fichier
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        transports_crees = 0
        erreurs = 0
        resultats = []
        
        for row in csv_reader:
            try:
                # Validation des données obligatoires
                if not row.get('ref') or not row.get('type_transport') or not row.get('niveau_calcul'):
                    erreurs += 1
                    resultats.append({'ref': row.get('ref', 'N/A'), 'error': 'Données obligatoires manquantes'})
                    continue
                
                # Vérifier si la référence existe déjà
                if Transport.query.filter_by(ref=row['ref']).first():
                    erreurs += 1
                    resultats.append({'ref': row['ref'], 'error': 'Référence déjà existante'})
                    continue
                
                # Créer le transport
                nouveau_transport = Transport(
                    ref=row['ref'],
                    type_transport=row['type_transport'],
                    niveau_calcul=row['niveau_calcul'],
                    type_vehicule=row.get('type_vehicule'),
                    energie=row.get('energie'),
                    conso_vehicule=float(row['conso_vehicule']) if row.get('conso_vehicule') else None,
                    poids_tonnes=float(row['poids_tonnes']) if row.get('poids_tonnes') else None,
                    distance_km=float(row['distance_km']) if row.get('distance_km') else None
                )
                
                db.session.add(nouveau_transport)
                transports_crees += 1
                resultats.append({'ref': row['ref'], 'success': True})
                
            except Exception as e:
                erreurs += 1
                resultats.append({'ref': row.get('ref', 'N/A'), 'error': str(e)})
        
        # Sauvegarder tous les transports créés
        try:
            db.session.commit()
            logger.info(f"✅ Import CSV terminé: {transports_crees} créés, {erreurs} erreurs")
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            return jsonify({'success': False, 'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Import terminé: {transports_crees} créés, {erreurs} erreurs',
            'transports_crees': transports_crees,
            'erreurs': erreurs,
            'resultats': resultats
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'import CSV: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculer_emissions_transport(transport):
    """Calcule les émissions CO₂e d'un transport selon son niveau de calcul"""
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

@app.route('/api/transports/recalculer-emissions', methods=['POST'])
def recalculer_emissions():
    """Endpoint pour recalculer les émissions de tous les transports"""
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

@app.route('/logout')
def logout():
    """Déconnexion"""
    return render_template('login.html')

@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    try:
        # Vérifier la base de données
        db.session.execute(text('SELECT 1'))
        db_status = 'OK'
    except Exception as e:
        db_status = f'ERROR: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))
    })

@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404"""
    return render_template('error.html', error='Page non trouvée'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500"""
    db.session.rollback()
    logger.error(f"Erreur interne: {str(error)}")
    return render_template('error.html', error='Erreur interne du serveur'), 500

def init_database():
    """Initialise la base de données et crée les tables"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("✅ Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base: {str(e)}")
        raise

if __name__ == '__main__':
    # Démarrage de l'application
    logger.info("🚀 Démarrage de l'application Myxploit...")
    
    try:
        # Initialiser la base de données
        init_database()
        
        # Démarrer le serveur
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {str(e)}")
        raise
# Test - Fichier corrigé localement
