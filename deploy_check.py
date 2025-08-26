#!/usr/bin/env python3
"""
Script de vérification de la configuration avant déploiement
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement locales
load_dotenv('env.local')
load_dotenv('.env')

from config import get_config

def check_configuration():
    """Vérifie la configuration de l'application"""
    print("🔍 Vérification de la configuration...")
    
    # Vérifier les variables d'environnement critiques
    critical_vars = ['SECRET_KEY', 'FLASK_ENV']
    missing_vars = []
    
    for var in critical_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("💡 Créez un fichier env.local avec ces variables pour les tests locaux")
        return False
    
    # Vérifier la configuration
    try:
        config = get_config()
        print(f"✅ Configuration chargée: {config.__class__.__name__}")
        
        # Vérifier la base de données
        if hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
            db_uri = config.SQLALCHEMY_DATABASE_URI
            if db_uri:
                print(f"✅ URI de base de données configurée: {db_uri[:50]}...")
            else:
                print("⚠️  URI de base de données non configurée (normal en local)")
        
        # Vérifier le mode debug
        debug_mode = getattr(config, 'DEBUG', None)
        if debug_mode is False:
            print("✅ Mode production activé (DEBUG=False)")
        else:
            print(f"⚠️  Mode debug: {debug_mode}")
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration: {e}")
        return False
    
    print("✅ Configuration vérifiée avec succès!")
    return True

def check_dependencies():
    """Vérifie les dépendances requises"""
    print("\n📦 Vérification des dépendances...")
    
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_migrate', 
        'flask_cors', 'gunicorn'
    ]
    
    # psycopg2 est optionnel en local mais requis en production
    optional_packages = ['psycopg2']
    
    missing_packages = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} (optionnel)")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (optionnel - requis en production)")
    
    if missing_packages:
        print(f"\n❌ Packages requis manquants: {', '.join(missing_packages)}")
        print("Installez-les avec: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Packages optionnels manquants: {', '.join(missing_optional)}")
        print("Ces packages seront installés automatiquement sur Render")
    
    print("✅ Toutes les dépendances requises sont installées!")
    return True

def main():
    """Fonction principale"""
    print("🚀 Vérification de la configuration de déploiement Myxploit\n")
    
    config_ok = check_configuration()
    deps_ok = check_dependencies()
    
    print("\n" + "="*50)
    
    if config_ok and deps_ok:
        print("🎉 Configuration prête pour le déploiement!")
        print("\nProchaines étapes:")
        print("1. Poussez votre code sur GitHub")
        print("2. Connectez votre repo à Render")
        print("3. Configurez les variables d'environnement")
        print("4. Déployez!")
        return 0
    else:
        print("❌ Problèmes détectés. Corrigez-les avant le déploiement.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
