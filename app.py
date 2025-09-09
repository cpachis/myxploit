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
    clients_bp, api_bp, api_vehicules_bp, api_energies_bp, api_transports_bp, api_clients_bp, api_invitations_bp, parametrage_bp, invitations_bp,
    transporteurs_bp, invitations_extended_bp, debug_bp, utils_bp, import_csv_bp, expeditions_bp, customer_bp, transport_management_bp
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
app.register_blueprint(transporteurs_bp)
app.register_blueprint(invitations_extended_bp)
app.register_blueprint(debug_bp, url_prefix='/debug')
app.register_blueprint(utils_bp)
app.register_blueprint(import_csv_bp)
app.register_blueprint(expeditions_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(transport_management_bp)

# Initialisation de la base de données avec migration automatique
with app.app_context():
    try:
        db.create_all()
        
        # Vérifier et ajouter la colonne vehicule_dedie si elle n'existe pas
        try:
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' 
                AND column_name = 'vehicule_dedie'
            """))
            
            if not result.fetchone():
                logger.info("🔧 Ajout de la colonne vehicule_dedie...")
                db.session.execute(text("""
                    ALTER TABLE transports 
                    ADD COLUMN vehicule_dedie BOOLEAN DEFAULT FALSE
                """))
                db.session.commit()
                logger.info("✅ Colonne vehicule_dedie ajoutée avec succès")
            else:
                logger.info("✅ Colonne vehicule_dedie existe déjà")
                
        except Exception as migration_error:
            logger.warning(f"⚠️ Erreur lors de la vérification/ajout de vehicule_dedie: {str(migration_error)}")
            # Ne pas faire échouer l'initialisation pour cette erreur
        
        logger.info("✅ Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base de données: {str(e)}")

# Configuration du login manager - DÉSACTIVÉ POUR LE DÉVELOPPEMENT
# login_manager.login_view = 'auth.login'
# login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données - MODE DÉVELOPPEMENT"""
    # Pour le développement, retourner un utilisateur fictif
    if app.config.get('DEBUG', False):
        class DevUser:
            def __init__(self):
                self.id = 1
                self.email = "dev@myxploit.com"
                self.type_utilisateur = "admin"
                self.statut = "actif"
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
            
            def get_id(self):
                return str(self.id)
            
            def check_password(self, password):
                return True  # Accepter n'importe quel mot de passe en dev
        
        return DevUser()
    
    # Mode production - charger depuis la base de données
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'utilisateur {user_id}: {str(e)}")
        return None

# ============================================================================
# ROUTE DE DÉVELOPPEMENT - CONNEXION AUTOMATIQUE
# ============================================================================

@app.route('/dev-login')
def dev_login():
    """Route de développement pour se connecter automatiquement"""
    if app.config.get('DEBUG', False):
        from flask_login import login_user
        
        class DevUser:
            def __init__(self):
                self.id = 1
                self.email = "dev@myxploit.com"
                self.type_utilisateur = "admin"
                self.statut = "actif"
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
            
            def get_id(self):
                return str(self.id)
        
        dev_user = DevUser()
        login_user(dev_user)
        flash('Connexion automatique en mode développement', 'success')
        return redirect(url_for('main.homepage'))
    else:
        flash('Cette route n\'est disponible qu\'en mode développement', 'danger')
        return redirect(url_for('main.homepage'))

# ============================================================================
# ROUTES MIGRÉES VERS LES BLUEPRINTS
# ============================================================================
# Toutes les routes ont été migrées vers leurs blueprints respectifs :
# - Routes d'import CSV → import_csv_bp
# - Routes d'authentification → auth_bp  
# - Routes de debug et santé → debug_bp
# - Routes transporteurs → transporteurs_bp
# - Routes transports → api_transports_bp
# - Routes invitations → invitations_bp
# - Routes admin → admin_bp
# - Routes clients → clients_bp
# ============================================================================







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