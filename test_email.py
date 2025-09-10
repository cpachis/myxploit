#!/usr/bin/env python3
"""
Script de test pour l'envoi d'emails
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from myxploit.app import envoyer_email, envoyer_email_confirmation_client, envoyer_email_confirmation_transporteur
from myxploit.app import Client, Transporteur, db, app

def test_email_simple():
    """Test d'envoi d'email simple"""
    print("🧪 Test d'envoi d'email simple...")
    
    destinataire = "test@example.com"
    sujet = "Test MyXploit - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    contenu_html = """
    <html>
    <body>
        <h2>Test d'envoi d'email</h2>
        <p>Ceci est un test d'envoi d'email depuis MyXploit.</p>
        <p>Date et heure : {}</p>
        <p>Si vous recevez cet email, la configuration est correcte !</p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    contenu_texte = """
    Test d'envoi d'email
    
    Ceci est un test d'envoi d'email depuis MyXploit.
    Date et heure : {}
    
    Si vous recevez cet email, la configuration est correcte !
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    resultat = envoyer_email(destinataire, sujet, contenu_html, contenu_texte)
    
    if resultat:
        print("✅ Email envoyé avec succès (ou simulé)")
    else:
        print("❌ Échec de l'envoi d'email")
    
    return resultat

def test_email_client():
    """Test d'envoi d'email de confirmation client"""
    print("\n🧪 Test d'envoi d'email de confirmation client...")
    
    # Créer un client de test
    client_test = Client(
        nom="Client Test",
        email="client-test@example.com",
        telephone="01 23 45 67 89",
        adresse="123 Rue de Test, 75001 Paris"
    )
    
    resultat = envoyer_email_confirmation_client(client_test)
    
    if resultat:
        print("✅ Email de confirmation client envoyé avec succès (ou simulé)")
    else:
        print("❌ Échec de l'envoi d'email de confirmation client")
    
    return resultat

def test_email_transporteur():
    """Test d'envoi d'email de confirmation transporteur"""
    print("\n🧪 Test d'envoi d'email de confirmation transporteur...")
    
    # Créer un transporteur de test
    transporteur_test = Transporteur(
        nom="Transporteur Test",
        email="transporteur-test@example.com",
        telephone="01 98 76 54 32",
        adresse="456 Avenue de Test, 75008 Paris"
    )
    
    resultat = envoyer_email_confirmation_transporteur(transporteur_test)
    
    if resultat:
        print("✅ Email de confirmation transporteur envoyé avec succès (ou simulé)")
    else:
        print("❌ Échec de l'envoi d'email de confirmation transporteur")
    
    return resultat

def afficher_configuration():
    """Afficher la configuration email actuelle"""
    print("\n📧 Configuration email actuelle :")
    print(f"SMTP Server: {os.environ.get('SMTP_SERVER', 'smtp.gmail.com')}")
    print(f"SMTP Port: {os.environ.get('SMTP_PORT', '587')}")
    print(f"Email émetteur: {os.environ.get('EMAIL_EMETTEUR', 'noreply@myxploit.com')}")
    
    mot_de_passe = os.environ.get('EMAIL_PASSWORD', '')
    if mot_de_passe:
        print(f"Mot de passe: {'*' * len(mot_de_passe)} (configuré)")
    else:
        print("Mot de passe: Non configuré (simulation activée)")

def main():
    """Fonction principale"""
    print("🚀 Test d'envoi d'emails MyXploit")
    print("=" * 50)
    
    # Afficher la configuration
    afficher_configuration()
    
    # Tests
    test1 = test_email_simple()
    test2 = test_email_client()
    test3 = test_email_transporteur()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé des tests :")
    print(f"Email simple: {'✅' if test1 else '❌'}")
    print(f"Email client: {'✅' if test2 else '❌'}")
    print(f"Email transporteur: {'✅' if test3 else '❌'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 Tous les tests sont passés avec succès !")
    else:
        print("\n⚠️ Certains tests ont échoué.")
        print("\n💡 Pour configurer l'envoi d'emails réels :")
        print("1. Configurez les variables d'environnement dans Render :")
        print("   - SMTP_SERVER")
        print("   - SMTP_PORT")
        print("   - EMAIL_EMETTEUR")
        print("   - EMAIL_PASSWORD")
        print("2. Ou utilisez un service comme SendGrid, Mailgun, etc.")

if __name__ == "__main__":
    main()







