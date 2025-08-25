# 🚀 Guide de Déploiement Myxploit

## 📋 Prérequis

- **Compte GitHub** : Pour héberger le code
- **Compte Render** : Pour le déploiement gratuit
- **Python 3.11+** : Installé localement

## 🔧 Préparation locale

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Configurer l'environnement
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer .env avec vos valeurs
nano .env
```

### 3. Tester localement
```bash
python app.py
```

## 🌐 Déploiement sur Render (Gratuit)

### Étape 1 : Préparer le repository GitHub

1. **Créer un repository** sur GitHub
2. **Pousser votre code** :
```bash
git init
git add .
git commit -m "Initial commit - Myxploit Transport API"
git branch -M main
git remote add origin https://github.com/votre-username/myxploit.git
git push -u origin main
```

### Étape 2 : Déployer sur Render

1. **Aller sur [render.com](https://render.com)**
2. **Se connecter avec GitHub**
3. **Cliquer "New +" → "Web Service"**
4. **Connecter votre repository GitHub**
5. **Configurer le service** :
   - **Name** : `myxploit-transports`
   - **Environment** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
   - **Plan** : `Free`

### Étape 3 : Configurer les variables d'environnement

Dans Render, aller dans **Environment** et ajouter :

```
FLASK_ENV=production
SECRET_KEY=votre_cle_secrete_tres_longue
```

### Étape 4 : Créer la base de données

1. **New +** → **PostgreSQL**
2. **Name** : `myxploit-db`
3. **Plan** : `Free`
4. **Copier l'URL de connexion**
5. **L'ajouter dans les variables d'environnement** :
   ```
   DATABASE_URL=postgresql://...
   ```

## 🔄 Déploiement automatique

### Configuration GitHub Actions (optionnel)

Créer `.github/workflows/deploy.yml` :

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        uses: johnbeynon/render-deploy-action@v0.0.1
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
```

## 🧪 Tests post-déploiement

### 1. Vérifier la santé
```
https://votre-app.onrender.com/health
```

### 2. Tester l'API
```bash
curl -X POST https://votre-app.onrender.com/api/transports/recalculer-emissions \
  -H "Content-Type: application/json" \
  -d '{"action": "recalculer_tous"}'
```

### 3. Vérifier les logs
Dans Render → **Logs** pour voir les erreurs

## 🚀 Déploiement sur d'autres plateformes

### Railway
1. **Connecter GitHub**
2. **Déployer automatiquement**
3. **Variables d'environnement** dans l'interface

### Heroku
1. **Installer Heroku CLI**
2. **Créer l'app** : `heroku create myxploit-transports`
3. **Configurer** : `heroku config:set FLASK_ENV=production`
4. **Déployer** : `git push heroku main`

### DigitalOcean
1. **Créer un Droplet**
2. **Installer Docker**
3. **Utiliser docker-compose**

## 🔍 Monitoring et maintenance

### Logs
- **Render** : Interface web
- **Local** : Fichier `emissions.log`

### Métriques
- **Uptime** : Vérifier `/health`
- **Performance** : Temps de réponse des API
- **Base de données** : Connexions actives

### Mises à jour
```bash
# Local
git pull origin main
pip install -r requirements.txt

# Redéployer
git push origin main
# Render se met à jour automatiquement
```

## 🛠️ Dépannage

### Erreurs courantes

1. **Module not found** : Vérifier `requirements.txt`
2. **Database connection** : Vérifier `DATABASE_URL`
3. **Port already in use** : Changer le port dans `.env`
4. **Permission denied** : Vérifier les droits des fichiers

### Commandes utiles

```bash
# Vérifier les processus Python
ps aux | grep python

# Vérifier les ports
netstat -tulpn | grep :5000

# Logs en temps réel
tail -f emissions.log
```

## 📞 Support

- **Issues GitHub** : Pour les bugs
- **Render Support** : Pour les problèmes de déploiement
- **Documentation** : `INTEGRATION_API_EMISSIONS.md`

---

## 🎯 Prochaines étapes

1. **Déployer sur Render** (gratuit)
2. **Tester l'API** en ligne
3. **Configurer un domaine** personnalisé
4. **Mettre en place le monitoring**
5. **Optimiser les performances**

Votre SaaS sera accessible en ligne et vous pourrez le modifier en continu ! 🚀
