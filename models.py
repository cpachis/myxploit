from datetime import datetime

# db sera importé depuis app.py pour éviter les conflits SQLAlchemy

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
