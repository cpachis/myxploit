# Configuration pour l'envoi d'emails
# Ces variables peuvent être définies dans les variables d'environnement de Render

# Configuration SMTP
SMTP_SERVER = 'smtp.gmail.com'  # ou votre serveur SMTP
SMTP_PORT = 587  # Port SMTP (587 pour TLS, 465 pour SSL)

# Email de l'émetteur
EMAIL_EMETTEUR = 'noreply@myxploit.com'  # Email d'où partent les messages
EMAIL_PASSWORD = ''  # Mot de passe de l'email (à configurer dans Render)

# Configuration alternative pour Gmail
# EMAIL_EMETTEUR = 'votre-email@gmail.com'
# EMAIL_PASSWORD = 'votre-mot-de-passe-app'  # Mot de passe d'application Gmail

# Configuration pour SendGrid (alternative)
# SMTP_SERVER = 'smtp.sendgrid.net'
# SMTP_PORT = 587
# EMAIL_EMETTEUR = 'noreply@myxploit.com'
# EMAIL_PASSWORD = 'votre-clé-api-sendgrid'

# Configuration pour Mailgun (alternative)
# SMTP_SERVER = 'smtp.mailgun.org'
# SMTP_PORT = 587
# EMAIL_EMETTEUR = 'noreply@myxploit.com'
# EMAIL_PASSWORD = 'votre-clé-api-mailgun'
