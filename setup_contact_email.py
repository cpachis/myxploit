#!/usr/bin/env python3
"""
Script pour configurer contact@myxploit.com comme adresse expéditeur
"""

import os
from pathlib import Path

def configurer_contact_email():
    """Configurer contact@myxploit.com"""
    print("📧 Configuration de contact@myxploit.com")
    print("=" * 50)
    
    print("\n🎯 Choisissez votre service email :")
    print("1. SendGrid (Recommandé pour contact@myxploit.com)")
    print("2. Gmail (si vous avez configuré l'alias)")
    print("3. Mailgun")
    print("4. Configuration manuelle")
    
    choix = input("\nVotre choix (1-4) : ")
    
    if choix == "1":
        return configurer_sendgrid()
    elif choix == "2":
        return configurer_gmail()
    elif choix == "3":
        return configurer_mailgun()
    elif choix == "4":
        return configurer_manuel()
    else:
        print("❌ Choix invalide")
        return False

def configurer_sendgrid():
    """Configuration SendGrid pour contact@myxploit.com"""
    print("\n🔧 Configuration SendGrid")
    print("-" * 30)
    print("📋 Étapes :")
    print("1. Aller sur https://sendgrid.com/")
    print("2. Créer un compte gratuit (100 emails/jour)")
    print("3. Vérifier votre email")
    print("4. Settings → API Keys → Create API Key")
    print("5. Copier la clé API")
    print()
    
    api_key = input("🔑 Clé API SendGrid : ")
    
    config = {
        'SMTP_SERVER': 'smtp.sendgrid.net',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': 'contact@myxploit.com',
        'EMAIL_PASSWORD': api_key
    }
    
    return sauvegarder_config(config, "SendGrid")

def configurer_gmail():
    """Configuration Gmail pour contact@myxploit.com"""
    print("\n🔧 Configuration Gmail")
    print("-" * 30)
    print("📋 Prérequis :")
    print("- Avoir configuré contact@myxploit.com comme alias Gmail")
    print("- Ou utiliser votre compte Gmail principal")
    print()
    
    email_gmail = input("📧 Votre email Gmail principal : ")
    password = input("🔑 Mot de passe d'application (16 caractères) : ")
    
    config = {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': 'contact@myxploit.com',
        'EMAIL_PASSWORD': password
    }
    
    return sauvegarder_config(config, "Gmail")

def configurer_mailgun():
    """Configuration Mailgun pour contact@myxploit.com"""
    print("\n🔧 Configuration Mailgun")
    print("-" * 30)
    print("📋 Étapes :")
    print("1. Aller sur https://www.mailgun.com/")
    print("2. Créer un compte gratuit (5000 emails/mois)")
    print("3. Vérifier votre domaine ou utiliser sandbox")
    print("4. Récupérer la clé API")
    print()
    
    api_key = input("🔑 Clé API Mailgun : ")
    
    config = {
        'SMTP_SERVER': 'smtp.mailgun.org',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': 'contact@myxploit.com',
        'EMAIL_PASSWORD': api_key
    }
    
    return sauvegarder_config(config, "Mailgun")

def configurer_manuel():
    """Configuration manuelle"""
    print("\n🔧 Configuration manuelle")
    print("-" * 30)
    
    smtp_server = input("🌐 Serveur SMTP : ")
    smtp_port = input("🔌 Port SMTP : ")
    password = input("🔑 Mot de passe/Clé API : ")
    
    config = {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'EMAIL_EMETTEUR': 'contact@myxploit.com',
        'EMAIL_PASSWORD': password
    }
    
    return sauvegarder_config(config, "Manuel")

def sauvegarder_config(config, service):
    """Sauvegarder la configuration"""
    print(f"\n💾 Sauvegarde de la configuration {service}...")
    
    # Créer le contenu du fichier .env
    env_content = f"""# Configuration email MyXploit - contact@myxploit.com
SMTP_SERVER={config['SMTP_SERVER']}
SMTP_PORT={config['SMTP_PORT']}
EMAIL_EMETTEUR={config['EMAIL_EMETTEUR']}
EMAIL_PASSWORD={config['EMAIL_PASSWORD']}

# Autres variables
SECRET_KEY=votre-cle-secrete-tres-longue
DATABASE_URL=sqlite:///instance/myxploit_dev.db
"""
    
    # Afficher le contenu à copier
    print(f"\n📄 Créez un fichier .env dans le dossier myxploit/ avec ce contenu :")
    print("-" * 60)
    print(env_content)
    print("-" * 60)
    
    # Afficher les variables pour Render
    print(f"\n🌐 Pour déployer sur Render, ajoutez ces variables d'environnement :")
    print("-" * 50)
    for key, value in config.items():
        print(f"{key}={value}")
    print("-" * 50)
    
    print(f"\n✅ Configuration prête pour contact@myxploit.com avec {service}")
    return True

if __name__ == "__main__":
    configurer_contact_email()
