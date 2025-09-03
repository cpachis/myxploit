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

# Imports des modèles (définis dans le dossier models/)

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
    # Pour l'instant, retourner None (pas d'authentification)
    return None

@login_manager.request_loader
def load_user_from_request(request):
    """Charge un utilisateur depuis la requête"""
    # Pour l'instant, retourner None (pas d'authentification)
    return None

# Les modèles sont maintenant définis dans le dossier models/

def calculer_distance_km(lieu_depart, lieu_arrivee):
    """Calcule la distance approximative entre deux lieux en km"""
    try:
        import requests
        
        # Utilisation de l'API OpenRouteService (gratuite avec clé)
        # En production, vous devriez utiliser votre propre clé API
        api_key = os.environ.get('OPENROUTE_API_KEY', '')
        
        if not api_key:
            # Si pas d'API key, utiliser des distances approximatives basées sur des villes connues
            return calculer_distance_approximative(lieu_depart, lieu_arrivee)
        
        # Géocoder les lieux
        def geocoder(lieu):
            url = f"https://api.openrouteservice.org/geocode/search"
            params = {
                'api_key': api_key,
                'text': lieu,
                'size': 1
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('features'):
                    coords = data['features'][0]['geometry']['coordinates']
                    return coords[1], coords[0]  # lat, lon
            return None
        
        # Obtenir les coordonnées
        coords_depart = geocoder(lieu_depart)
        coords_arrivee = geocoder(lieu_arrivee)
        
        if not coords_depart or not coords_arrivee:
            return calculer_distance_approximative(lieu_depart, lieu_arrivee)
        
        # Calculer la distance avec l'API de routage
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {'Authorization': api_key}
        body = {
            'coordinates': [coords_depart[::-1], coords_arrivee[::-1]],  # [lon, lat]
            'units': 'km'
        }
        
        response = requests.post(url, json=body, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                distance = data['features'][0]['properties']['segments'][0]['distance']
                return round(distance, 1)
        
        # Fallback vers calcul approximatif
        return calculer_distance_approximative(lieu_depart, lieu_arrivee)
        
    except Exception as e:
        logger.warning(f"Erreur lors du calcul de distance: {str(e)}")
        return calculer_distance_approximative(lieu_depart, lieu_arrivee)

def calculer_distance_approximative(lieu_depart, lieu_arrivee):
    """Calcule une distance approximative basée sur des villes connues"""
    # Base de données simplifiée de distances entre villes françaises principales
    distances_connues = {
        ('Paris', 'Lyon'): 463,
        ('Paris', 'Marseille'): 775,
        ('Paris', 'Toulouse'): 678,
        ('Paris', 'Nantes'): 385,
        ('Paris', 'Strasbourg'): 491,
        ('Paris', 'Montpellier'): 750,
        ('Paris', 'Bordeaux'): 584,
        ('Lyon', 'Marseille'): 314,
        ('Lyon', 'Toulouse'): 538,
        ('Lyon', 'Nantes'): 589,
        ('Marseille', 'Toulouse'): 404,
        ('Marseille', 'Montpellier'): 171,
        ('Toulouse', 'Bordeaux'): 245,
        ('Nantes', 'Bordeaux'): 340,
        ('Strasbourg', 'Lyon'): 493,
        ('Montpellier', 'Toulouse'): 240,
    }
    
    # Normaliser les noms de lieux
    def normaliser_lieu(lieu):
        lieu = lieu.lower().strip()
        # Extraire le nom de la ville principal
        for ville in ['paris', 'lyon', 'marseille', 'toulouse', 'nantes', 'strasbourg', 'montpellier', 'bordeaux']:
            if ville in lieu:
                return ville.title()
        return lieu.title()
    
    lieu_depart_norm = normaliser_lieu(lieu_depart)
    lieu_arrivee_norm = normaliser_lieu(lieu_arrivee)
    
    # Chercher la distance connue
    distance = distances_connues.get((lieu_depart_norm, lieu_arrivee_norm))
    if not distance:
        distance = distances_connues.get((lieu_arrivee_norm, lieu_depart_norm))
    
    if distance:
        return distance
    
    # Si pas de distance connue, estimation basée sur la longueur des noms
    # (très approximatif, mais mieux que rien)
    return 200  # Distance par défaut

def calculer_emissions_carbone(distance_km, poids_tonnes, type_transport='direct'):
    """Calcule les émissions carbone d'un transport"""
    # Facteurs d'émission par type de transport (kg CO2e par tonne-km)
    facteurs_emission = {
        'direct': 0.15,      # Transport routier direct
        'indirect': 0.25,    # Transport avec étapes (plus d'émissions)
    }
    
    facteur = facteurs_emission.get(type_transport, 0.15)
    
    # Calcul des émissions
    emis_kg = distance_km * poids_tonnes * facteur
    emis_tkm = emis_kg / (distance_km * poids_tonnes) if distance_km > 0 and poids_tonnes > 0 else 0
    
    return round(emis_kg, 2), round(emis_tkm, 3)

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

def envoyer_email_invitation(invitation):
    """Envoyer un email d'invitation à un nouveau client"""
    sujet = "Invitation à rejoindre MyXploit - Plateforme de gestion des transports"
    
    # URL de base pour l'acceptation de l'invitation
    base_url = request.host_url.rstrip('/')
    url_acceptation = f"{base_url}/invitation/{invitation.token}"
    
    contenu_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2c3e50; margin-bottom: 10px;">🚛 MyXploit</h1>
                <p style="color: #7f8c8d; font-size: 18px;">Plateforme de gestion des transports</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">🎉 Vous êtes invité à rejoindre MyXploit !</h2>
                
                <p>Bonjour,</p>
                
                <p>Vous avez été invité à rejoindre la plateforme <strong>MyXploit</strong>, notre solution de gestion des transports et de suivi des émissions CO2.</p>
                
                <p>Avec MyXploit, vous pourrez :</p>
                <ul style="color: #2c3e50;">
                    <li>📊 Suivre vos transports et émissions CO2</li>
                    <li>📈 Analyser vos performances environnementales</li>
                    <li>🤝 Collaborer avec vos partenaires logistiques</li>
                    <li>📋 Gérer vos missions de transport efficacement</li>
                </ul>
                
                {f'<p><strong>Message personnalisé :</strong><br><em style="color: #7f8c8d;">{invitation.message_personnalise}</em></p>' if invitation.message_personnalise else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_acceptation}" 
                       style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        ✅ Accepter l'invitation
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #7f8c8d;">
                    <strong>Note :</strong> Ce lien d'invitation est personnel et sécurisé. Ne le partagez pas avec d'autres personnes.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1;">
                <p style="color: #7f8c8d; font-size: 14px;">
                    Si vous ne souhaitez pas rejoindre MyXploit, vous pouvez ignorer cet email.
                </p>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                    © 2025 MyXploit - Plateforme de gestion des transports
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    contenu_texte = f"""
    INVITATION À REJOINDRE MYXPLOIT
    
    Bonjour,
    
    Vous avez été invité à rejoindre la plateforme MyXploit, notre solution de gestion des transports et de suivi des émissions CO2.
    
    Avec MyXploit, vous pourrez :
    - Suivre vos transports et émissions CO2
    - Analyser vos performances environnementales
    - Collaborer avec vos partenaires logistiques
    - Gérer vos missions de transport efficacement
    
    {f'Message personnalisé : {invitation.message_personnalise}' if invitation.message_personnalise else ''}
    
    Pour accepter cette invitation, cliquez sur le lien suivant :
    {url_acceptation}
    
    Note : Ce lien d'invitation est personnel et sécurisé. Ne le partagez pas avec d'autres personnes.
    
    Si vous ne souhaitez pas rejoindre MyXploit, vous pouvez ignorer cet email.
    
    Cordialement,
    L'équipe MyXploit
    """
    
    return envoyer_email(invitation.email, sujet, contenu_html, contenu_texte)

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
        
        # Migration pour ajouter les nouvelles colonnes au modèle Transport
        try:
            logger.info("🔧 Migration du modèle Transport...")
            
            # Détecter le type de base de données
            db_url = str(db.engine.url)
            is_postgresql = 'postgresql' in db_url
            
            if is_postgresql:
                logger.info("🐘 Migration PostgreSQL détectée")
                # Pour PostgreSQL, utiliser information_schema
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'transports' AND table_schema = 'public'
                """))
                columns = [row[0] for row in result.fetchall()]
            else:
                logger.info("📱 Migration SQLite détectée")
                # Pour SQLite, utiliser PRAGMA
                result = db.session.execute(text("PRAGMA table_info(transports)"))
                columns = [row[1] for row in result.fetchall()]
            
            logger.info(f"📋 Colonnes existantes: {columns}")
            
            # Ajouter les colonnes manquantes
            if 'date' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN date DATE"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN date DATE"))
                logger.info("✅ Colonne 'date' ajoutée")
            
            if 'lieu_collecte' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN lieu_collecte VARCHAR(200)"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN lieu_collecte VARCHAR(200)"))
                logger.info("✅ Colonne 'lieu_collecte' ajoutée")
            
            if 'lieu_livraison' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN lieu_livraison VARCHAR(200)"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN lieu_livraison VARCHAR(200)"))
                logger.info("✅ Colonne 'lieu_livraison' ajoutée")
            
            if 'poids_tonnes' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN poids_tonnes REAL"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN poids_tonnes FLOAT"))
                logger.info("✅ Colonne 'poids_tonnes' ajoutée")
            
            if 'type_transport' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN type_transport VARCHAR(50) DEFAULT 'direct'"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN type_transport VARCHAR(50) DEFAULT 'direct'"))
                logger.info("✅ Colonne 'type_transport' ajoutée")
            
            if 'distance_km' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN distance_km REAL DEFAULT 0.0"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN distance_km FLOAT DEFAULT 0.0"))
                logger.info("✅ Colonne 'distance_km' ajoutée")
            
            if 'emis_kg' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN emis_kg REAL DEFAULT 0.0"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN emis_kg FLOAT DEFAULT 0.0"))
                logger.info("✅ Colonne 'emis_kg' ajoutée")
            
            if 'emis_tkm' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN emis_tkm REAL DEFAULT 0.0"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN emis_tkm FLOAT DEFAULT 0.0"))
                logger.info("✅ Colonne 'emis_tkm' ajoutée")
            
            if 'client' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN client VARCHAR(100)"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN client VARCHAR(100)"))
                logger.info("✅ Colonne 'client' ajoutée")
            
            if 'transporteur' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN transporteur VARCHAR(100)"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN transporteur VARCHAR(100)"))
                logger.info("✅ Colonne 'transporteur' ajoutée")
            
            if 'description' not in columns:
                if is_postgresql:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN description TEXT"))
                else:
                    db.session.execute(text("ALTER TABLE transports ADD COLUMN description TEXT"))
                logger.info("✅ Colonne 'description' ajoutée")
            
            db.session.commit()
            logger.info("✅ Migration du modèle Transport terminée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la migration du modèle Transport: {str(e)}")
            db.session.rollback()
        
        logger.info("✅ Initialisation de la base de données terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique lors de l'initialisation de la base: {str(e)}")
        logger.error(f"❌ Type d'erreur: {type(e).__name__}")
        # Ne pas lever l'erreur pour permettre le démarrage
        logger.info("ℹ️ L'application tentera de continuer malgré l'erreur")

# Les modèles sont maintenant définis directement dans app.py
# Plus besoin d'importer transport_api

# Les routes principales sont maintenant dans le blueprint main_bp

# Les routes /myxploit et /administration sont maintenant dans les blueprints

# La route /dashboard est maintenant dans le blueprint main_bp

# L'API /api/dashboard est maintenant dans le blueprint api_bp

# Routes de transport migrées vers le blueprint transports_bp

# Les routes API véhicules sont maintenant dans le blueprint api_vehicules_bp

# La route API véhicule detail est maintenant dans le blueprint api_vehicules_bp

# La route API énergies est maintenant dans le blueprint api_energies_bp

# Route /administration migrée vers le blueprint admin_bp

# Route /parametrage_clients migrée vers le blueprint parametrage_bp

# Route /parametrage_energies migrée vers le blueprint parametrage_bp

# La route API énergies POST est maintenant dans le blueprint api_energies_bp

# La route API énergies PUT est maintenant dans le blueprint api_energies_bp

# La route API énergies DELETE est maintenant dans le blueprint api_energies_bp

# La route API énergies facteurs est maintenant dans le blueprint api_energies_bp

# Les routes API énergies données sont maintenant dans le blueprint api_energies_bp

# Route /parametrage_vehicules migrée vers le blueprint parametrage_bp



@app.route('/import_csv')
def import_csv():
    """Page d'import CSV"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'import CSV: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Routes /nouveau_transport et /transport migrées vers le blueprint transports_bp

# Route /import_transports_csv migrée vers le blueprint transports_bp

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

# La route API transports recalculer-emissions est maintenant dans le blueprint api_transports_bp

# La route API transports liste-mise-a-jour est maintenant dans le blueprint api_transports_bp

# La route API transports est maintenant dans le blueprint api_transports_bp
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

# Routes /parametrage_transporteurs et /parametrage_dashboards migrées vers le blueprint parametrage_bp

# Route /clients migrée vers le blueprint clients_bp

# Code API clients migré vers le blueprint api_clients_bp
    
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

# La route API clients DELETE est maintenant dans le blueprint api_clients_bp
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        nom_client = client.nom
        
        # Vérifier s'il y a des transports associés à ce client
        # Les transports utilisent un champ 'client' (string) et non 'client_id'
        try:
            from sqlalchemy import text
            transports_count = db.session.execute(
                text("SELECT COUNT(*) FROM transports WHERE client = :client_ref"),
                {'client_ref': f'CL{client_id:03d}'}  # Format CL001, CL002, etc.
            ).scalar()
            
            if transports_count > 0:
                return jsonify({
                    'success': False, 
                    'error': f'Impossible de supprimer ce client car il a {transports_count} transport(s) associé(s). Supprimez d\'abord les transports.'
                }), 400
        except Exception as db_error:
            # Si la table transports n'existe pas ou a une structure différente, on continue
            logger.warning(f"⚠️ Impossible de vérifier les transports: {str(db_error)}")
            pass
        
        # Supprimer les invitations associées à ce client
        invitations = Invitation.query.filter_by(email=client.email).all()
        for invitation in invitations:
            db.session.delete(invitation)
        
        # Supprimer le client
        db.session.delete(client)
        db.session.commit()
        
        logger.info(f"✅ Client supprimé: {nom_client} (ID: {client_id})")
        
        return jsonify({
            'success': True,
            'message': f'Client "{nom_client}" supprimé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du client {client_id}: {str(e)}")
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

@app.route('/api/transporteurs/<int:transporteur_id>', methods=['PUT', 'DELETE'])
def api_transporteur_individual(transporteur_id):
    """API pour modifier ou supprimer un transporteur spécifique"""
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
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

@app.route('/api/transporteurs/invite', methods=['POST'])
def invite_transporteur():
    """API pour inviter un transporteur par email"""
    try:
        data = request.get_json()
        transporteur_id = data.get('transporteur_id')
        message_personnalise = data.get('message', '')
        
        if not transporteur_id:
            return jsonify({'success': False, 'error': 'ID du transporteur manquant'}), 400
        
        transporteur = Transporteur.query.get(transporteur_id)
        if not transporteur:
            return jsonify({'success': False, 'error': 'Transporteur non trouvé'}), 404
        
        if not transporteur.email:
            return jsonify({'success': False, 'error': 'Aucun email configuré pour ce transporteur'}), 400
        
        # Créer le contenu de l'email d'invitation
        sujet = f"Invitation à rejoindre MyXploit - {transporteur.nom}"
        
        contenu_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invitation MyXploit</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .btn {{ display: inline-block; background: #48bb78; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚚 Invitation MyXploit</h1>
                    <p>Rejoignez notre plateforme de gestion des transports</p>
                </div>
                <div class="content">
                    <h2>Bonjour {transporteur.nom},</h2>
                    <p>Vous avez été invité à rejoindre la plateforme <strong>MyXploit</strong> pour gérer vos transports et optimiser votre empreinte carbone.</p>
                    
                    {f'<p><em>"{message_personnalise}"</em></p>' if message_personnalise else ''}
                    
                    <h3>🎯 Avantages de MyXploit :</h3>
                    <ul>
                        <li>📊 Suivi en temps réel de vos émissions CO₂</li>
                        <li>📈 Tableaux de bord et rapports détaillés</li>
                        <li>🚛 Gestion complète de votre flotte</li>
                        <li>🌱 Optimisation de votre impact environnemental</li>
                        <li>📱 Interface moderne et intuitive</li>
                    </ul>
                    
                    <p>Cliquez sur le bouton ci-dessous pour accéder à votre espace :</p>
                    <a href="https://myxploit-transports.onrender.com/login" class="btn">Accéder à MyXploit</a>
                    
                    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
                    
                    <p>Cordialement,<br>L'équipe MyXploit</p>
                </div>
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement par MyXploit</p>
                    <p>Si vous ne souhaitez plus recevoir ces emails, vous pouvez nous le signaler.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        contenu_texte = f"""
        Invitation MyXploit
        
        Bonjour {transporteur.nom},
        
        Vous avez été invité à rejoindre la plateforme MyXploit pour gérer vos transports et optimiser votre empreinte carbone.
        
        {f'Message personnalisé: "{message_personnalise}"' if message_personnalise else ''}
        
        Avantages de MyXploit :
        - Suivi en temps réel de vos émissions CO₂
        - Tableaux de bord et rapports détaillés
        - Gestion complète de votre flotte
        - Optimisation de votre impact environnemental
        - Interface moderne et intuitive
        
        Accédez à votre espace : https://myxploit-transports.onrender.com/login
        
        Si vous avez des questions, n'hésitez pas à nous contacter.
        
        Cordialement,
        L'équipe MyXploit
        """
        
        # Envoyer l'email
        email_envoye = envoyer_email(transporteur.email, sujet, contenu_html, contenu_texte)
        
        if email_envoye:
            logger.info(f"📧 Invitation envoyée à {transporteur.nom} ({transporteur.email})")
            return jsonify({
                'success': True,
                'message': f'Invitation envoyée avec succès à {transporteur.email}'
            })
        else:
            logger.warning(f"⚠️ Échec de l'envoi d'invitation à {transporteur.email}")
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'envoi de l\'email'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors de l'invitation du transporteur: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# La route API transports-v2 est maintenant dans le blueprint api_transports_bp
    if request.method == 'GET':
        try:
            transports = Transport.query.all()
            transports_data = []
            
            for transport in transports:
                transports_data.append({
                    'id': transport.id,
                    'ref': transport.ref,
                    'date': transport.date.strftime('%Y-%m-%d') if transport.date else None,
                    'lieu_collecte': transport.lieu_collecte,
                    'lieu_livraison': transport.lieu_livraison,
                    'poids_tonnes': transport.poids_tonnes,
                    'type_transport': transport.type_transport,
                    'distance_km': transport.distance_km,
                    'emis_kg': transport.emis_kg,
                    'emis_tkm': transport.emis_tkm,
                    'client': transport.client,
                    'transporteur': transport.transporteur,
                    'description': transport.description,
                    'created_at': transport.created_at.strftime('%Y-%m-%d %H:%M:%S') if transport.created_at else None
                })
            
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
            
            # Validation des données obligatoires
            if not data.get('ref') or not data.get('date') or not data.get('lieu_collecte') or not data.get('lieu_livraison') or not data.get('poids_tonnes'):
                return jsonify({'success': False, 'error': 'Tous les champs obligatoires doivent être remplis'}), 400
            
            # Vérifier si la référence existe déjà
            if Transport.query.filter_by(ref=data['ref']).first():
                return jsonify({'success': False, 'error': 'Une référence de transport avec ce nom existe déjà'}), 400
            
            # Calculer la distance si pas fournie
            distance_km = data.get('distance_km', 0)
            if distance_km == 0:
                distance_km = calculer_distance_km(data['lieu_collecte'], data['lieu_livraison'])
            
            # Calculer les émissions
            emis_kg, emis_tkm = calculer_emissions_carbone(
                distance_km, 
                data['poids_tonnes'], 
                data.get('type_transport', 'direct')
            )
            
            # Créer le nouveau transport
            nouveau_transport = Transport(
                ref=data['ref'],
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                lieu_collecte=data['lieu_collecte'],
                lieu_livraison=data['lieu_livraison'],
                poids_tonnes=data['poids_tonnes'],
                type_transport=data.get('type_transport', 'direct'),
                distance_km=distance_km,
                emis_kg=emis_kg,
                emis_tkm=emis_tkm,
                client=data.get('client'),
                transporteur=data.get('transporteur'),
                description=data.get('description')
            )
            
            db.session.add(nouveau_transport)
            db.session.commit()
            
            logger.info(f"✅ Nouveau transport créé: {nouveau_transport.ref}")
            
            return jsonify({
                'success': True,
                'message': 'Transport créé avec succès',
                'transport': {
                    'id': nouveau_transport.id,
                    'ref': nouveau_transport.ref,
                    'date': nouveau_transport.date.strftime('%Y-%m-%d'),
                    'lieu_collecte': nouveau_transport.lieu_collecte,
                    'lieu_livraison': nouveau_transport.lieu_livraison,
                    'poids_tonnes': nouveau_transport.poids_tonnes,
                    'type_transport': nouveau_transport.type_transport,
                    'distance_km': nouveau_transport.distance_km,
                    'emis_kg': nouveau_transport.emis_kg,
                    'emis_tkm': nouveau_transport.emis_tkm
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du transport: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transports-v2/<int:transport_id>', methods=['PUT', 'DELETE'])
def api_transport_individual_new(transport_id):
    """API pour modifier ou supprimer un transport spécifique"""
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            transport = Transport.query.get(transport_id)
            if not transport:
                return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
            
            # Mettre à jour les champs
            if data.get('ref'):
                # Vérifier si la référence existe déjà pour un autre transport
                existing_transport = Transport.query.filter_by(ref=data['ref']).first()
                if existing_transport and existing_transport.id != transport_id:
                    return jsonify({'success': False, 'error': 'Une référence de transport avec ce nom existe déjà'}), 400
                transport.ref = data['ref']
            
            if data.get('date'):
                transport.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            if data.get('lieu_collecte'):
                transport.lieu_collecte = data['lieu_collecte']
            
            if data.get('lieu_livraison'):
                transport.lieu_livraison = data['lieu_livraison']
            
            if data.get('poids_tonnes'):
                transport.poids_tonnes = data['poids_tonnes']
            
            if data.get('type_transport'):
                transport.type_transport = data['type_transport']
            
            # Recalculer la distance et les émissions si les lieux ou le poids ont changé
            if (data.get('lieu_collecte') or data.get('lieu_livraison') or 
                data.get('poids_tonnes') or data.get('type_transport')):
                
                distance_km = calculer_distance_km(transport.lieu_collecte, transport.lieu_livraison)
                emis_kg, emis_tkm = calculer_emissions_carbone(
                    distance_km, 
                    transport.poids_tonnes, 
                    transport.type_transport
                )
                
                transport.distance_km = distance_km
                transport.emis_kg = emis_kg
                transport.emis_tkm = emis_tkm
            
            # Mettre à jour les autres champs
            if data.get('client'):
                transport.client = data['client']
            if data.get('transporteur'):
                transport.transporteur = data['transporteur']
            if data.get('description'):
                transport.description = data['description']
            
            transport.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Transport modifié: {transport.ref}")
            
            return jsonify({
                'success': True,
                'message': 'Transport modifié avec succès',
                'transport': {
                    'id': transport.id,
                    'ref': transport.ref,
                    'date': transport.date.strftime('%Y-%m-%d'),
                    'lieu_collecte': transport.lieu_collecte,
                    'lieu_livraison': transport.lieu_livraison,
                    'poids_tonnes': transport.poids_tonnes,
                    'type_transport': transport.type_transport,
                    'distance_km': transport.distance_km,
                    'emis_kg': transport.emis_kg,
                    'emis_tkm': transport.emis_tkm
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du transport: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            transport = Transport.query.get(transport_id)
            if not transport:
                return jsonify({'success': False, 'error': 'Transport non trouvé'}), 404
            
            ref_transport = transport.ref
            db.session.delete(transport)
            db.session.commit()
            
            logger.info(f"✅ Transport supprimé: {ref_transport} (ID: {transport_id})")
            
            return jsonify({
                'success': True,
                'message': 'Transport supprimé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du transport: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transports/calculate-distance', methods=['POST'])
def api_calculate_distance():
    """API pour calculer la distance et les émissions entre deux lieux"""
    try:
        data = request.get_json()
        
        lieu_depart = data.get('lieu_depart')
        lieu_arrivee = data.get('lieu_arrivee')
        poids_tonnes = data.get('poids_tonnes', 0)
        type_transport = data.get('type_transport', 'direct')
        
        if not lieu_depart or not lieu_arrivee:
            return jsonify({'success': False, 'error': 'Les lieux de départ et d\'arrivée sont obligatoires'}), 400
        
        # Calculer la distance
        distance_km = calculer_distance_km(lieu_depart, lieu_arrivee)
        
        # Calculer les émissions
        emis_kg, emis_tkm = calculer_emissions_carbone(distance_km, poids_tonnes, type_transport)
        
        return jsonify({
            'success': True,
            'distance_km': distance_km,
            'emis_kg': emis_kg,
            'emis_tkm': emis_tkm
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de distance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lieux/autocomplete', methods=['GET'])
def api_lieux_autocomplete():
    """API pour l'autocomplétion des lieux (codes postaux et villes)"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'suggestions': []
            })
        
        # Base de données étendue des villes françaises avec codes postaux
        villes_france = [
            # Paris et région parisienne
            {"nom": "Paris", "code_postal": "75001", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75002", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75003", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75004", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75005", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75006", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75007", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75008", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75009", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75010", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75011", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75012", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75013", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75014", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75015", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75016", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75017", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75018", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75019", "departement": "75", "region": "Île-de-France"},
            {"nom": "Paris", "code_postal": "75020", "departement": "75", "region": "Île-de-France"},
            
            # Banlieue parisienne
            {"nom": "Boulogne-Billancourt", "code_postal": "92100", "departement": "92", "region": "Île-de-France"},
            {"nom": "Montreuil", "code_postal": "93100", "departement": "93", "region": "Île-de-France"},
            {"nom": "Saint-Denis", "code_postal": "93200", "departement": "93", "region": "Île-de-France"},
            {"nom": "Argenteuil", "code_postal": "95100", "departement": "95", "region": "Île-de-France"},
            {"nom": "Montrouge", "code_postal": "92120", "departement": "92", "region": "Île-de-France"},
            {"nom": "Nanterre", "code_postal": "92000", "departement": "92", "region": "Île-de-France"},
            {"nom": "Vitry-sur-Seine", "code_postal": "94400", "departement": "94", "region": "Île-de-France"},
            {"nom": "Créteil", "code_postal": "94000", "departement": "94", "region": "Île-de-France"},
            {"nom": "Colombes", "code_postal": "92700", "departement": "92", "region": "Île-de-France"},
            {"nom": "Aubervilliers", "code_postal": "93300", "departement": "93", "region": "Île-de-France"},
            {"nom": "Asnières-sur-Seine", "code_postal": "92600", "departement": "92", "region": "Île-de-France"},
            {"nom": "Courbevoie", "code_postal": "92400", "departement": "92", "region": "Île-de-France"},
            {"nom": "Rueil-Malmaison", "code_postal": "92500", "departement": "92", "region": "Île-de-France"},
            {"nom": "Champigny-sur-Marne", "code_postal": "94500", "departement": "94", "region": "Île-de-France"},
            {"nom": "Saint-Maur-des-Fossés", "code_postal": "94100", "departement": "94", "region": "Île-de-France"},
            {"nom": "Drancy", "code_postal": "93700", "departement": "93", "region": "Île-de-France"},
            {"nom": "Issy-les-Moulineaux", "code_postal": "92130", "departement": "92", "region": "Île-de-France"},
            {"nom": "Noisy-le-Grand", "code_postal": "93160", "departement": "93", "region": "Île-de-France"},
            {"nom": "Levallois-Perret", "code_postal": "92300", "departement": "92", "region": "Île-de-France"},
            {"nom": "Antony", "code_postal": "92160", "departement": "92", "region": "Île-de-France"},
            
            # Lyon et région lyonnaise
            {"nom": "Lyon", "code_postal": "69001", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69002", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69003", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69004", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69005", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69006", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69007", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69008", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Lyon", "code_postal": "69009", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Villeurbanne", "code_postal": "69100", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Vénissieux", "code_postal": "69200", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Priest", "code_postal": "69800", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Caluire-et-Cuire", "code_postal": "69300", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Vaulx-en-Velin", "code_postal": "69120", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Bron", "code_postal": "69500", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Décines-Charpieu", "code_postal": "69150", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Oullins", "code_postal": "69600", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Pierre-Bénite", "code_postal": "69310", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Rillieux-la-Pape", "code_postal": "69140", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Meyzieu", "code_postal": "69330", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            
            # Marseille et région marseillaise
            {"nom": "Marseille", "code_postal": "13001", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13002", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13003", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13004", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13005", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13006", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13007", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13008", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13009", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13010", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13011", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13012", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13013", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13014", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13015", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marseille", "code_postal": "13016", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Aix-en-Provence", "code_postal": "13100", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Aubagne", "code_postal": "13400", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "La Ciotat", "code_postal": "13600", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Vitrolles", "code_postal": "13127", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Marignane", "code_postal": "13700", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Martigues", "code_postal": "13500", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Istres", "code_postal": "13800", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Salon-de-Provence", "code_postal": "13300", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Arles", "code_postal": "13200", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Tarascon", "code_postal": "13150", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Miramas", "code_postal": "13140", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Port-de-Bouc", "code_postal": "13110", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Fos-sur-Mer", "code_postal": "13270", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            
            # Toulouse et région toulousaine
            {"nom": "Toulouse", "code_postal": "31000", "departement": "31", "region": "Occitanie"},
            {"nom": "Toulouse", "code_postal": "31100", "departement": "31", "region": "Occitanie"},
            {"nom": "Toulouse", "code_postal": "31200", "departement": "31", "region": "Occitanie"},
            {"nom": "Toulouse", "code_postal": "31300", "departement": "31", "region": "Occitanie"},
            {"nom": "Toulouse", "code_postal": "31400", "departement": "31", "region": "Occitanie"},
            {"nom": "Toulouse", "code_postal": "31500", "departement": "31", "region": "Occitanie"},
            {"nom": "Colomiers", "code_postal": "31770", "departement": "31", "region": "Occitanie"},
            {"nom": "Tournefeuille", "code_postal": "31170", "departement": "31", "region": "Occitanie"},
            {"nom": "Blagnac", "code_postal": "31700", "departement": "31", "region": "Occitanie"},
            {"nom": "Muret", "code_postal": "31600", "departement": "31", "region": "Occitanie"},
            {"nom": "Plaisance-du-Touch", "code_postal": "31830", "departement": "31", "region": "Occitanie"},
            {"nom": "Cugnaux", "code_postal": "31270", "departement": "31", "region": "Occitanie"},
            {"nom": "Balma", "code_postal": "31130", "departement": "31", "region": "Occitanie"},
            {"nom": "L'Union", "code_postal": "31240", "departement": "31", "region": "Occitanie"},
            {"nom": "Ramonville-Saint-Agne", "code_postal": "31520", "departement": "31", "region": "Occitanie"},
            
            # Nice et Côte d'Azur
            {"nom": "Nice", "code_postal": "06000", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Nice", "code_postal": "06100", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Nice", "code_postal": "06200", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Nice", "code_postal": "06300", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Cannes", "code_postal": "06400", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Antibes", "code_postal": "06600", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Grasse", "code_postal": "06130", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Cagnes-sur-Mer", "code_postal": "06800", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Menton", "code_postal": "06500", "departement": "06", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Monaco", "code_postal": "98000", "departement": "98", "region": "Monaco"},
            
            # Nantes et région nantaise
            {"nom": "Nantes", "code_postal": "44000", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Nantes", "code_postal": "44100", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Nantes", "code_postal": "44200", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Nantes", "code_postal": "44300", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Saint-Nazaire", "code_postal": "44600", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "La Roche-sur-Yon", "code_postal": "85000", "departement": "85", "region": "Pays de la Loire"},
            {"nom": "Le Mans", "code_postal": "72000", "departement": "72", "region": "Pays de la Loire"},
            {"nom": "Angers", "code_postal": "49000", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Cholet", "code_postal": "49300", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Laval", "code_postal": "53000", "departement": "53", "region": "Pays de la Loire"},
            {"nom": "Rezé", "code_postal": "44400", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Orvault", "code_postal": "44700", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Vertou", "code_postal": "44120", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Carquefou", "code_postal": "44470", "departement": "44", "region": "Pays de la Loire"},
            {"nom": "Saint-Herblain", "code_postal": "44800", "departement": "44", "region": "Pays de la Loire"},
            
            # Strasbourg et région strasbourgeoise
            {"nom": "Strasbourg", "code_postal": "67000", "departement": "67", "region": "Grand Est"},
            {"nom": "Strasbourg", "code_postal": "67100", "departement": "67", "region": "Grand Est"},
            {"nom": "Mulhouse", "code_postal": "68100", "departement": "68", "region": "Grand Est"},
            {"nom": "Colmar", "code_postal": "68000", "departement": "68", "region": "Grand Est"},
            {"nom": "Haguenau", "code_postal": "67500", "departement": "67", "region": "Grand Est"},
            {"nom": "Schiltigheim", "code_postal": "67300", "departement": "67", "region": "Grand Est"},
            {"nom": "Illkirch-Graffenstaden", "code_postal": "67400", "departement": "67", "region": "Grand Est"},
            {"nom": "Saint-Louis", "code_postal": "68300", "departement": "68", "region": "Grand Est"},
            {"nom": "Wittenheim", "code_postal": "68270", "departement": "68", "region": "Grand Est"},
            {"nom": "Kingersheim", "code_postal": "68260", "departement": "68", "region": "Grand Est"},
            
            # Montpellier et région montpelliéraine
            {"nom": "Montpellier", "code_postal": "34000", "departement": "34", "region": "Occitanie"},
            {"nom": "Montpellier", "code_postal": "34070", "departement": "34", "region": "Occitanie"},
            {"nom": "Montpellier", "code_postal": "34080", "departement": "34", "region": "Occitanie"},
            {"nom": "Montpellier", "code_postal": "34090", "departement": "34", "region": "Occitanie"},
            {"nom": "Béziers", "code_postal": "34500", "departement": "34", "region": "Occitanie"},
            {"nom": "Nîmes", "code_postal": "30000", "departement": "30", "region": "Occitanie"},
            {"nom": "Perpignan", "code_postal": "66000", "departement": "66", "region": "Occitanie"},
            {"nom": "Sète", "code_postal": "34200", "departement": "34", "region": "Occitanie"},
            {"nom": "Alès", "code_postal": "30100", "departement": "30", "region": "Occitanie"},
            {"nom": "Lunel", "code_postal": "34400", "departement": "34", "region": "Occitanie"},
            {"nom": "Agde", "code_postal": "34300", "departement": "34", "region": "Occitanie"},
            {"nom": "Frontignan", "code_postal": "34110", "departement": "34", "region": "Occitanie"},
            {"nom": "Castelnau-le-Lez", "code_postal": "34170", "departement": "34", "region": "Occitanie"},
            {"nom": "Lattes", "code_postal": "34970", "departement": "34", "region": "Occitanie"},
            {"nom": "Mauguio", "code_postal": "34130", "departement": "34", "region": "Occitanie"},
            
            # Bordeaux et région bordelaise
            {"nom": "Bordeaux", "code_postal": "33000", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Bordeaux", "code_postal": "33100", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Bordeaux", "code_postal": "33200", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Bordeaux", "code_postal": "33300", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Pessac", "code_postal": "33600", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Mérignac", "code_postal": "33700", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Talence", "code_postal": "33400", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Villenave-d'Ornon", "code_postal": "33140", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Bègles", "code_postal": "33130", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Gradignan", "code_postal": "33170", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Cenon", "code_postal": "33150", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Lormont", "code_postal": "33310", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Pessac", "code_postal": "33600", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Le Bouscat", "code_postal": "33110", "departement": "33", "region": "Nouvelle-Aquitaine"},
            {"nom": "Eysines", "code_postal": "33320", "departement": "33", "region": "Nouvelle-Aquitaine"},
            
            # Lille et région lilloise
            {"nom": "Lille", "code_postal": "59000", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Lille", "code_postal": "59100", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Lille", "code_postal": "59200", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Lille", "code_postal": "59300", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Roubaix", "code_postal": "59100", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Tourcoing", "code_postal": "59200", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Villeneuve-d'Ascq", "code_postal": "59650", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Dunkerque", "code_postal": "59140", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Valenciennes", "code_postal": "59300", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Douai", "code_postal": "59500", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Wattrelos", "code_postal": "59150", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Marcq-en-Barœul", "code_postal": "59700", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Croix", "code_postal": "59170", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Lambersart", "code_postal": "59130", "departement": "59", "region": "Hauts-de-France"},
            {"nom": "Lomme", "code_postal": "59160", "departement": "59", "region": "Hauts-de-France"},
            
            # Rennes et région rennaise
            {"nom": "Rennes", "code_postal": "35000", "departement": "35", "region": "Bretagne"},
            {"nom": "Rennes", "code_postal": "35100", "departement": "35", "region": "Bretagne"},
            {"nom": "Rennes", "code_postal": "35200", "departement": "35", "region": "Bretagne"},
            {"nom": "Brest", "code_postal": "29200", "departement": "29", "region": "Bretagne"},
            {"nom": "Quimper", "code_postal": "29000", "departement": "29", "region": "Bretagne"},
            {"nom": "Lorient", "code_postal": "56100", "departement": "56", "region": "Bretagne"},
            {"nom": "Vannes", "code_postal": "56000", "departement": "56", "region": "Bretagne"},
            {"nom": "Saint-Malo", "code_postal": "35400", "departement": "35", "region": "Bretagne"},
            {"nom": "Fougères", "code_postal": "35300", "departement": "35", "region": "Bretagne"},
            {"nom": "Vitré", "code_postal": "35500", "departement": "35", "region": "Bretagne"},
            {"nom": "Redon", "code_postal": "35600", "departement": "35", "region": "Bretagne"},
            {"nom": "Dinan", "code_postal": "22100", "departement": "22", "region": "Bretagne"},
            {"nom": "Saint-Brieuc", "code_postal": "22000", "departement": "22", "region": "Bretagne"},
            {"nom": "Lannion", "code_postal": "22300", "departement": "22", "region": "Bretagne"},
            {"nom": "Guingamp", "code_postal": "22200", "departement": "22", "region": "Bretagne"},
            
            # Reims et région rémoise
            {"nom": "Reims", "code_postal": "51100", "departement": "51", "region": "Grand Est"},
            {"nom": "Reims", "code_postal": "51200", "departement": "51", "region": "Grand Est"},
            {"nom": "Troyes", "code_postal": "10000", "departement": "10", "region": "Grand Est"},
            {"nom": "Châlons-en-Champagne", "code_postal": "51000", "departement": "51", "region": "Grand Est"},
            {"nom": "Charleville-Mézières", "code_postal": "08000", "departement": "08", "region": "Grand Est"},
            {"nom": "Sedan", "code_postal": "08200", "departement": "08", "region": "Grand Est"},
            {"nom": "Épernay", "code_postal": "51200", "departement": "51", "region": "Grand Est"},
            {"nom": "Vitry-le-François", "code_postal": "51300", "departement": "51", "region": "Grand Est"},
            {"nom": "Romilly-sur-Seine", "code_postal": "10100", "departement": "10", "region": "Grand Est"},
            {"nom": "Saint-Dizier", "code_postal": "52100", "departement": "52", "region": "Grand Est"},
            {"nom": "Chaumont", "code_postal": "52000", "departement": "52", "region": "Grand Est"},
            {"nom": "Langres", "code_postal": "52200", "departement": "52", "region": "Grand Est"},
            {"nom": "Bar-sur-Aube", "code_postal": "10200", "departement": "10", "region": "Grand Est"},
            {"nom": "Nogent-sur-Seine", "code_postal": "10400", "departement": "10", "region": "Grand Est"},
            {"nom": "Sainte-Menehould", "code_postal": "51800", "departement": "51", "region": "Grand Est"},
            
            # Le Havre et région havraise
            {"nom": "Le Havre", "code_postal": "76600", "departement": "76", "region": "Normandie"},
            {"nom": "Le Havre", "code_postal": "76610", "departement": "76", "region": "Normandie"},
            {"nom": "Le Havre", "code_postal": "76620", "departement": "76", "region": "Normandie"},
            {"nom": "Rouen", "code_postal": "76000", "departement": "76", "region": "Normandie"},
            {"nom": "Caen", "code_postal": "14000", "departement": "14", "region": "Normandie"},
            {"nom": "Cherbourg-en-Cotentin", "code_postal": "50100", "departement": "50", "region": "Normandie"},
            {"nom": "Évreux", "code_postal": "27000", "departement": "27", "region": "Normandie"},
            {"nom": "Dieppe", "code_postal": "76200", "departement": "76", "region": "Normandie"},
            {"nom": "Alençon", "code_postal": "61000", "departement": "61", "region": "Normandie"},
            {"nom": "Lisieux", "code_postal": "14100", "departement": "14", "region": "Normandie"},
            {"nom": "Vire", "code_postal": "14500", "departement": "14", "region": "Normandie"},
            {"nom": "Falaise", "code_postal": "14700", "departement": "14", "region": "Normandie"},
            {"nom": "Argentan", "code_postal": "61200", "departement": "61", "region": "Normandie"},
            {"nom": "Flers", "code_postal": "61100", "departement": "61", "region": "Normandie"},
            {"nom": "Vernon", "code_postal": "27200", "departement": "27", "region": "Normandie"},
            
            # Saint-Étienne et région stéphanoise
            {"nom": "Saint-Étienne", "code_postal": "42000", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Étienne", "code_postal": "42100", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Roanne", "code_postal": "42300", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Montbrison", "code_postal": "42600", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Firminy", "code_postal": "42700", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Chamond", "code_postal": "42400", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Rive-de-Gier", "code_postal": "42800", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Le Chambon-Feugerolles", "code_postal": "42500", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "La Talaudière", "code_postal": "42350", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Sorbiers", "code_postal": "42290", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Roche-la-Molière", "code_postal": "42230", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Unieux", "code_postal": "42240", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Andrézieux-Bouthéon", "code_postal": "42160", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Villars", "code_postal": "42390", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "La Ricamarie", "code_postal": "42150", "departement": "42", "region": "Auvergne-Rhône-Alpes"},
            
            # Toulon et région toulonnaise
            {"nom": "Toulon", "code_postal": "83000", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Toulon", "code_postal": "83100", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Toulon", "code_postal": "83200", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "La Seyne-sur-Mer", "code_postal": "83500", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Hyères", "code_postal": "83400", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Fréjus", "code_postal": "83600", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Draguignan", "code_postal": "83300", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Brignoles", "code_postal": "83170", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Six-Fours-les-Plages", "code_postal": "83140", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Ollioules", "code_postal": "83190", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Le Pradet", "code_postal": "83220", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "La Garde", "code_postal": "83130", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Le Revest-les-Eaux", "code_postal": "83200", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "La Valette-du-Var", "code_postal": "83160", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Solliès-Pont", "code_postal": "83210", "departement": "83", "region": "Provence-Alpes-Côte d'Azur"},
            
            # Grenoble et région grenobloise
            {"nom": "Grenoble", "code_postal": "38000", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Grenoble", "code_postal": "38100", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Martin-d'Hères", "code_postal": "38400", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Échirolles", "code_postal": "38130", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Vienne", "code_postal": "38200", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Bourgoin-Jallieu", "code_postal": "38300", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Voiron", "code_postal": "38500", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Meylan", "code_postal": "38240", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Fontaine", "code_postal": "38600", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Seyssinet-Pariset", "code_postal": "38170", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Sassenage", "code_postal": "38360", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Crolles", "code_postal": "38920", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Le Pont-de-Claix", "code_postal": "38800", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Égrève", "code_postal": "38120", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Gières", "code_postal": "38610", "departement": "38", "region": "Auvergne-Rhône-Alpes"},
            
            # Dijon et région dijonnaise
            {"nom": "Dijon", "code_postal": "21000", "departement": "21", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Dijon", "code_postal": "21100", "departement": "21", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Chalon-sur-Saône", "code_postal": "71100", "departement": "71", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Nevers", "code_postal": "58000", "departement": "58", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Auxerre", "code_postal": "89000", "departement": "89", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Mâcon", "code_postal": "71000", "departement": "71", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Sens", "code_postal": "89100", "departement": "89", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Le Creusot", "code_postal": "71200", "departement": "71", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Montceau-les-Mines", "code_postal": "71300", "departement": "71", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Joigny", "code_postal": "89300", "departement": "89", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Paray-le-Monial", "code_postal": "71600", "departement": "71", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Cosne-Cours-sur-Loire", "code_postal": "58200", "departement": "58", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Decize", "code_postal": "58300", "departement": "58", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Château-Chinon", "code_postal": "58120", "departement": "58", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Clamecy", "code_postal": "58500", "departement": "58", "region": "Bourgogne-Franche-Comté"},
            
            # Angers et région angevine
            {"nom": "Angers", "code_postal": "49000", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Angers", "code_postal": "49100", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Cholet", "code_postal": "49300", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Saumur", "code_postal": "49400", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Sèvremoine", "code_postal": "49230", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Trélazé", "code_postal": "49800", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Avrillé", "code_postal": "49240", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Beaucouzé", "code_postal": "49070", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Mazé-Milon", "code_postal": "49630", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Longué-Jumelles", "code_postal": "49160", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Doué-la-Fontaine", "code_postal": "49700", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Chemillé-en-Anjou", "code_postal": "49120", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Segré-en-Anjou Bleu", "code_postal": "49500", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Baugé-en-Anjou", "code_postal": "49150", "departement": "49", "region": "Pays de la Loire"},
            {"nom": "Chalonnes-sur-Loire", "code_postal": "49290", "departement": "49", "region": "Pays de la Loire"},
            
            # Nîmes et région nîmoise
            {"nom": "Nîmes", "code_postal": "30000", "departement": "30", "region": "Occitanie"},
            {"nom": "Nîmes", "code_postal": "30900", "departement": "30", "region": "Occitanie"},
            {"nom": "Alès", "code_postal": "30100", "departement": "30", "region": "Occitanie"},
            {"nom": "Bagnols-sur-Cèze", "code_postal": "30200", "departement": "30", "region": "Occitanie"},
            {"nom": "Beaucaire", "code_postal": "30300", "departement": "30", "region": "Occitanie"},
            {"nom": "Uzès", "code_postal": "30700", "departement": "30", "region": "Occitanie"},
            {"nom": "Villeneuve-lès-Avignon", "code_postal": "30400", "departement": "30", "region": "Occitanie"},
            {"nom": "Pont-Saint-Esprit", "code_postal": "30130", "departement": "30", "region": "Occitanie"},
            {"nom": "Saint-Gilles", "code_postal": "30800", "departement": "30", "region": "Occitanie"},
            {"nom": "Vauvert", "code_postal": "30600", "departement": "30", "region": "Occitanie"},
            {"nom": "Marguerittes", "code_postal": "30320", "departement": "30", "region": "Occitanie"},
            {"nom": "Laudun-l'Ardoise", "code_postal": "30290", "departement": "30", "region": "Occitanie"},
            {"nom": "Rochefort-du-Gard", "code_postal": "30650", "departement": "30", "region": "Occitanie"},
            {"nom": "Saint-Laurent-des-Arbres", "code_postal": "30126", "departement": "30", "region": "Occitanie"},
            {"nom": "Fourques", "code_postal": "30300", "departement": "30", "region": "Occitanie"},
            
            # Villeurbanne et région villeurbannaise
            {"nom": "Villeurbanne", "code_postal": "69100", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Villeurbanne", "code_postal": "69120", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Vénissieux", "code_postal": "69200", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Saint-Priest", "code_postal": "69800", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Caluire-et-Cuire", "code_postal": "69300", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Vaulx-en-Velin", "code_postal": "69120", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Bron", "code_postal": "69500", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Décines-Charpieu", "code_postal": "69150", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Oullins", "code_postal": "69600", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Pierre-Bénite", "code_postal": "69310", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Rillieux-la-Pape", "code_postal": "69140", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Meyzieu", "code_postal": "69330", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Tassin-la-Demi-Lune", "code_postal": "69160", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Écully", "code_postal": "69130", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Champagne-au-Mont-d'Or", "code_postal": "69410", "departement": "69", "region": "Auvergne-Rhône-Alpes"},
            
            # Saint-Denis et région saint-dionysienne
            {"nom": "Saint-Denis", "code_postal": "93200", "departement": "93", "region": "Île-de-France"},
            {"nom": "Saint-Denis", "code_postal": "93210", "departement": "93", "region": "Île-de-France"},
            {"nom": "Aubervilliers", "code_postal": "93300", "departement": "93", "region": "Île-de-France"},
            {"nom": "Aulnay-sous-Bois", "code_postal": "93600", "departement": "93", "region": "Île-de-France"},
            {"nom": "Bondy", "code_postal": "93140", "departement": "93", "region": "Île-de-France"},
            {"nom": "Drancy", "code_postal": "93700", "departement": "93", "region": "Île-de-France"},
            {"nom": "Épinay-sur-Seine", "code_postal": "93800", "departement": "93", "region": "Île-de-France"},
            {"nom": "La Courneuve", "code_postal": "93120", "departement": "93", "region": "Île-de-France"},
            {"nom": "Le Blanc-Mesnil", "code_postal": "93150", "departement": "93", "region": "Île-de-France"},
            {"nom": "Le Bourget", "code_postal": "93350", "departement": "93", "region": "Île-de-France"},
            {"nom": "Le Raincy", "code_postal": "93340", "departement": "93", "region": "Île-de-France"},
            {"nom": "Les Lilas", "code_postal": "93260", "departement": "93", "region": "Île-de-France"},
            {"nom": "Livry-Gargan", "code_postal": "93190", "departement": "93", "region": "Île-de-France"},
            {"nom": "Montreuil", "code_postal": "93100", "departement": "93", "region": "Île-de-France"},
            {"nom": "Neuilly-sur-Marne", "code_postal": "93330", "departement": "93", "region": "Île-de-France"},
            
            {"nom": "Le Mans", "code_postal": "72000", "departement": "72", "region": "Pays de la Loire"},
            {"nom": "Le Mans", "code_postal": "72100", "departement": "72", "region": "Pays de la Loire"},
            
            {"nom": "Aix-en-Provence", "code_postal": "13100", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            {"nom": "Aix-en-Provence", "code_postal": "13290", "departement": "13", "region": "Provence-Alpes-Côte d'Azur"},
            
            {"nom": "Clermont-Ferrand", "code_postal": "63000", "departement": "63", "region": "Auvergne-Rhône-Alpes"},
            {"nom": "Clermont-Ferrand", "code_postal": "63100", "departement": "63", "region": "Auvergne-Rhône-Alpes"},
            
            {"nom": "Brest", "code_postal": "29200", "departement": "29", "region": "Bretagne"},
            {"nom": "Brest", "code_postal": "29210", "departement": "29", "region": "Bretagne"},
            
            {"nom": "Tours", "code_postal": "37000", "departement": "37", "region": "Centre-Val de Loire"},
            {"nom": "Tours", "code_postal": "37100", "departement": "37", "region": "Centre-Val de Loire"},
            
            {"nom": "Limoges", "code_postal": "87000", "departement": "87", "region": "Nouvelle-Aquitaine"},
            {"nom": "Limoges", "code_postal": "87100", "departement": "87", "region": "Nouvelle-Aquitaine"},
            
            {"nom": "Amiens", "code_postal": "80000", "departement": "80", "region": "Hauts-de-France"},
            {"nom": "Amiens", "code_postal": "80080", "departement": "80", "region": "Hauts-de-France"},
            
            {"nom": "Perpignan", "code_postal": "66000", "departement": "66", "region": "Occitanie"},
            {"nom": "Perpignan", "code_postal": "66100", "departement": "66", "region": "Occitanie"},
            
            {"nom": "Metz", "code_postal": "57000", "departement": "57", "region": "Grand Est"},
            {"nom": "Metz", "code_postal": "57050", "departement": "57", "region": "Grand Est"},
            
            {"nom": "Besançon", "code_postal": "25000", "departement": "25", "region": "Bourgogne-Franche-Comté"},
            {"nom": "Besançon", "code_postal": "25010", "departement": "25", "region": "Bourgogne-Franche-Comté"},
            
            {"nom": "Orléans", "code_postal": "45000", "departement": "45", "region": "Centre-Val de Loire"},
            {"nom": "Orléans", "code_postal": "45100", "departement": "45", "region": "Centre-Val de Loire"},
            
            {"nom": "Mulhouse", "code_postal": "68100", "departement": "68", "region": "Grand Est"},
            {"nom": "Mulhouse", "code_postal": "68200", "departement": "68", "region": "Grand Est"},
            
            {"nom": "Rouen", "code_postal": "76000", "departement": "76", "region": "Normandie"},
            {"nom": "Rouen", "code_postal": "76100", "departement": "76", "region": "Normandie"},
            
            {"nom": "Caen", "code_postal": "14000", "departement": "14", "region": "Normandie"},
            {"nom": "Caen", "code_postal": "14100", "departement": "14", "region": "Normandie"},
            
            {"nom": "Nancy", "code_postal": "54000", "departement": "54", "region": "Grand Est"},
            {"nom": "Nancy", "code_postal": "54100", "departement": "54", "region": "Grand Est"},
            
            {"nom": "Saint-Denis (La Réunion)", "code_postal": "97400", "departement": "974", "region": "La Réunion"},
            {"nom": "Saint-Pierre (La Réunion)", "code_postal": "97410", "departement": "974", "region": "La Réunion"},
            
            {"nom": "Fort-de-France", "code_postal": "97200", "departement": "972", "region": "Martinique"},
            {"nom": "Pointe-à-Pitre", "code_postal": "97100", "departement": "971", "region": "Guadeloupe"},
        ]
        
        # Filtrer les suggestions
        suggestions = []
        query_lower = query.lower()
        
        for ville in villes_france:
            # Recherche par nom de ville
            if query_lower in ville["nom"].lower():
                suggestions.append({
                    "value": f"{ville['nom']} ({ville['code_postal']})",
                    "label": f"{ville['nom']} - {ville['code_postal']}",
                    "nom": ville["nom"],
                    "code_postal": ville["code_postal"],
                    "departement": ville["departement"],
                    "region": ville["region"],
                    "type": "ville"
                })
            # Recherche par code postal
            elif query in ville["code_postal"]:
                suggestions.append({
                    "value": f"{ville['nom']} ({ville['code_postal']})",
                    "label": f"{ville['code_postal']} - {ville['nom']}",
                    "nom": ville["nom"],
                    "code_postal": ville["code_postal"],
                    "departement": ville["departement"],
                    "region": ville["region"],
                    "type": "code_postal"
                })
        
        # Limiter le nombre de résultats
        suggestions = suggestions[:limit]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'autocomplétion des lieux: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'autocomplétion: {str(e)}'
        })

# La route API véhicules/types est maintenant dans le blueprint api_vehicules_bp

# Routes /parametrage_impact et /parametrage_systeme migrées vers le blueprint parametrage_bp

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

# La route API invitations est maintenant dans le blueprint api_invitations_bp
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
            
            # Envoyer l'email d'invitation
            try:
                email_envoye = envoyer_email_invitation(invitation)
                if email_envoye:
                    logger.info(f"📧 Email d'invitation envoyé avec succès à {email}")
                else:
                    logger.warning(f"⚠️ Échec de l'envoi de l'email d'invitation à {email}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'envoi de l'email d'invitation à {email}: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': f'Invitation envoyée à {email}',
                'invitation_id': invitation.id
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'invitation: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

# La route API invitations resend est maintenant dans le blueprint api_invitations_bp
    try:
        invitation = Invitation.query.get(invitation_id)
        
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        if invitation.statut == 'acceptee':
            return jsonify({'success': False, 'error': 'Cette invitation a déjà été acceptée'}), 400
        
        # Mettre à jour la date d'invitation
        invitation.date_invitation = datetime.utcnow()
        db.session.commit()
        
        # Renvoyer l'email d'invitation
        try:
            email_envoye = envoyer_email_invitation(invitation)
            if email_envoye:
                logger.info(f"📧 Email d'invitation relancé avec succès à {invitation.email}")
                return jsonify({
                    'success': True,
                    'message': f'Invitation relancée à {invitation.email}'
                })
            else:
                logger.warning(f"⚠️ Échec de l'envoi de l'email d'invitation relancé à {invitation.email}")
                return jsonify({
                    'success': False,
                    'error': 'Échec de l\'envoi de l\'email'
                }), 500
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi de l'email d'invitation relancé à {invitation.email}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Erreur lors de l\'envoi: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors de la relance de l'invitation {invitation_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clients/<client_id>/invitation-status')
def get_client_invitation_status(client_id):
    """Récupérer le statut d'invitation d'un client"""
    try:
        # Récupérer le client
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client non trouvé'}), 404
        
        # Chercher une invitation pour cet email
        invitation = Invitation.query.filter_by(email=client.email).first()
        
        if invitation:
            return jsonify({
                'success': True,
                'has_invitation': True,
                'invitation': {
                    'id': invitation.id,
                    'statut': invitation.statut,
                    'date_invitation': invitation.date_invitation.strftime('%d/%m/%Y %H:%M') if invitation.date_invitation else None,
                    'date_reponse': invitation.date_reponse.strftime('%d/%m/%Y %H:%M') if invitation.date_reponse else None
                }
            })
        else:
            return jsonify({
                'success': True,
                'has_invitation': False
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut d'invitation pour le client {client_id}: {str(e)}")
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
            
            mot_de_passe = data.get('mot_de_passe')
            if not mot_de_passe:
                return jsonify({'success': False, 'error': 'Mot de passe requis'}), 400
            
            if len(mot_de_passe) < 6:
                return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
            
            # Vérifier si l'utilisateur existe déjà
            existing_user = User.query.filter_by(email=invitation.email).first()
            if existing_user:
                return jsonify({'success': False, 'error': 'Un compte existe déjà avec cet email'}), 400
            
            # Créer le compte utilisateur
            nouveau_user = User(
                email=invitation.email,
                mot_de_passe=mot_de_passe,
                nom=nom_utilisateur,
                nom_entreprise=nom_entreprise,
                type_utilisateur='client',
                statut='actif'
            )
            
            db.session.add(nouveau_user)
            
            # Mettre à jour l'invitation
            invitation.statut = 'acceptee'
            invitation.nom_entreprise = nom_entreprise
            invitation.nom_utilisateur = nom_utilisateur
            invitation.date_reponse = datetime.utcnow()
            
            logger.info(f"✅ Invitation acceptée par {nom_utilisateur} ({nom_entreprise}) - Compte créé")
            
        elif action == 'refuser':
            invitation.statut = 'refusee'
            invitation.date_reponse = datetime.utcnow()
            logger.info(f"❌ Invitation refusée par {invitation.email}")
        
        db.session.commit()
        
        if action == 'accepter':
            return jsonify({
                'success': True,
                'message': f'Invitation acceptée avec succès. Votre compte a été créé.',
                'identifiants': {
                    'email': invitation.email,
                    'mot_de_passe': mot_de_passe
                }
            })
        else:
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

# === FONCTIONS UTILITAIRES ===

def getTimeElapsed(date):
    """Calculer le temps écoulé depuis une date"""
    if not date:
        return "N/A"
    
    now = datetime.utcnow()
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    
    diff = now - date
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 jour"
        else:
            return f"{diff.days} jours"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        if hours == 1:
            return "1 heure"
        else:
            return f"{hours} heures"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        if minutes == 1:
            return "1 minute"
        else:
            return f"{minutes} minutes"
    else:
        return "À l'instant"

# === ROUTES D'ADMINISTRATION DES CLIENTS ===

@app.route('/admin/clients')
def admin_clients_list():
    """Page d'administration - Liste des clients"""
    try:
        # Récupérer tous les clients
        clients = Client.query.all()
        
        # Récupérer les utilisateurs clients
        users_clients = User.query.filter_by(type_utilisateur='client').all()
        
        # Créer un dictionnaire pour lier les clients aux utilisateurs
        clients_data = []
        for client in clients:
            user = next((u for u in users_clients if u.email == client.email), None)
            clients_data.append({
                'client': client,
                'user': user,
                'has_account': user is not None
            })
        
        return render_template('admin_clients_list.html', clients_data=clients_data)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de la liste des clients admin: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/admin/invitations')
def admin_invitations():
    """Page d'administration - Gestion des invitations"""
    try:
        # Récupérer toutes les invitations
        invitations = Invitation.query.order_by(Invitation.created_at.desc()).all()
        
        # Statistiques
        stats = {
            'total': len(invitations),
            'en_attente': len([i for i in invitations if i.statut == 'en_attente']),
            'acceptees': len([i for i in invitations if i.statut == 'acceptee']),
            'refusees': len([i for i in invitations if i.statut == 'refusee']),
            'expirees': len([i for i in invitations if i.statut == 'expiree'])
        }
        
        return render_template('admin_invitations.html', invitations=invitations, stats=stats)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des invitations admin: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/admin/clients/pending')
def admin_clients_pending():
    """Page d'administration - Clients en attente d'acceptation"""
    try:
        # Récupérer les invitations en attente
        invitations_pending = Invitation.query.filter_by(statut='en_attente').order_by(Invitation.created_at.desc()).all()
        
        # Récupérer les invitations refusées (pour relancer)
        invitations_refused = Invitation.query.filter_by(statut='refusee').order_by(Invitation.created_at.desc()).all()
        
        return render_template('admin_clients_pending.html', 
                             invitations_pending=invitations_pending,
                             invitations_refused=invitations_refused,
                             getTimeElapsed=getTimeElapsed)
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des clients en attente: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# === API ENDPOINTS POUR L'ADMINISTRATION ===

@app.route('/api/invitations/<int:invitation_id>/resend', methods=['POST'])
def resend_invitation_admin(invitation_id):
    """Relancer une invitation"""
    try:
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        # Générer un nouveau token
        invitation.token = secrets.token_urlsafe(32)
        invitation.date_invitation = datetime.utcnow()
        invitation.statut = 'en_attente'
        
        # Envoyer l'email
        try:
            send_invitation_email(invitation.email, invitation.token, invitation.message_personnalise)
            db.session.commit()
            logger.info(f"✅ Invitation relancée pour {invitation.email}")
            return jsonify({
                'success': True,
                'message': f'Invitation relancée avec succès à {invitation.email}'
            })
        except Exception as email_error:
            logger.error(f"Erreur lors de l'envoi de l'email: {str(email_error)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Erreur lors de l\'envoi de l\'email: {str(email_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors de la relance de l'invitation {invitation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
def delete_invitation(invitation_id):
    """Supprimer une invitation"""
    try:
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation non trouvée'}), 404
        
        email = invitation.email
        db.session.delete(invitation)
        db.session.commit()
        
        logger.info(f"✅ Invitation supprimée pour {email}")
        return jsonify({
            'success': True,
            'message': f'Invitation supprimée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'invitation {invitation_id}: {str(e)}")
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
                'created_at': client.created_at.isoformat() if client.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du client {client_id}: {str(e)}")
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
