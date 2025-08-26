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
    facteur = db.Column(db.Float)       # kg CO2e/L
    description = db.Column(db.Text)
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
        if not data.get('nom') or not data.get('identifiant') or data.get('facteur') is None:
            return jsonify({'success': False, 'error': 'Nom, identifiant et facteur requis'}), 400
        
        # Vérifier si l'identifiant existe déjà
        if Energie.query.filter_by(identifiant=data['identifiant']).first():
            return jsonify({'success': False, 'error': 'Cet identifiant existe déjà'}), 400
        
        # Créer la nouvelle énergie
        nouvelle_energie = Energie(
            nom=data['nom'],
            identifiant=data['identifiant'],
            facteur=float(data['facteur']),
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
