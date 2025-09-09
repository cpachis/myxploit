#!/usr/bin/env python3
"""
Script interactif pour configurer l'envoi d'emails MyXploit
"""

import os
import sys
from pathlib import Path

def afficher_menu():
    """Afficher le menu de configuration"""
    print("\n" + "="*60)
    print("📧 CONFIGURATION EMAIL MYXPLOIT")
    print("="*60)
    print("1. Gmail (Gratuit - 500 emails/jour)")
    print("2. SendGrid (Gratuit - 100 emails/jour)")
    print("3. Mailgun (Gratuit - 5000 emails/mois)")
    print("4. Configuration manuelle")
    print("5. Tester la configuration actuelle")
    print("6. Quitter")
    print("="*60)

def configurer_gmail():
    """Configuration Gmail"""
    print("\n🔧 Configuration Gmail")
    print("-" * 30)
    print("📋 Étapes à suivre :")
    print("1. Aller sur https://myaccount.google.com/")
    print("2. Sécurité → Validation en 2 étapes (doit être activée)")
    print("3. Mots de passe des applications → Autre")
    print("4. Nom : 'MyXploit Email Service'")
    print("5. Copier le mot de passe généré (16 caractères)")
    print()
    
    email = input("📧 Votre email Gmail : ")
    password = input("🔑 Mot de passe d'application (16 caractères) : ")
    
    if len(password) != 16:
        print("❌ Le mot de passe d'application doit faire 16 caractères")
        return False
    
    config = {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': email,
        'EMAIL_PASSWORD': password
    }
    
    return sauvegarder_config(config, "Gmail")

def configurer_sendgrid():
    """Configuration SendGrid"""
    print("\n🔧 Configuration SendGrid")
    print("-" * 30)
    print("📋 Étapes à suivre :")
    print("1. Aller sur https://sendgrid.com/")
    print("2. Créer un compte gratuit")
    print("3. Vérifier votre email")
    print("4. Settings → API Keys → Create API Key")
    print("5. Copier la clé API générée")
    print()
    
    email = input("📧 Email émetteur (ex: noreply@myxploit.com) : ")
    api_key = input("🔑 Clé API SendGrid : ")
    
    config = {
        'SMTP_SERVER': 'smtp.sendgrid.net',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': email,
        'EMAIL_PASSWORD': api_key
    }
    
    return sauvegarder_config(config, "SendGrid")

def configurer_mailgun():
    """Configuration Mailgun"""
    print("\n🔧 Configuration Mailgun")
    print("-" * 30)
    print("📋 Étapes à suivre :")
    print("1. Aller sur https://www.mailgun.com/")
    print("2. Créer un compte gratuit")
    print("3. Vérifier votre domaine ou utiliser sandbox")
    print("4. Récupérer la clé API dans le dashboard")
    print()
    
    email = input("📧 Email émetteur (ex: noreply@myxploit.com) : ")
    api_key = input("🔑 Clé API Mailgun : ")
    
    config = {
        'SMTP_SERVER': 'smtp.mailgun.org',
        'SMTP_PORT': '587',
        'EMAIL_EMETTEUR': email,
        'EMAIL_PASSWORD': api_key
    }
    
    return sauvegarder_config(config, "Mailgun")

def configurer_manuel():
    """Configuration manuelle"""
    print("\n🔧 Configuration manuelle")
    print("-" * 30)
    
    smtp_server = input("🌐 Serveur SMTP : ")
    smtp_port = input("🔌 Port SMTP : ")
    email_emetteur = input("📧 Email émetteur : ")
    password = input("🔑 Mot de passe/Clé API : ")
    
    config = {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'EMAIL_EMETTEUR': email_emetteur,
        'EMAIL_PASSWORD': password
    }
    
    return sauvegarder_config(config, "Manuel")

def sauvegarder_config(config, service):
    """Sauvegarder la configuration"""
    print(f"\n💾 Sauvegarde de la configuration {service}...")
    
    # Créer le fichier .env
    env_content = f"""# Configuration email MyXploit - {service}
SMTP_SERVER={config['SMTP_SERVER']}
SMTP_PORT={config['SMTP_PORT']}
EMAIL_EMETTEUR={config['EMAIL_EMETTEUR']}
EMAIL_PASSWORD={config['EMAIL_PASSWORD']}
"""
    
    env_file = Path('.env')
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ Configuration sauvegardée dans {env_file}")
        
        # Afficher les variables pour Render
        print(f"\n🌐 Pour déployer sur Render, ajoutez ces variables d'environnement :")
        print("-" * 50)
        for key, value in config.items():
            if key == 'EMAIL_PASSWORD':
                print(f"{key}={value}")
            else:
                print(f"{key}={value}")
        print("-" * 50)
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return False

def tester_configuration():
    """Tester la configuration actuelle"""
    print("\n🧪 Test de la configuration actuelle...")
    
    # Vérifier si le fichier .env existe
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Aucun fichier .env trouvé")
        print("💡 Configurez d'abord un service email")
        return
    
    # Charger les variables d'environnement
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️ Module python-dotenv non installé")
        print("💡 Installez-le avec : pip install python-dotenv")
        return
    
    # Afficher la configuration
    print("\n📋 Configuration actuelle :")
    print(f"SMTP Server: {os.environ.get('SMTP_SERVER', 'Non configuré')}")
    print(f"SMTP Port: {os.environ.get('SMTP_PORT', 'Non configuré')}")
    print(f"Email émetteur: {os.environ.get('EMAIL_EMETTEUR', 'Non configuré')}")
    
    password = os.environ.get('EMAIL_PASSWORD', '')
    if password:
        print(f"Mot de passe: {'*' * len(password)} (configuré)")
    else:
        print("Mot de passe: Non configuré")
    
    # Proposer de tester
    if input("\n🧪 Voulez-vous tester l'envoi d'un email ? (o/n) : ").lower() == 'o':
        try:
            from test_email import main as test_email
            test_email()
        except ImportError:
            print("❌ Script de test non trouvé")
            print("💡 Lancez : python test_email.py")

def main():
    """Fonction principale"""
    print("🚀 Configuration Email MyXploit")
    
    while True:
        afficher_menu()
        choix = input("\n🎯 Votre choix (1-6) : ")
        
        if choix == '1':
            configurer_gmail()
        elif choix == '2':
            configurer_sendgrid()
        elif choix == '3':
            configurer_mailgun()
        elif choix == '4':
            configurer_manuel()
        elif choix == '5':
            tester_configuration()
        elif choix == '6':
            print("\n👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide")
        
        input("\n⏸️ Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()




