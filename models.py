"""
Modèles de données pour l'application MyXploit
Ce fichier centralise tous les modèles pour éviter les problèmes d'import circulaire
"""

from datetime import datetime

# Les modèles seront définis ici et importés depuis app.py
# pour éviter les problèmes d'ordre d'importation

def create_models(db):
    """Crée tous les modèles avec la base de données fournie"""
    
    class Transport(db.Model):
        """Modèle pour les transports"""
        __tablename__ = 'transports'
        
        id = db.Column(db.Integer, primary_key=True)
        ref = db.Column(db.String(50), unique=True, nullable=False)
        date = db.Column(db.Date, nullable=False)
        lieu_collecte = db.Column(db.String(200), nullable=False)
        lieu_livraison = db.Column(db.String(200), nullable=False)
        poids_tonnes = db.Column(db.Float, nullable=False)
        type_transport = db.Column(db.String(50), default='direct')  # direct ou indirect
        distance_km = db.Column(db.Float, default=0.0)
        emis_kg = db.Column(db.Float, default=0.0)
        emis_tkm = db.Column(db.Float, default=0.0)
        
        # Champs optionnels pour les calculs avancés
        niveau_calcul = db.Column(db.String(50))
        type_vehicule = db.Column(db.String(50))
        energie = db.Column(db.String(50))
        conso_vehicule = db.Column(db.Float)
        client = db.Column(db.String(100))
        transporteur = db.Column(db.String(100))
        description = db.Column(db.Text)
        
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

    class User(db.Model):
        """Modèle pour les utilisateurs (clients et administrateurs)"""
        __tablename__ = 'users'
        
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        mot_de_passe = db.Column(db.String(255), nullable=False)
        nom = db.Column(db.String(100), nullable=False)
        nom_entreprise = db.Column(db.String(100))
        type_utilisateur = db.Column(db.String(20), default='client')  # 'client' ou 'admin'
        statut = db.Column(db.String(20), default='actif')
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def check_password(self, password):
            """Vérifier le mot de passe (simple comparaison pour l'instant)"""
            return self.mot_de_passe == password
        
        def get_id(self):
            """Méthode requise par Flask-Login"""
            return str(self.id)

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

    # Retourner un dictionnaire avec tous les modèles
    return {
        'Transport': Transport,
        'Vehicule': Vehicule,
        'Energie': Energie,
        'Invitation': Invitation,
        'User': User,
        'Client': Client,
        'Transporteur': Transporteur
    }