# 📧 Configuration Email pour MyXploit

## 🎯 Option 1 : Gmail (Recommandé pour commencer)

### Étape 1 : Créer un mot de passe d'application

1. **Aller sur votre compte Google** : https://myaccount.google.com/
2. **Sécurité** → **Validation en 2 étapes** (doit être activée)
3. **Mots de passe des applications** → **Sélectionner une application** → **Autre**
4. **Nom** : "MyXploit Email Service"
5. **Copier le mot de passe généré** (16 caractères)

### Étape 2 : Configurer les variables d'environnement

#### Pour le développement local :
Créer un fichier `.env` dans le dossier `myxploit/` :

```bash
# Configuration Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_EMETTEUR=votre-email@gmail.com
EMAIL_PASSWORD=votre-mot-de-passe-app-16-caracteres
```

#### Pour le déploiement sur Render :
Dans votre dashboard Render, aller dans **Environment** et ajouter :

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_EMETTEUR=votre-email@gmail.com
EMAIL_PASSWORD=votre-mot-de-passe-app-16-caracteres
```

### Étape 3 : Tester la configuration

```bash
# Dans le dossier myxploit
python test_email.py
```

---

## 🎯 Option 2 : SendGrid (Pour la production)

### Étape 1 : Créer un compte SendGrid

1. **Aller sur** : https://sendgrid.com/
2. **Créer un compte gratuit** (100 emails/jour)
3. **Vérifier votre email**
4. **Créer une clé API** : Settings → API Keys → Create API Key

### Étape 2 : Configuration

```bash
# Variables d'environnement
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
EMAIL_EMETTEUR=noreply@myxploit.com
EMAIL_PASSWORD=votre-cle-api-sendgrid
```

---

## 🎯 Option 3 : Mailgun (Alternative robuste)

### Étape 1 : Créer un compte Mailgun

1. **Aller sur** : https://www.mailgun.com/
2. **Créer un compte gratuit** (5000 emails/mois)
3. **Vérifier votre domaine** ou utiliser le domaine sandbox
4. **Récupérer la clé API** dans le dashboard

### Étape 2 : Configuration

```bash
# Variables d'environnement
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
EMAIL_EMETTEUR=noreply@myxploit.com
EMAIL_PASSWORD=votre-cle-api-mailgun
```

---

## 🧪 Test de la configuration

### Script de test automatique

```bash
# Activer l'environnement virtuel
venv\Scripts\activate

# Lancer le test
python test_email.py
```

### Test manuel via l'interface

1. **Démarrer l'application** : `python run.py`
2. **Aller sur** : http://localhost:5000/invitations
3. **Inviter un utilisateur** avec votre email
4. **Vérifier votre boîte mail**

---

## 🔧 Dépannage

### Erreur "Authentication failed"
- ✅ Vérifier que la validation en 2 étapes est activée (Gmail)
- ✅ Utiliser un mot de passe d'application, pas votre mot de passe normal
- ✅ Vérifier les variables d'environnement

### Erreur "Connection refused"
- ✅ Vérifier le serveur SMTP et le port
- ✅ Vérifier votre connexion internet
- ✅ Vérifier les paramètres de pare-feu

### Emails non reçus
- ✅ Vérifier le dossier spam
- ✅ Vérifier que l'email émetteur est correct
- ✅ Tester avec un autre email de destination

---

## 📊 Comparaison des services

| Service | Gratuit | Limite | Facilité | Recommandation |
|---------|---------|--------|----------|----------------|
| Gmail | ✅ | 500/jour | ⭐⭐⭐⭐⭐ | Développement |
| SendGrid | ✅ | 100/jour | ⭐⭐⭐⭐ | Production |
| Mailgun | ✅ | 5000/mois | ⭐⭐⭐ | Production |
| Amazon SES | ❌ | Payant | ⭐⭐ | Grande échelle |

---

## 🚀 Prochaines étapes

1. **Choisir un service** selon vos besoins
2. **Configurer les variables d'environnement**
3. **Tester l'envoi d'emails**
4. **Déployer sur Render** avec la configuration
5. **Monitorer les envois** et ajuster si nécessaire




