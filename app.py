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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    energie = db.Column(db.String(50)) # Changed from energie to energie
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
    energie_id = db.Column(db.Integer, db.ForeignKey('energies.id'))
    consommation = db.Column(db.Float)  # L/100km
    emissions = db.Column(db.Float)     # g CO2e/km
    charge_utile = db.Column(db.Float)  # tonnes
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation avec l'énergie
    energie = db.relationship('Energie', backref='vehicules')

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

class Invitation(db.Model):
    """Modèle pour les invitations de clients"""
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    statut = db.Column(db.String(20), default='en_attente')  # en_attente, acceptee, refusee, expiree
    nom_entreprise = db.Column(db.String(100))
    nom_utilisateur = db.Column(db.String(100))
    date_invitation = db.Column(db.DateTime, default=datetime.utcnow)
    date_reponse = db.Column(db.DateTime)
    message_personnalise = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Client(db.Model):
    """Modèle pour les clients"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    siret = db.Column(db.String(14))
    site_web = db.Column(db.String(200))
    description = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')  # actif, inactif
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transporteur(db.Model):
    """Modèle pour les transporteurs"""
    __tablename__ = 'transporteurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    siret = db.Column(db.String(14))
    site_web = db.Column(db.String(200))
    description = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')  # actif, inactif
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def envoyer_email(destinataire, sujet, contenu_html, contenu_texte=None):
    """Fonction pour envoyer des emails"""
    try:
        # Configuration email (à adapter selon votre fournisseur)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        email_emetteur = os.environ.get('EMAIL_EMETTEUR', 'noreply@myxploit.com')
        mot_de_passe = os.environ.get('EMAIL_PASSWORD', '')
        
        # Si pas de mot de passe configuré, simuler l'envoi
        if not mot_de_passe:
            logger.info(f"📧 SIMULATION - Email à {destinataire}: {sujet}")
            return True
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = sujet
        msg['From'] = email_emetteur
        msg['To'] = destinataire
        
        # Ajouter le contenu texte et HTML
        if contenu_texte:
            msg.attach(MIMEText(contenu_texte, 'plain', 'utf-8'))
        msg.attach(MIMEText(contenu_html, 'html', 'utf-8'))
        
        # Envoyer l'email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_emetteur, mot_de_passe)
            server.send_message(msg)
        
        logger.info(f"📧 Email envoyé avec succès à {destinataire}: {sujet}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi d'email à {destinataire}: {str(e)}")
        return False

def envoyer_email_confirmation_client(client):
    """Envoyer un email de confirmation à un nouveau client"""
    sujet = "Bienvenue chez MyXploit - Votre compte a été créé"
    
    contenu_html = f"""
    <html>
    <body>
        <h2>🎉 Bienvenue chez MyXploit !</h2>
        <p>Bonjour {client.nom},</p>
        <p>Votre compte client a été créé avec succès sur notre plateforme MyXploit.</p>
        
        <h3>📋 Vos informations :</h3>
        <ul>
            <li><strong>Nom :</strong> {client.nom}</li>
            <li><strong>Email :</strong> {client.email}</li>
            <li><strong>Téléphone :</strong> {client.telephone or 'Non renseigné'}</li>
        </ul>
        
        <p>Vous pouvez maintenant accéder à votre espace client et commencer à gérer vos transports.</p>
        
        <p>Cordialement,<br>L'équipe MyXploit</p>
    </body>
    </html>
    """
    
    contenu_texte = f"""
    Bienvenue chez MyXploit !
    
    Bonjour {client.nom},
    
    Votre compte client a été créé avec succès sur notre plateforme MyXploit.
    
    Vos informations :
    - Nom : {client.nom}
    - Email : {client.email}
    - Téléphone : {client.telephone or 'Non renseigné'}
    
    Vous pouvez maintenant accéder à votre espace client et commencer à gérer vos transports.
    
    Cordialement,
    L'équipe MyXploit
    """
    
    return envoyer_email(client.email, sujet, contenu_html, contenu_texte)

def envoyer_email_confirmation_transporteur(transporteur):
    """Envoyer un email de confirmation à un nouveau transporteur"""
    sujet = "Bienvenue chez MyXploit - Votre compte transporteur a été créé"
    
    contenu_html = f"""
    <html>
    <body>
        <h2>🚚 Bienvenue chez MyXploit !</h2>
        <p>Bonjour {transporteur.nom},</p>
        <p>Votre compte transporteur a été créé avec succès sur notre plateforme MyXploit.</p>
        
        <h3>📋 Vos informations :</h3>
        <ul>
            <li><strong>Nom :</strong> {transporteur.nom}</li>
            <li><strong>Email :</strong> {transporteur.email}</li>
            <li><strong>Téléphone :</strong> {transporteur.telephone or 'Non renseigné'}</li>
        </ul>
        
        <p>Vous pouvez maintenant accéder à votre espace transporteur et commencer à gérer vos missions de transport.</p>
        
        <p>Cordialement,<br>L'équipe MyXploit</p>
    </body>
    </html>
    """
    
    contenu_texte = f"""
    Bienvenue chez MyXploit !
    
    Bonjour {transporteur.nom},
    
    Votre compte transporteur a été créé avec succès sur notre plateforme MyXploit.
    
    Vos informations :
    - Nom : {transporteur.nom}
    - Email : {transporteur.email}
    - Téléphone : {transporteur.telephone or 'Non renseigné'}
    
    Vous pouvez maintenant accéder à votre espace transporteur et commencer à gérer vos missions de transport.
    
    Cordialement,
    L'équipe MyXploit
    """
    
    return envoyer_email(transporteur.email, sujet, contenu_html, contenu_texte)

# Initialiser la base de données APRÈS la définition des modèles
with app.app_context():
    try:
        logger.info("🚀 Démarrage de l'initialisation de la base de données...")
        db.create_all()
        logger.info("✅ Base de données initialisée avec succès")
        
        # Vérifier le type de base utilisée
        db_url = str(db.engine.url)
        logger.info(f"🔍 URL de la base de données: {db_url}")
        
        if 'postgresql' in db_url:
            logger.info("🐘 Base PostgreSQL confirmée")
        elif 'sqlite' in db_url:
            logger.warning("⚠️ ATTENTION: Base SQLite détectée au lieu de PostgreSQL!")
        else:
            logger.info(f"📊 Type de base: {db_url}")
        
        # Migration automatique pour ajouter les colonnes manquantes
        try:
            logger.info("🔧 Vérification de la structure de la table 'energies'...")
            
            # Vérifier si les colonnes existent déjà
            with db.engine.connect() as conn:
                # Pour PostgreSQL
                if 'postgresql' in str(db.engine.url):
                    logger.info("🐘 Base PostgreSQL détectée - vérification des colonnes...")
                    
                    # Forcer l'ajout des colonnes manquantes (avec gestion d'erreur)
                    columns_to_add = [
                        ('phase_amont', 'FLOAT DEFAULT 0.0'),
                        ('phase_fonctionnement', 'FLOAT DEFAULT 0.0'),
                        ('donnees_supplementaires', 'JSONB DEFAULT \'{}\'')
                    ]
                    
                    # Colonnes pour la table véhicules
                    vehicules_columns_to_add = [
                        ('energie_id', 'INTEGER REFERENCES energies(id)'),
                        ('description', 'TEXT')
                    ]
                    
                    for column_name, column_definition in columns_to_add:
                        try:
                            # Vérifier si la colonne existe
                            result = conn.execute(text(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'energies' 
                                AND column_name = '{column_name}'
                            """))
                            
                            if not result.fetchone():
                                logger.info(f"➕ Ajout de la colonne '{column_name}'...")
                                conn.execute(text(f"ALTER TABLE energies ADD COLUMN {column_name} {column_definition}"))
                                conn.commit()
                                logger.info(f"✅ Colonne '{column_name}' ajoutée")
                            else:
                                logger.info(f"✅ Colonne '{column_name}' existe déjà")
                                
                        except Exception as col_error:
                            if "already exists" in str(col_error).lower() or "duplicate column" in str(col_error).lower():
                                logger.info(f"ℹ️ Colonne '{column_name}' existe déjà (erreur ignorée)")
                            else:
                                logger.warning(f"⚠️ Erreur avec la colonne '{column_name}': {str(col_error)}")
                    
                    # Migration pour la table véhicules
                    logger.info("🔧 Vérification de la structure de la table 'vehicules'...")
                    for column_name, column_definition in vehicules_columns_to_add:
                        try:
                            # Vérifier si la colonne existe
                            result = conn.execute(text(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'vehicules' 
                                AND column_name = '{column_name}'
                            """))
                            
                            if not result.fetchone():
                                logger.info(f"➕ Ajout de la colonne '{column_name}' à la table vehicules...")
                                conn.execute(text(f"ALTER TABLE vehicules ADD COLUMN {column_name} {column_definition}"))
                                conn.commit()
                                logger.info(f"✅ Colonne '{column_name}' ajoutée à vehicules")
                            else:
                                logger.info(f"✅ Colonne '{column_name}' existe déjà dans vehicules")
                                
                        except Exception as col_error:
                            if "already exists" in str(col_error).lower() or "duplicate column" in str(col_error).lower():
                                logger.info(f"ℹ️ Colonne '{column_name}' existe déjà dans vehicules (erreur ignorée)")
                            else:
                                logger.warning(f"⚠️ Erreur avec la colonne '{column_name}' dans vehicules: {str(col_error)}")
                    
                    logger.info("🎉 Migration automatique terminée avec succès !")
                else:
                    logger.info("📱 Base SQLite détectée - pas de migration nécessaire")
                    
        except Exception as migration_error:
            logger.warning(f"⚠️ Migration automatique échouée (non critique): {str(migration_error)}")
            logger.info("ℹ️ L'application continuera sans les nouvelles colonnes")
        
        logger.info("✅ Initialisation de la base de données terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique lors de l'initialisation de la base: {str(e)}")
        logger.error(f"❌ Type d'erreur: {type(e).__name__}")
        # Ne pas lever l'erreur pour permettre le démarrage
        logger.info("ℹ️ L'application tentera de continuer malgré l'erreur")

# Les modèles sont maintenant définis directement dans app.py
# Plus besoin d'importer transport_api

@app.route('/')
def index():
    """Page d'accueil"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'affichage de l'index: {str(e)}")
        return f"""
        <html>
        <head><title>MyXploit - Statut</title></head>
        <body>
            <h1>🚀 MyXploit - Application en cours de démarrage</h1>
            <p>L'application est en cours d'initialisation...</p>
            <p>Erreur: {str(e)}</p>
            <p><a href="/health">Vérifier le statut</a></p>
        </body>
        </html>
        """, 500

@app.route('/myxploit')
def myxploit_home():
    """Page d'accueil MyXploit (côté client)"""
    try:
        return render_template('myxploit_home.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'accueil MyXploit: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/administration')
def administration_home():
    """Page d'accueil Administration (côté admin)"""
    try:
        return render_template('administration_home.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'accueil Administration: {str(e)}")
        return render_template('error.html', error=str(e)), 500

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

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    """API pour récupérer les données du dashboard"""
    try:
        # Simulation de données de dashboard
        dashboard_data = {
            'statistiques': {
                'total_transports': 25,
                'transports_ce_mois': 8,
                'emissions_total': 1250.5,
                'emissions_ce_mois': 320.8,
                'clients_actifs': 12,
                'transporteurs_actifs': 6
            },
            'graphiques': {
                'emissions_par_mois': [
                    {'mois': 'Jan', 'emissions': 280.5},
                    {'mois': 'Fév', 'emissions': 320.8},
                    {'mois': 'Mar', 'emissions': 295.2},
                    {'mois': 'Avr', 'emissions': 354.0}
                ],
                'transports_par_type': [
                    {'type': 'Routier', 'nombre': 15},
                    {'type': 'Ferroviaire', 'nombre': 5},
                    {'type': 'Maritime', 'nombre': 3},
                    {'type': 'Aérien', 'nombre': 2}
                ]
            },
            'transports_recents': [
                {
                    'id': 1,
                    'reference': 'TR-001',
                    'date': '2024-01-15',
                    'client': 'Client Test 1',
                    'emissions': 45.5,
                    'statut': 'terminé'
                },
                {
                    'id': 2,
                    'reference': 'TR-002',
                    'date': '2024-01-16',
                    'client': 'Client Test 2',
                    'emissions': 78.2,
                    'statut': 'en_cours'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données du dashboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/vehicules', methods=['GET', 'POST'])
def api_vehicules():
    """API pour récupérer et créer des véhicules"""
    if request.method == 'GET':
        try:
            vehicules = Vehicule.query.all()
            vehicules_data = []
            
            for v in vehicules:
                # Récupérer le nom de l'énergie si elle existe
                energie_nom = None
                if v.energie_id and v.energie:
                    energie_nom = v.energie.nom
                
                vehicules_data.append({
                    'id': v.id,
                    'nom': v.nom,
                    'type': v.type,
                    'energie_id': v.energie_id,
                    'energie_nom': energie_nom,
                    'consommation': v.consommation,
                    'emissions': v.emissions,
                    'charge_utile': v.charge_utile,
                    'description': v.description
                })
            
            return jsonify({
                'success': True,
                'vehicules': vehicules_data
            })
        
        except Exception as e:
            logger.error(f"Erreur API véhicules GET: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        """Créer un nouveau véhicule"""
        try:
            logger.info("=== CRÉATION DE VÉHICULE ===")
            
            data = request.get_json()
            logger.info(f"📥 Données reçues: {data}")
            
            # Validation des données
            if not data:
                return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400
                
            if not data.get('nom'):
                return jsonify({'success': False, 'error': 'Nom du véhicule requis'}), 400
            
            # Créer le véhicule
            nouveau_vehicule = Vehicule(
                nom=data['nom'],
                type=data.get('type', 'PORTEUR'),
                energie_id=data.get('energie_id'),
                charge_utile=float(data.get('capacite', 0)),
                consommation=float(data.get('consommation', 0)),
                emissions=float(data.get('emissions', 0)),
                description=data.get('description', '')
            )
            
            db.session.add(nouveau_vehicule)
            db.session.commit()
            
            logger.info(f"✅ Véhicule créé avec succès: {nouveau_vehicule.id}")
            
            return jsonify({
                'success': True,
                'message': 'Véhicule créé avec succès',
                'vehicule': {
                    'id': nouveau_vehicule.id,
                    'nom': nouveau_vehicule.nom,
                    'type': nouveau_vehicule.type,
                    'energie_id': nouveau_vehicule.energie_id,
                    'consommation': nouveau_vehicule.consommation,
                    'emissions': nouveau_vehicule.emissions,
                    'charge_utile': nouveau_vehicule.charge_utile,
                    'description': nouveau_vehicule.description
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur création véhicule: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            }), 500

@app.route('/api/vehicules/<int:vehicule_id>', methods=['PUT', 'DELETE'])
def api_vehicule_detail(vehicule_id):
    """API pour modifier et supprimer un véhicule spécifique"""
    try:
        vehicule = Vehicule.query.get(vehicule_id)
        if not vehicule:
            return jsonify({'success': False, 'error': 'Véhicule non trouvé'}), 404
        
        if request.method == 'PUT':
            """Modifier un véhicule"""
            data = request.get_json()
            logger.info(f"📝 Modification véhicule {vehicule_id}: {data}")
            
            if data.get('nom'):
                vehicule.nom = data['nom']
            if data.get('type'):
                vehicule.type = data['type']
            if data.get('energie_id') is not None:
                vehicule.energie_id = data['energie_id']
            if data.get('capacite') is not None:
                vehicule.charge_utile = float(data['capacite'])
            if data.get('consommation') is not None:
                vehicule.consommation = float(data['consommation'])
            if data.get('emissions') is not None:
                vehicule.emissions = float(data['emissions'])
            if data.get('description') is not None:
                vehicule.description = data['description']
            
            db.session.commit()
            logger.info(f"✅ Véhicule {vehicule_id} modifié avec succès")
            
            return jsonify({
                'success': True,
                'message': 'Véhicule modifié avec succès'
            })
        
        elif request.method == 'DELETE':
            """Supprimer un véhicule"""
            db.session.delete(vehicule)
            db.session.commit()
            logger.info(f"✅ Véhicule {vehicule_id} supprimé avec succès")
            
            return jsonify({
                'success': True,
                'message': 'Véhicule supprimé avec succès'
            })
    
    except Exception as e:
        logger.error(f"Erreur API véhicule {vehicule_id}: {str(e)}")
        db.session.rollback()
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
                'unite': e.unite,
                'facteur': e.facteur,
                'description': e.description,
                'phase_amont': getattr(e, 'phase_amont', 0.0),
                'phase_fonctionnement': getattr(e, 'phase_fonctionnement', 0.0),
                'donnees_supplementaires': getattr(e, 'donnees_supplementaires', {})
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
        logger.info("=== CRÉATION D'ÉNERGIE ===")
        
        data = request.get_json()
        logger.info(f"📥 JSON parsé: {data}")
        logger.info(f"📊 Type de données: {type(data)}")
        
        # Validation des données
        if not data:
            logger.error("❌ Données JSON manquantes ou invalides")
            return jsonify({'success': False, 'error': 'Données JSON manquantes ou invalides'}), 400
            
        if not data.get('nom') or not data.get('identifiant'):
            logger.error(f"❌ Validation échouée - nom: '{data.get('nom')}', identifiant: '{data.get('identifiant')}'")
            return jsonify({'success': False, 'error': 'Nom et identifiant requis'}), 400
        
        # Vérifier si l'identifiant existe déjà
        logger.info(f"🔍 Vérification de l'identifiant: {data['identifiant']}")
        energie_existante = Energie.query.filter_by(identifiant=data['identifiant']).first()
        if energie_existante:
            logger.error(f"❌ Identifiant déjà existant: {data['identifiant']} (ID: {energie_existante.id})")
            return jsonify({'success': False, 'error': 'Cet identifiant existe déjà'}), 400
        else:
            logger.info(f"✅ Identifiant disponible: {data['identifiant']}")
        
        # Validation des types de données
        try:
            unite = data.get('unite', 'L')
            logger.info(f"🔍 Unité: '{unite}' (type: {type(unite)})")
            
            facteur = None
            if data.get('facteur') is not None:
                facteur = float(data.get('facteur'))
                logger.info(f"🔍 Facteur: {facteur} (type: {type(facteur)})")
            else:
                logger.info("🔍 Facteur: None (non fourni)")
            
            description = data.get('description', '')
            logger.info(f"🔍 Description: '{description}' (type: {type(description)})")
            
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erreur de conversion de type: {str(e)}")
            return jsonify({'success': False, 'error': f'Type de données invalide: {str(e)}'}), 400
        
        # Créer la nouvelle énergie
        logger.info(f"🏗️ Création de l'énergie avec les données validées:")
        logger.info(f"   - nom: {data['nom']}")
        logger.info(f"   - identifiant: {data['identifiant']}")
        logger.info(f"   - unite: {unite}")
        logger.info(f"   - facteur: {facteur}")
        logger.info(f"   - description: {description}")
        
        nouvelle_energie = Energie(
            nom=data['nom'],
            identifiant=data['identifiant'],
            unite=unite,
            facteur=facteur,
            description=description
        )
        
        logger.info(f"📝 Objet énergie créé: {nouvelle_energie.nom} (ID: {nouvelle_energie.id})")
        logger.info(f"📊 Attributs de l'objet:")
        logger.info(f"   - nom: {nouvelle_energie.nom}")
        logger.info(f"   - identifiant: {nouvelle_energie.identifiant}")
        logger.info(f"   - unite: {nouvelle_energie.unite}")
        logger.info(f"   - facteur: {nouvelle_energie.facteur}")
        logger.info(f"   - description: {nouvelle_energie.description}")
        
        # Vérifier la validité de l'objet avant l'ajout
        try:
            db.session.add(nouvelle_energie)
            logger.info("✅ Objet ajouté à la session")
            
            # Vérifier que l'objet est valide
            db.session.flush()
            logger.info("✅ Objet validé par la base de données")
            
            db.session.commit()
            logger.info(f"💾 Énergie sauvegardée en base avec l'ID: {nouvelle_energie.id}")
            
        except Exception as db_error:
            logger.error(f"❌ Erreur lors de la sauvegarde en base: {str(db_error)}")
            logger.error(f"❌ Type d'erreur: {type(db_error).__name__}")
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Erreur de base de données: {str(db_error)}'}), 500
        
        logger.info(f"✅ Nouvelle énergie créée: {nouvelle_energie.nom}")
        return jsonify({
            'success': True, 
            'message': 'Énergie créée avec succès',
            'energie_id': nouvelle_energie.id,
            'id': nouvelle_energie.id
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de l'énergie: {str(e)}")
        logger.error(f"❌ Type d'erreur: {type(e).__name__}")
        logger.error(f"❌ Détails de l'erreur: {str(e)}")
        
        try:
            db.session.rollback()
            logger.info("✅ Rollback effectué")
        except Exception as rollback_error:
            logger.error(f"❌ Erreur lors du rollback: {str(rollback_error)}")
        
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energies/<int:energie_id>', methods=['PUT'])
def modifier_energie(energie_id):
    """Modifier une énergie existante"""
    try:
        energie = Energie.query.get_or_404(energie_id)
        data = request.get_json()
        
        # Validation des données
        if not data.get('nom'):
            return jsonify({'success': False, 'error': 'Nom requis'}), 400
        
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
        if data.get('facteur') is not None:
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
        
        # Mettre à jour les facteurs avec gestion d'erreur robuste
        try:
            if 'phase_amont' in data:
                if hasattr(energie, 'phase_amont'):
                    energie.phase_amont = float(data['phase_amont'])
                else:
                    logger.warning("⚠️ Colonne 'phase_amont' non disponible")
            
            if 'phase_fonctionnement' in data:
                if hasattr(energie, 'phase_fonctionnement'):
                    energie.phase_fonctionnement = float(data['phase_fonctionnement'])
                else:
                    logger.warning("⚠️ Colonne 'phase_fonctionnement' non disponible")
            
            if 'total' in data:
                energie.facteur = float(data['total'])
            
            # Mettre à jour les données supplémentaires
            if 'donnees_supplementaires' in data:
                if hasattr(energie, 'donnees_supplementaires'):
                    energie.donnees_supplementaires = data['donnees_supplementaires']
                else:
                    logger.warning("⚠️ Colonne 'donnees_supplementaires' non disponible")
                    
        except AttributeError as attr_error:
            logger.warning(f"⚠️ Colonne non disponible: {str(attr_error)}")
            # Continuer avec les colonnes disponibles
        except ValueError as val_error:
            logger.error(f"❌ Erreur de conversion de valeur: {str(val_error)}")
            return jsonify({'success': False, 'error': f'Valeur invalide: {str(val_error)}'}), 400
        
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

@app.route('/api/transports/liste-mise-a-jour')
def liste_transports_mise_a_jour():
    """Endpoint pour récupérer la liste des transports avec les émissions mises à jour"""
    try:
        logger.info("Récupération de la liste des transports mise à jour")
        
        # Récupérer tous les transports
        transports = Transport.query.all()
        transports_data = []
        
        for transport in transports:
            transports_data.append({
                'ref': transport.ref,
                'emis_kg': transport.emis_kg or 0,
                'emis_tkm': transport.emis_tkm or 0,
                'type_transport': transport.type_transport,
                'niveau_calcul': transport.niveau_calcul,
                'type_vehicule': transport.type_vehicule,
                'energie': transport.energie,
                'poids_tonnes': transport.poids_tonnes,
                'distance_km': transport.distance_km,
                'created_at': transport.created_at.isoformat() if transport.created_at else None,
                'updated_at': transport.updated_at.isoformat() if transport.updated_at else None
            })
        
        logger.info(f"Liste mise à jour: {len(transports_data)} transports")
        
        return jsonify({
            'success': True,
            'transports': transports_data,
            'total': len(transports_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste des transports: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/transports', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_transports():
    """API pour gérer les transports"""
    if request.method == 'GET':
        try:
            # Simulation de données transports pour le moment
            transports_data = [
                {
                    'id': 1,
                    'reference': 'TR-001',
                    'date_transport': '2024-01-15',
                    'client': 'Client Test 1',
                    'transporteur': 'Transporteur Test 1',
                    'vehicule': 'Camion 3.5T',
                    'energie': 'Gazole',
                    'distance': 150,
                    'poids': 2.5,
                    'emissions_co2': 45.5,
                    'statut': 'terminé'
                },
                {
                    'id': 2,
                    'reference': 'TR-002',
                    'date_transport': '2024-01-16',
                    'client': 'Client Test 2',
                    'transporteur': 'Transporteur Test 2',
                    'vehicule': 'Camion 7.5T',
                    'energie': 'Gazole',
                    'distance': 200,
                    'poids': 5.0,
                    'emissions_co2': 78.2,
                    'statut': 'en_cours'
                }
            ]
            
            return jsonify({
                'success': True,
                'transports': transports_data
            })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des transports: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Simulation de création d'un transport
            nouveau_transport = {
                'id': len(data) + 1,  # Simulation d'ID
                'reference': f"TR-{len(data) + 1:03d}",
                'date_transport': data.get('date_transport', ''),
                'client': data.get('client', ''),
                'transporteur': data.get('transporteur', ''),
                'vehicule': data.get('vehicule', ''),
                'energie': data.get('energie', ''),
                'distance': data.get('distance', 0),
                'poids': data.get('poids', 0),
                'emissions_co2': data.get('emissions_co2', 0),
                'statut': 'en_cours'
            }
            
            logger.info(f"✅ Nouveau transport créé: {nouveau_transport['reference']}")
            
            return jsonify({
                'success': True,
                'message': 'Transport créé avec succès',
                'transport': nouveau_transport
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du transport: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            transport_id = data.get('id')
            
            # Simulation de mise à jour d'un transport
            transport_modifie = {
                'id': transport_id,
                'reference': data.get('reference', ''),
                'date_transport': data.get('date_transport', ''),
                'client': data.get('client', ''),
                'transporteur': data.get('transporteur', ''),
                'vehicule': data.get('vehicule', ''),
                'energie': data.get('energie', ''),
                'distance': data.get('distance', 0),
                'poids': data.get('poids', 0),
                'emissions_co2': data.get('emissions_co2', 0),
                'statut': data.get('statut', 'en_cours')
            }
            
            logger.info(f"✅ Transport modifié: {transport_modifie['reference']}")
            
            return jsonify({
                'success': True,
                'message': 'Transport modifié avec succès',
                'transport': transport_modifie
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du transport: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            transport_id = data.get('id')
            
            logger.info(f"✅ Transport supprimé: ID {transport_id}")
            
            return jsonify({
                'success': True,
                'message': 'Transport supprimé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du transport: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

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
        db_details = 'Connexion réussie'
    except Exception as e:
        db_status = f'ERROR: {str(e)}'
        db_details = f'Type: {type(e).__name__}'
    
    # Vérifier les modèles
    try:
        energie_count = Energie.query.count()
        transport_count = Transport.query.count()
        vehicule_count = Vehicule.query.count()
        models_status = 'OK'
        models_details = {
            'energies': energie_count,
            'transports': transport_count,
            'vehicules': vehicule_count
        }
    except Exception as e:
        models_status = f'ERROR: {str(e)}'
        models_details = f'Type: {type(e).__name__}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': {
            'status': db_status,
            'details': db_details
        },
        'models': {
            'status': models_status,
            'details': models_details
        },
        'app_info': {
            'flask_version': '2.3.3',
            'sqlalchemy_version': '2.0.43',
            'environment': app.config.get('ENV', 'production')
        }
    })

@app.route('/debug/database')
def debug_database():
    """Route de diagnostic pour la structure de la base de données"""
    try:
        # Vérifier la structure de la table energies
        with db.engine.connect() as conn:
            # Pour PostgreSQL
            if 'postgresql' in str(db.engine.url):
                # Récupérer la structure de la table energies
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'energies'
                    ORDER BY ordinal_position
                """))
                
                columns = []
                for row in result:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2],
                        'default': row[3]
                    })
                
                # Vérifier les colonnes manquantes
                missing_columns = []
                required_columns = ['phase_amont', 'phase_fonctionnement', 'donnees_supplementaires']
                existing_columns = [col['name'] for col in columns]
                
                for col in required_columns:
                    if col not in existing_columns:
                        missing_columns.append(col)
                
                # Vérifier les données existantes
                try:
                    energie_count = Energie.query.count()
                    vehicule_count = Vehicule.query.count()
                    sample_energies = Energie.query.limit(3).all()
                    sample_vehicules = Vehicule.query.limit(3).all()
                    
                    sample_data = {
                        'energies': [],
                        'vehicules': []
                    }
                    
                    for e in sample_energies:
                        sample_data['energies'].append({
                            'id': e.id,
                            'nom': e.nom,
                            'has_phase_amont': hasattr(e, 'phase_amont'),
                            'has_phase_fonctionnement': hasattr(e, 'phase_fonctionnement'),
                            'has_donnees_supplementaires': hasattr(e, 'donnees_supplementaires')
                        })
                    
                    for v in sample_vehicules:
                        sample_data['vehicules'].append({
                            'id': v.id,
                            'nom': v.nom,
                            'type': v.type,
                            'consommation': v.consommation,
                            'emissions': v.emissions,
                            'charge_utile': v.charge_utile
                        })
                        
                except Exception as model_error:
                    sample_data = f"Erreur modèles: {str(model_error)}"
                
                return jsonify({
                    'success': True,
                    'database_type': 'PostgreSQL',
                    'table': 'energies',
                    'columns': columns,
                    'missing_columns': missing_columns,
                    'total_columns': len(columns),
                    'data_info': {
                        'total_energies': energie_count if 'energie_count' in locals() else 'N/A',
                        'sample_data': sample_data
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'database_type': 'SQLite',
                    'message': 'Structure automatiquement gérée par SQLAlchemy'
                })
                
    except Exception as e:
        logger.error(f"❌ Erreur lors du diagnostic de la base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/debug')
def debug_page():
    """Page de debug pour diagnostiquer la base de données"""
    return render_template('debug.html')

@app.route('/debug/invitations')
def debug_invitations():
    """Debug spécifique pour les invitations"""
    try:
        # Vérifier les modèles
        invitations_count = Invitation.query.count()
        clients_count = Client.query.count() if 'Client' in globals() else 0
        transporteurs_count = Transporteur.query.count() if 'Transporteur' in globals() else 0
        
        # Vérifier les templates
        import os
        template_folder = app.template_folder
        invitations_template = os.path.join(template_folder, 'invitations.html')
        base_template = os.path.join(template_folder, 'base.html')
        
        debug_info = {
            'status': 'OK',
            'models': {
                'invitations_count': invitations_count,
                'clients_count': clients_count,
                'transporteurs_count': transporteurs_count
            },
            'templates': {
                'template_folder': template_folder,
                'invitations_template_exists': os.path.exists(invitations_template),
                'base_template_exists': os.path.exists(base_template),
                'invitations_template_path': invitations_template,
                'base_template_path': base_template
            },
            'routes': {
                '/invitations': 'invitations()',
                '/api/invitations': 'api_invitations()',
                '/invitation/<token>': 'invitation_accept(token)'
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Erreur debug invitations: {str(e)}")
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/test-invitations')
def test_invitations_page():
    """Page de test pour diagnostiquer les problèmes d'invitations"""
    try:
        return render_template('test_invitations.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de la page de test invitations: {str(e)}")
        return f"Erreur page de test: {str(e)}", 500

@app.route('/debug/vehicules')
def debug_vehicules_page():
    """Page de debug spécifique pour les véhicules"""
    return render_template('debug_vehicules.html')

@app.route('/parametrage_transporteurs')
def parametrage_transporteurs():
    """Page de paramétrage des transporteurs"""
    try:
        return render_template('parametrage_transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transporteurs: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/parametrage_dashboards')
def parametrage_dashboards():
    """Page de paramétrage des dashboards"""
    try:
        return render_template('parametrage_dashboards.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des dashboards: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/clients')
def clients():
    """Page de gestion des clients (côté client)"""
    try:
        return render_template('clients.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/clients', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_clients():
    """API pour gérer les clients"""
    if request.method == 'GET':
        try:
            clients = Client.query.all()
            clients_data = []
            
            for client in clients:
                clients_data.append({
                    'id': client.id,
                    'nom': client.nom,
                    'email': client.email,
                    'telephone': client.telephone,
                    'adresse': client.adresse,
                    'siret': client.siret,
                    'site_web': client.site_web,
                    'description': client.description,
                    'statut': client.statut,
                    'created_at': client.created_at.strftime('%Y-%m-%d %H:%M:%S') if client.created_at else None
                })
            
            return jsonify({
                'success': True,
                'clients': clients_data
            })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des clients: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation des données
            if not data.get('nom') or not data.get('email'):
                return jsonify({'success': False, 'error': 'Nom et email sont obligatoires'}), 400
            
            # Vérifier si l'email existe déjà
            if Client.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'error': 'Un client avec cet email existe déjà'}), 400
            
            # Créer le nouveau client
            nouveau_client = Client(
                nom=data.get('nom'),
                email=data.get('email'),
                telephone=data.get('telephone'),
                adresse=data.get('adresse'),
                siret=data.get('siret'),
                site_web=data.get('site_web'),
                description=data.get('description'),
                statut='actif'
            )
            
            db.session.add(nouveau_client)
            db.session.commit()
            
            logger.info(f"✅ Nouveau client créé: {nouveau_client.nom} ({nouveau_client.email})")
            
            # Envoyer un email de confirmation
            try:
                email_envoye = envoyer_email_confirmation_client(nouveau_client)
                if email_envoye:
                    logger.info(f"📧 Email de confirmation envoyé à {nouveau_client.email}")
                else:
                    logger.warning(f"⚠️ Échec de l'envoi d'email à {nouveau_client.email}")
            except Exception as email_error:
                logger.warning(f"⚠️ Erreur lors de l'envoi d'email: {str(email_error)}")
            
            return jsonify({
                'success': True,
                'message': 'Client créé avec succès. Un email de confirmation a été envoyé.',
                'client': {
                    'id': nouveau_client.id,
                    'nom': nouveau_client.nom,
                    'email': nouveau_client.email,
                    'telephone': nouveau_client.telephone,
                    'adresse': nouveau_client.adresse,
                    'statut': nouveau_client.statut
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du client: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            client_id = data.get('id')
            
            if not client_id:
                return jsonify({'success': False, 'error': 'ID du client manquant'}), 400
            
            client = Client.query.get(client_id)
            if not client:
                return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
            
            # Mettre à jour les champs
            if data.get('nom'):
                client.nom = data['nom']
            if data.get('email'):
                # Vérifier si l'email existe déjà pour un autre client
                existing_client = Client.query.filter_by(email=data['email']).first()
                if existing_client and existing_client.id != client_id:
                    return jsonify({'success': False, 'error': 'Un autre client utilise déjà cet email'}), 400
                client.email = data['email']
            if data.get('telephone'):
                client.telephone = data['telephone']
            if data.get('adresse'):
                client.adresse = data['adresse']
            if data.get('siret'):
                client.siret = data['siret']
            if data.get('site_web'):
                client.site_web = data['site_web']
            if data.get('description'):
                client.description = data['description']
            if data.get('statut'):
                client.statut = data['statut']
            
            client.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Client modifié: {client.nom}")
            
            return jsonify({
                'success': True,
                'message': 'Client modifié avec succès',
                'client': {
                    'id': client.id,
                    'nom': client.nom,
                    'email': client.email,
                    'telephone': client.telephone,
                    'adresse': client.adresse,
                    'statut': client.statut
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du client: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            client_id = data.get('id')
            
            if not client_id:
                return jsonify({'success': False, 'error': 'ID du client manquant'}), 400
            
            client = Client.query.get(client_id)
            if not client:
                return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
            
            nom_client = client.nom
            db.session.delete(client)
            db.session.commit()
            
            logger.info(f"✅ Client supprimé: {nom_client} (ID: {client_id})")
            
            return jsonify({
                'success': True,
                'message': 'Client supprimé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du client: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/transporteurs')
def transporteurs():
    """Page de gestion des transporteurs (côté client)"""
    try:
        return render_template('transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transporteurs: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/transporteurs', methods=['GET', 'POST', 'PUT', 'DELETE'])
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
                    'site_web': transporteur.site_web,
                    'description': transporteur.description,
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
                site_web=data.get('site_web'),
                description=data.get('description'),
                statut='actif'
            )
            
            db.session.add(nouveau_transporteur)
            db.session.commit()
            
            logger.info(f"✅ Nouveau transporteur créé: {nouveau_transporteur.nom} ({nouveau_transporteur.email})")
            
            # Envoyer un email de confirmation
            try:
                email_envoye = envoyer_email_confirmation_transporteur(nouveau_transporteur)
                if email_envoye:
                    logger.info(f"📧 Email de confirmation envoyé à {nouveau_transporteur.email}")
                else:
                    logger.warning(f"⚠️ Échec de l'envoi d'email à {nouveau_transporteur.email}")
            except Exception as email_error:
                logger.warning(f"⚠️ Erreur lors de l'envoi d'email: {str(email_error)}")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur créé avec succès. Un email de confirmation a été envoyé.',
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
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            transporteur_id = data.get('id')
            
            if not transporteur_id:
                return jsonify({'success': False, 'error': 'ID du transporteur manquant'}), 400
            
            transporteur = Transporteur.query.get(transporteur_id)
            if not transporteur:
                return jsonify({'success': False, 'error': 'Transporteur non trouvé'}), 404
            
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
            if data.get('site_web'):
                transporteur.site_web = data['site_web']
            if data.get('description'):
                transporteur.description = data['description']
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
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du transporteur: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            transporteur_id = data.get('id')
            
            if not transporteur_id:
                return jsonify({'success': False, 'error': 'ID du transporteur manquant'}), 400
            
            transporteur = Transporteur.query.get(transporteur_id)
            if not transporteur:
                return jsonify({'success': False, 'error': 'Transporteur non trouvé'}), 404
            
            nom_transporteur = transporteur.nom
            db.session.delete(transporteur)
            db.session.commit()
            
            logger.info(f"✅ Transporteur supprimé: {nom_transporteur} (ID: {transporteur_id})")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur supprimé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du transporteur: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/parametrage_impact')
def parametrage_impact():
    """Page de configuration de l'impact environnemental"""
    try:
        return render_template('parametrage_impact.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de la configuration d'impact: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/parametrage_systeme')
def parametrage_systeme():
    """Page de paramètres système"""
    try:
        return render_template('parametrage_systeme.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des paramètres système: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/debug/migrate')
def force_migration():
    """Route pour forcer la migration des colonnes manquantes"""
    try:
        with db.engine.connect() as conn:
            if 'postgresql' in str(db.engine.url):
                # Forcer l'ajout des colonnes manquantes
                columns_to_add = [
                    ('phase_amont', 'FLOAT DEFAULT 0.0'),
                    ('phase_fonctionnement', 'FLOAT DEFAULT 0.0'),
                    ('donnees_supplementaires', 'JSONB DEFAULT \'{}\'')
                ]
                
                added_columns = []
                existing_columns = []
                errors = []
                
                for column_name, column_definition in columns_to_add:
                    try:
                        # Vérifier si la colonne existe
                        result = conn.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'energies' 
                            AND column_name = '{column_name}'
                        """))
                        
                        if not result.fetchone():
                            # Ajouter la colonne
                            conn.execute(text(f"ALTER TABLE energies ADD COLUMN {column_name} {column_definition}"))
                            added_columns.append(column_name)
                        else:
                            existing_columns.append(column_name)
                            
                    except Exception as col_error:
                        if "already exists" in str(col_error).lower() or "duplicate column" in str(col_error).lower():
                            existing_columns.append(column_name)
                        else:
                            errors.append(f"{column_name}: {str(col_error)}")
                
                # Valider les changements
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Migration terminée',
                    'added_columns': added_columns,
                    'existing_columns': existing_columns,
                    'errors': errors
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'SQLite détecté - migration non nécessaire'
                })
                
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration forcée: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

# Routes pour les invitations de clients
@app.route('/invitations')
def invitations():
    """Page de gestion des invitations de clients"""
    try:
        logger.info("🔍 Tentative d'accès à la page invitations")
        
        # Vérifier si le template existe
        import os
        template_path = os.path.join(app.template_folder, 'invitations.html')
        if not os.path.exists(template_path):
            logger.error(f"❌ Template non trouvé: {template_path}")
            return f"Template non trouvé: {template_path}", 404
        
        logger.info("✅ Template trouvé, rendu de la page")
        return render_template('invitations.html')
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'affichage des invitations: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/invitations', methods=['GET', 'POST'])
def api_invitations():
    """API pour gérer les invitations"""
    if request.method == 'GET':
        try:
            invitations = Invitation.query.order_by(Invitation.created_at.desc()).all()
            invitations_data = []
            
            for inv in invitations:
                invitations_data.append({
                    'id': inv.id,
                    'email': inv.email,
                    'statut': inv.statut,
                    'nom_entreprise': inv.nom_entreprise,
                    'nom_utilisateur': inv.nom_utilisateur,
                    'date_invitation': inv.date_invitation.strftime('%d/%m/%Y %H:%M') if inv.date_invitation else None,
                    'date_reponse': inv.date_reponse.strftime('%d/%m/%Y %H:%M') if inv.date_reponse else None,
                    'message_personnalise': inv.message_personnalise
                })
            
            return jsonify({
                'success': True,
                'invitations': invitations_data
            })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des invitations: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email')
            message_personnalise = data.get('message_personnalise', '')
            
            if not email:
                return jsonify({'success': False, 'error': 'Email requis'}), 400
            
            # Vérifier si l'email n'est pas déjà invité
            existing_invitation = Invitation.query.filter_by(email=email).first()
            if existing_invitation:
                return jsonify({'success': False, 'error': 'Une invitation existe déjà pour cet email'}), 400
            
            # Générer un token unique
            import secrets
            token = secrets.token_urlsafe(32)
            
            # Créer l'invitation
            invitation = Invitation(
                email=email,
                token=token,
                message_personnalise=message_personnalise
            )
            
            db.session.add(invitation)
            db.session.commit()
            
            # TODO: Envoyer l'email d'invitation
            # Pour l'instant, on simule l'envoi
            logger.info(f"📧 Invitation envoyée à {email} avec le token {token}")
            
            return jsonify({
                'success': True,
                'message': f'Invitation envoyée à {email}',
                'invitation_id': invitation.id
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'invitation: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/invitation/<token>')
def invitation_accept(token):
    """Page pour accepter/refuser une invitation"""
    try:
        invitation = Invitation.query.filter_by(token=token).first()
        
        if not invitation:
            return render_template('error.html', error='Invitation invalide ou expirée'), 404
        
        if invitation.statut != 'en_attente':
            return render_template('error.html', error='Cette invitation a déjà été traitée'), 400
        
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
            return jsonify({'success': False, 'error': 'Invitation invalide'}), 404
        
        if invitation.statut != 'en_attente':
            return jsonify({'success': False, 'error': 'Cette invitation a déjà été traitée'}), 400
        
        data = request.get_json()
        action = data.get('action')  # 'accepter' ou 'refuser'
        nom_entreprise = data.get('nom_entreprise', '')
        nom_utilisateur = data.get('nom_utilisateur', '')
        
        if action == 'accepter':
            if not nom_entreprise or not nom_utilisateur:
                return jsonify({'success': False, 'error': 'Nom d\'entreprise et nom d\'utilisateur requis'}), 400
            
            invitation.statut = 'acceptee'
            invitation.nom_entreprise = nom_entreprise
            invitation.nom_utilisateur = nom_utilisateur
            invitation.date_reponse = datetime.utcnow()
            
            # TODO: Créer le compte utilisateur
            logger.info(f"✅ Invitation acceptée par {nom_utilisateur} ({nom_entreprise})")
            
        elif action == 'refuser':
            invitation.statut = 'refusee'
            invitation.date_reponse = datetime.utcnow()
            logger.info(f"❌ Invitation refusée par {invitation.email}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Invitation {action} avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'invitation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/mon-entreprise')
def mon_entreprise():
    """Page de gestion de l'entreprise (côté client)"""
    try:
        return render_template('mon_entreprise.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de mon entreprise: {str(e)}")
        return render_template('error.html', error=str(e)), 500

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
