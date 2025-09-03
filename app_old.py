from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text
import os
import logging
from datetime import datetime, timedelta
from config import get_config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️ Module python-dotenv non installé - variables d'environnement système utilisées")

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

# Forcer l'utilisation de la DATABASE_URL de Render en production
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Correction pour Render (postgres:// -> postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    config.SQLALCHEMY_DATABASE_URI = database_url
    logger.info(f"🔧 Configuration forcée: Base PostgreSQL détectée - {database_url[:50]}...")
else:
    logger.warning("⚠️ DATABASE_URL non trouvée, utilisation de la configuration par défaut")

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

# Création des modèles
from models import create_models
models = create_models(db)

# Import des modèles pour utilisation dans les routes
User = models['User']
Invitation = models['Invitation']
Transport = models['Transport']
Vehicule = models['Vehicule']
Energie = models['Energie']
Client = models['Client']
Transporteur = models['Transporteur']

# Enregistrement des blueprints
from blueprints import (
    auth_bp, main_bp, admin_bp, transports_bp, 
    clients_bp, api_bp, api_vehicules_bp, api_energies_bp, api_transports_bp, api_clients_bp, api_invitations_bp, parametrage_bp, invitations_bp
)

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(transports_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(api_bp)
app.register_blueprint(api_vehicules_bp)
app.register_blueprint(api_energies_bp)
app.register_blueprint(api_transports_bp)
app.register_blueprint(api_clients_bp)
app.register_blueprint(api_invitations_bp)
app.register_blueprint(parametrage_bp)
app.register_blueprint(invitations_bp)

# Configuration du login manager
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données"""
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'utilisateur {user_id}: {str(e)}")
        return None

# ============================================================================
# ROUTES RESTANTES À MIGRER (29 routes)
# ============================================================================

# Routes d'import
@app.route('/import_csv')
def import_csv():
    """Page d'import CSV"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'import CSV: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Routes d'authentification
@app.route('/logout')
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('auth.login'))

# Routes de santé et debug
@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    try:
        # Test de connexion à la base de données
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

# Routes de debug
@app.route('/debug/database')
def debug_database():
    """Route de diagnostic pour la structure de la base de données"""
    try:
        # Vérifier la structure des tables
        tables_info = {}
        
        # Vérifier les tables principales
        tables = ['users', 'clients', 'transports', 'vehicules', 'energies', 'invitations', 'transporteurs']
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                tables_info[table] = {
                    'exists': True,
                    'count': count
                }
            except Exception as e:
                tables_info[table] = {
                    'exists': False,
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'tables': tables_info,
            'database_url': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')[:50] + '...'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic de la base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/debug')
def debug_page():
    """Page de debug pour diagnostiquer la base de données"""
    return render_template('debug.html')

@app.route('/debug/invitations')
def debug_invitations():
    """Debug spécifique pour les invitations"""
    try:
        invitations = Invitation.query.all()
        invitations_data = []
        
        for inv in invitations:
            invitations_data.append({
                'id': inv.id,
                'email': inv.email,
                'statut': inv.statut,
                'created_at': inv.created_at.isoformat() if inv.created_at else None,
                'token': inv.token[:20] + '...' if inv.token else None
            })
        
        return jsonify({
            'success': True,
            'invitations': invitations_data,
            'total': len(invitations_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du debug des invitations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-invitations')
def test_invitations_page():
    """Page de test pour diagnostiquer les problèmes d'invitations"""
    return render_template('test_invitations.html')

@app.route('/debug/vehicules')
def debug_vehicules_page():
    """Page de debug spécifique pour les véhicules"""
    return render_template('debug_vehicules.html')

# Routes de transporteurs (à migrer vers un blueprint dédié)
@app.route('/transporteurs')
def transporteurs():
    """Page de gestion des transporteurs (côté client)"""
    try:
        return render_template('transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transporteurs: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Routes API transporteurs (à migrer vers un blueprint dédié)
@app.route('/api/transporteurs', methods=['GET', 'POST'])
def api_transporteurs():
    """API pour gérer les transporteurs"""
    if request.method == 'GET':
        try:
            transporteurs = Transporteur.query.all()
            transporteurs_data = []
            
            for transporteur in transporteurs:
                transporteurs_data.append({
                    'id': transporteur.id,
                    'nom': transporteur.nom,
                    'email': transporteur.email,
                    'telephone': transporteur.telephone,
                    'adresse': transporteur.adresse,
                    'siret': transporteur.siret,
                    'statut': transporteur.statut,
                    'created_at': transporteur.created_at.strftime('%Y-%m-%d %H:%M:%S') if transporteur.created_at else None
                })
            
            return jsonify({
                'success': True,
                'transporteurs': transporteurs_data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des transporteurs: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation des données
            if not data.get('nom') or not data.get('email'):
                return jsonify({'success': False, 'error': 'Nom et email sont obligatoires'}), 400
            
            # Vérifier si l'email existe déjà
            if Transporteur.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'error': 'Un transporteur avec cet email existe déjà'}), 400
            
            # Créer le nouveau transporteur
            nouveau_transporteur = Transporteur(
                nom=data.get('nom'),
                email=data.get('email'),
                telephone=data.get('telephone'),
                adresse=data.get('adresse'),
                siret=data.get('siret'),
                statut='actif'
            )
            
            db.session.add(nouveau_transporteur)
            db.session.commit()
            
            logger.info(f"✅ Nouveau transporteur créé: {nouveau_transporteur.nom} ({nouveau_transporteur.email})")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur créé avec succès',
                'transporteur': {
                    'id': nouveau_transporteur.id,
                    'nom': nouveau_transporteur.nom,
                    'email': nouveau_transporteur.email,
                    'telephone': nouveau_transporteur.telephone,
                    'adresse': nouveau_transporteur.adresse,
                    'statut': nouveau_transporteur.statut
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du transporteur: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

# Routes API transporteurs individuels
@app.route('/api/transporteurs/<int:transporteur_id>', methods=['PUT', 'DELETE'])
def api_transporteur_individual(transporteur_id):
    """API pour modifier ou supprimer un transporteur spécifique"""
    try:
        transporteur = Transporteur.query.get(transporteur_id)
        if not transporteur:
            return jsonify({'success': False, 'error': 'Transporteur non trouvé'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            
            # Mettre à jour les champs
            if data.get('nom'):
                transporteur.nom = data['nom']
            if data.get('email'):
                # Vérifier si l'email existe déjà pour un autre transporteur
                existing_transporteur = Transporteur.query.filter_by(email=data['email']).first()
                if existing_transporteur and existing_transporteur.id != transporteur_id:
                    return jsonify({'success': False, 'error': 'Un autre transporteur utilise déjà cet email'}), 400
                transporteur.email = data['email']
            if data.get('telephone'):
                transporteur.telephone = data['telephone']
            if data.get('adresse'):
                transporteur.adresse = data['adresse']
            if data.get('siret'):
                transporteur.siret = data['siret']
            if data.get('statut'):
                transporteur.statut = data['statut']
            
            transporteur.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Transporteur modifié: {transporteur.nom}")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur modifié avec succès',
                'transporteur': {
                    'id': transporteur.id,
                    'nom': transporteur.nom,
                    'email': transporteur.email,
                    'telephone': transporteur.telephone,
                    'adresse': transporteur.adresse,
                    'statut': transporteur.statut
                }
            })
            
        elif request.method == 'DELETE':
            nom_transporteur = transporteur.nom
            db.session.delete(transporteur)
            db.session.commit()
            
            logger.info(f"✅ Transporteur supprimé: {nom_transporteur} (ID: {transporteur_id})")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur supprimé avec succès'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du transporteur {transporteur_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Route d'invitation de transporteur
@app.route('/api/transporteurs/invite', methods=['POST'])
def invite_transporteur():
    """API pour inviter un transporteur par email"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('nom'):
            return jsonify({'success': False, 'error': 'Email et nom sont obligatoires'}), 400
        
        # Vérifier si le transporteur existe déjà
        existing_transporteur = Transporteur.query.filter_by(email=data['email']).first()
        if existing_transporteur:
            return jsonify({'success': False, 'error': 'Un transporteur avec cet email existe déjà'}), 400
        
        # Créer le transporteur avec statut "en_attente"
        nouveau_transporteur = Transporteur(
            nom=data.get('nom'),
            email=data.get('email'),
            telephone=data.get('telephone'),
            adresse=data.get('adresse'),
            siret=data.get('siret'),
            statut='en_attente'
        )
        
        db.session.add(nouveau_transporteur)
        db.session.commit()
        
        logger.info(f"✅ Transporteur invité: {nouveau_transporteur.nom} ({nouveau_transporteur.email})")
        
        return jsonify({
            'success': True,
            'message': 'Invitation envoyée avec succès',
            'transporteur': {
                'id': nouveau_transporteur.id,
                'nom': nouveau_transporteur.nom,
                'email': nouveau_transporteur.email,
                'statut': nouveau_transporteur.statut
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'invitation du transporteur: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Routes API transports restantes
@app.route('/api/transports-v2/<int:transport_id>', methods=['PUT', 'DELETE'])
def api_transport_individual_new(transport_id):
    """API pour modifier ou supprimer un transport spécifique"""
    try:
        transport = Transport.query.get(transport_id)
        if not transport:
            return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            
            # Mettre à jour les champs
            if data.get('ref'):
                transport.ref = data['ref']
            if data.get('type_transport'):
                transport.type_transport = data['type_transport']
            if data.get('niveau_calcul'):
                transport.niveau_calcul = data['niveau_calcul']
            if data.get('type_vehicule'):
                transport.type_vehicule = data['type_vehicule']
            if data.get('energie'):
                transport.energie = data['energie']
            if data.get('conso_vehicule'):
                transport.conso_vehicule = data['conso_vehicule']
            if data.get('poids_tonnes'):
                transport.poids_tonnes = data['poids_tonnes']
            if data.get('distance_km'):
                transport.distance_km = data['distance_km']
            
            transport.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Transport modifié: {transport.ref}")
            
            return jsonify({
                'success': True,
                'message': 'Transport modifié avec succès',
                'transport': {
                    'id': transport.id,
                    'ref': transport.ref,
                    'type_transport': transport.type_transport,
                    'niveau_calcul': transport.niveau_calcul
                }
            })
            
        elif request.method == 'DELETE':
            ref_transport = transport.ref
            db.session.delete(transport)
            db.session.commit()
            
            logger.info(f"✅ Transport supprimé: {ref_transport} (ID: {transport_id})")
            
            return jsonify({
                'success': True,
                'message': 'Transport supprimé avec succès'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du transport {transport_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Routes API utilitaires
@app.route('/api/transports/calculate-distance', methods=['POST'])
def api_calculate_distance():
    """API pour calculer la distance et les émissions entre deux lieux"""
    try:
        data = request.get_json()
        
        if not data.get('lieu_depart') or not data.get('lieu_arrivee'):
            return jsonify({'success': False, 'error': 'Lieu de départ et lieu d\'arrivée sont obligatoires'}), 400
        
        # Ici, vous pourriez intégrer une API de calcul de distance (Google Maps, etc.)
        # Pour l'instant, on retourne des valeurs simulées
        
        distance_km = 150  # Valeur simulée
        emissions_kg = distance_km * 0.1  # Facteur simulé
        
        return jsonify({
            'success': True,
            'distance_km': distance_km,
            'emissions_kg': emissions_kg,
            'lieu_depart': data['lieu_depart'],
            'lieu_arrivee': data['lieu_arrivee']
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de distance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lieux/autocomplete', methods=['GET'])
def api_lieux_autocomplete():
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

# Routes de debug et migration
@app.route('/debug/migrate')
def force_migration():
    """Route pour forcer la migration des colonnes manquantes"""
    try:
        # Vérifier et ajouter les colonnes manquantes
        with db.engine.connect() as conn:
            # Vérifier si la colonne type_transport existe dans la table transports
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' AND column_name = 'type_transport'
            """))
            
            if not result.fetchone():
                # Ajouter la colonne type_transport
                conn.execute(text("ALTER TABLE transports ADD COLUMN type_transport VARCHAR(50)"))
                conn.commit()
                logger.info("✅ Colonne type_transport ajoutée à la table transports")
            
            # Vérifier si la colonne niveau_calcul existe dans la table transports
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' AND column_name = 'niveau_calcul'
            """))
            
            if not result.fetchone():
                # Ajouter la colonne niveau_calcul
                conn.execute(text("ALTER TABLE transports ADD COLUMN niveau_calcul VARCHAR(50)"))
                conn.commit()
                logger.info("✅ Colonne niveau_calcul ajoutée à la table transports")
        
        return jsonify({
            'success': True,
            'message': 'Migration terminée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Routes d'invitations (à migrer vers le blueprint invitations)
@app.route('/invitations')
def invitations():
    """Page de gestion des invitations de clients"""
    try:
        return render_template('invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/clients/<client_id>/invitation-status')
def get_client_invitation_status(client_id):
    """Récupérer le statut d'invitation d'un client"""
    try:
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

@app.route('/invitation/<token>')
def invitation_accept(token):
    """Page pour accepter/refuser une invitation"""
    try:
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return render_template('error.html', error='Invitation non trouvée ou expirée'), 404
        
        return render_template('invitation_accept.html', invitation=invitation)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'invitation: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/invitation/<token>/reponse', methods=['POST'])
def api_invitation_reponse(token):
    """API pour accepter/refuser une invitation"""
    try:
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        data = request.get_json()
        reponse = data.get('reponse')
        
        if reponse not in ['accepte', 'refuse']:
            return jsonify({'success': False, 'error': 'Réponse invalide'}), 400
        
        # Mettre à jour le statut de l'invitation
        invitation.statut = reponse
        invitation.updated_at = datetime.utcnow()
        
        # Si acceptée, activer le client
        if reponse == 'accepte':
            client = Client.query.get(invitation.client_id)
            if client:
                client.statut = 'actif'
                client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Invitation {reponse}: {invitation.email}")
        
        return jsonify({
            'success': True,
            'message': f'Invitation {reponse} avec succès',
            'statut': reponse
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la réponse à l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Routes clients restantes
@app.route('/mon-entreprise')
def mon_entreprise():
    """Page de gestion de l'entreprise (côté client)"""
    try:
        return render_template('mon_entreprise.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de mon entreprise: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Routes d'administration restantes
@app.route('/admin/clients')
def admin_clients_list():
    """Page d'administration - Liste des clients"""
    try:
        # Récupérer tous les clients
        clients = Client.query.all()
        
        # Récupérer les invitations associées
        invitations = Invitation.query.all()
        invitations_by_client = {inv.client_id: inv for inv in invitations}
        
        return render_template('admin/clients.html', 
                            clients=clients, 
                            invitations_by_client=invitations_by_client)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de la liste des clients: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/admin/invitations')
def admin_invitations():
    """Page d'administration - Gestion des invitations"""
    try:
        return render_template('admin/invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/admin/clients/pending')
def admin_clients_pending():
    """Page d'administration - Clients en attente d'acceptation"""
    try:
        # Récupérer les invitations en attente
        invitations_pending = Invitation.query.filter_by(statut='en_attente').order_by(Invitation.created_at.desc()).all()
        
        # Récupérer les clients associés
        clients_pending = []
        for invitation in invitations_pending:
            client = Client.query.get(invitation.client_id)
            if client:
                clients_pending.append({
                    'client': client,
                    'invitation': invitation
                })
        
        return render_template('admin/clients_pending.html', 
                            clients_pending=clients_pending)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients en attente: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Routes API d'administration
@app.route('/api/invitations/<int:invitation_id>/resend', methods=['POST'])
def resend_invitation_admin(invitation_id):
    """Relancer une invitation"""
    try:
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        # Ici, vous pourriez renvoyer l'email d'invitation
        # Pour l'instant, on met juste à jour la date
        
        invitation.created_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Invitation relancée: {invitation.email}")
        
        return jsonify({
            'success': True,
            'message': 'Invitation relancée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du relancement de l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
def delete_invitation(invitation_id):
    """Supprimer une invitation"""
    try:
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        email_invitation = invitation.email
        db.session.delete(invitation)
        db.session.commit()
        
        logger.info(f"✅ Invitation supprimée: {email_invitation}")
        
        return jsonify({
            'success': True,
            'message': 'Invitation supprimée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'invitation: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client_details(client_id):
    """Récupérer les détails d'un client"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        return jsonify({
            'success': True,
            'client': {
                'id': client.id,
                'nom': client.nom,
                'email': client.email,
                'telephone': client.telephone,
                'adresse': client.adresse,
                'siret': client.siret,
                'site_web': client.site_web,
                'description': client.description,
                'statut': client.statut,
                'created_at': client.created_at.isoformat() if client.created_at else None,
                'updated_at': client.updated_at.isoformat() if client.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails du client: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clients', methods=['PUT'])
def update_client():
    """Mettre à jour un client"""
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        client = Client.query.get(data['id'])
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Mettre à jour les champs
        client.nom = data.get('nom', client.nom)
        client.email = data.get('email', client.email)
        client.telephone = data.get('telephone', client.telephone)
        client.adresse = data.get('adresse', client.adresse)
        client.siret = data.get('siret', client.siret)
        client.site_web = data.get('site_web', client.site_web)
        client.description = data.get('description', client.description)
        client.statut = data.get('statut', client.statut)
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Client mis à jour: {client.nom} (ID: {client.id})")
        return jsonify({
            'success': True,
            'message': f'Client "{client.nom}" mis à jour avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du client: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# GESTION DES ERREURS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404"""
    return render_template('error.html', error='Page non trouvée'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500"""
    try:
        db.session.rollback()
    except Exception as rollback_error:
        logger.error(f"❌ Erreur lors du rollback: {str(rollback_error)}")
    
    logger.error(f"❌ Erreur interne 500: {str(error)}")
    logger.error(f"❌ Type d'erreur: {type(error).__name__}")
    
    try:
        return render_template('error.html', error='Erreur interne du serveur'), 500
    except Exception as template_error:
        logger.error(f"❌ Erreur lors du rendu du template d'erreur: {str(template_error)}")
        return f"""
        <html>
        <head><title>Erreur 500 - MyXploit</title></head>
        <body>
            <h1>❌ Erreur interne du serveur</h1>
            <p>Une erreur s'est produite lors du traitement de votre demande.</p>
            <p>Détails: {str(error)}</p>
            <p><a href="/health">Vérifier le statut de l'application</a></p>
        </body>
        </html>
        """, 500

# ============================================================================
# INITIALISATION DE LA BASE DE DONNÉES
# ============================================================================

def init_database():
    """Initialise la base de données et crée les tables"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("✅ Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base: {str(e)}")
        raise

# ============================================================================
# POINT D'ENTRÉE DE L'APPLICATION
# ============================================================================

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
