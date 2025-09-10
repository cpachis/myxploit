"""
Blueprintntntnts pour l'application MyXploit
"""

from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from .transports import transports_bp
from .clients import clients_bp
from .api import api_bp
from .api_vehicules import api_vehicules_bp
from .api_energies import api_energies_bp
from .api_transports import api_transports_bp
from .api_clients import api_clients_bp
from .api_invitations import api_invitations_bp
from .parametrage import parametrage_bp
from .invitations import invitations_bp
from .transporteurs import transporteurs_bp
from .invitations_extended import invitations_extended_bp
from .debug import debug_bp
from .utils import utils_bp
from .import_csv import import_csv_bp
from .expeditions import expeditions_bp
from .customer import customer_bp
from .transport_management import transport_management_bp

__all__ = [
    'auth_bp', 'main_bp', 'admin_bp', 'transports_bp', 
    'clients_bp', 'api_bp', 'api_vehicules_bp', 'api_energies_bp', 'api_transports_bp', 'api_clients_bp', 'api_invitations_bp', 'parametrage_bp', 'invitations_bp',
    'transporteurs_bp', 'invitations_extended_bp', 'debug_bp', 'utils_bp', 'import_csv_bp', 'expeditions_bp', 'customer_bp', 'transport_management_bp'
] 