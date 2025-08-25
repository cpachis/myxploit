import json
import os
from flask_login import UserMixin

# Emplacement du fichier users.json
data_dir = 'data'
users_file = os.path.join(data_dir, 'users.json')


def load_users():
    """Charge les utilisateurs depuis data/users.json"""
    if not os.path.exists(users_file):
        return {}
    with open(users_file, encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


class User(UserMixin):
    """Modèle utilisateur pour Flask-Login"""
    def __init__(self, username):
        self.id = username

    @staticmethod
    def validate(username, password):
        users = load_users()
        user_entry = users.get(username)
        if not user_entry:
            return None
        # Pour un prototype, mots de passe en clair. En prod, utilisez hashing.
        if user_entry.get('password') == password:
            return User(username)
        return None

    @staticmethod
    def get(user_id):
        users = load_users()
        if user_id in users:
            return User(user_id)
        return None


class Transport:
    """Modèle de transport simplifié"""
    
    def __init__(self, ref, client, ville_depart, ville_arrivee, distance_km, energie, poids_tonnes, date):
        self.ref = ref
        self.client = client
        self.ville_depart = ville_depart
        self.ville_arrivee = ville_arrivee
        self.distance_km = distance_km
        self.energie = energie
        self.poids_tonnes = poids_tonnes
        self.date = date
        self.emis_kg = None
        self.emis_tkm = None
    
    def calculer_emissions(self, facteur_energie):
        """Calcule les émissions CO2 en fonction de l'énergie et de la distance"""
        if self.distance_km and self.poids_tonnes and facteur_energie:
            # Émissions totales = distance × poids × facteur d'émission de l'énergie
            self.emis_kg = self.distance_km * self.poids_tonnes * facteur_energie
            # Émissions par tonne-kilomètre
            self.emis_tkm = facteur_energie
            return self.emis_kg
        return 0
    
    def to_dict(self):
        """Convertit le transport en dictionnaire"""
        return {
            'ref': self.ref,
            'client': self.client,
            'ville_depart': self.ville_depart,
            'ville_arrivee': self.ville_arrivee,
            'distance_km': self.distance_km,
            'energie': self.energie,
            'poids_tonnes': self.poids_tonnes,
            'date': self.date,
            'emis_kg': self.emis_kg,
            'emis_tkm': self.emis_tkm
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crée un transport à partir d'un dictionnaire"""
        transport = cls(
            ref=data.get('ref', ''),
            client=data.get('client', ''),
            ville_depart=data.get('ville_depart', ''),
            ville_arrivee=data.get('ville_arrivee', ''),
            distance_km=data.get('distance_km', 0),
            energie=data.get('energie', ''),
            poids_tonnes=data.get('poids_tonnes', 0),
            date=data.get('date', '')
        )
        transport.emis_kg = data.get('emis_kg')
        transport.emis_tkm = data.get('emis_tkm')
        return transport
