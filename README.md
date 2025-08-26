# MyXploit - Application de Gestion de Transports

Application Flask pour la gestion des transports et des émissions CO2.

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd myxploit
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Lancer l'application
```bash
python run.py
```

L'application sera accessible sur : http://localhost:5000

## 🔑 Connexion

Les identifiants par défaut se trouvent dans `data/users.json`.

## 📁 Structure du Projet

```
myxploit/
├── app.py              # Application principale
├── run.py              # Script de démarrage
├── requirements.txt    # Dépendances Python
├── data/               # Données JSON
│   ├── users.json      # Utilisateurs
│   ├── clients.json    # Clients
│   ├── transports.json # Transports
│   └── ...
├── templates/          # Templates HTML
├── static/            # Fichiers statiques (CSS, JS)
└── blueprints/        # Modules de l'application
```

## 🛠️ Fonctionnalités

- **Authentification** : Système de connexion sécurisé
- **Gestion des clients** : CRUD des clients
- **Gestion des transports** : Suivi des transports et émissions
- **Paramétrage** : Configuration des énergies, véhicules, etc.
- **Tableau de bord** : Vue d'ensemble des données
- **Administration** : Gestion des utilisateurs

## 🔧 Configuration

### Variables d'environnement
- `SECRET_KEY` : Clé secrète pour les sessions (optionnel)

### Port par défaut
- Port : 5000
- Host : 0.0.0.0 (accessible depuis l'extérieur)

## 📊 Données

L'application utilise des fichiers JSON pour stocker les données :
- `clients.json` : Informations des clients
- `transports.json` : Historique des transports
- `energies.json` : Types d'énergies
- `vehicules.json` : Types de véhicules
- `soustraitants.json` : Sous-traitants
- `users.json` : Utilisateurs de l'application

## 🚀 Déploiement

### Déploiement Local avec Gunicorn
Pour la production, utilisez Gunicorn :
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Déploiement sur Render

#### 1. Préparation du projet
Avant de déployer, vérifiez votre configuration :
```bash
python deploy_check.py
```

#### 2. Configuration Render
- Créez un compte sur [Render](https://render.com)
- Connectez votre repository GitHub
- Créez un nouveau **Web Service**
- Sélectionnez votre repo `myxploit`

#### 3. Configuration du service
Le fichier `render.yaml` est déjà configuré avec :
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn --bind 0.0.0.0:$PORT app:app`
- **Environment** : Python 3.11.7

#### 4. Variables d'environnement
Render configurera automatiquement :
- `SECRET_KEY` : Générée automatiquement
- `DATABASE_URL` : Fournie par la base de données PostgreSQL
- `FLASK_ENV` : `production`
- `PORT` : Fourni par Render

#### 5. Base de données
- Render créera automatiquement une base PostgreSQL
- L'application se connectera automatiquement

#### 6. Déploiement
- Poussez vos modifications sur GitHub
- Render déploiera automatiquement
- Surveillez les logs de build et de démarrage

#### 7. Vérification
Après le déploiement, testez :
- L'URL de votre application
- Le point de contrôle de santé : `/health`
- La connexion à la base de données

### Résolution des problèmes courants

#### Erreur de base de données
- Vérifiez que `psycopg2-binary` est dans `requirements.txt`
- Assurez-vous que `DATABASE_URL` est correctement configurée

#### Erreur de port
- Utilisez `$PORT` dans votre configuration (Render le gère automatiquement)
- Vérifiez que Gunicorn est configuré pour écouter sur `0.0.0.0`

#### Erreur de dépendances
- Vérifiez que toutes les dépendances sont dans `requirements.txt`
- Utilisez `deploy_check.py` pour diagnostiquer

#### Logs et débogage
- Consultez les logs de build et de démarrage sur Render
- Utilisez le point `/health` pour vérifier l'état de l'application

## 📝 Support

Pour toute question ou problème de déploiement, consultez :
1. Les logs de Render
2. Le script `deploy_check.py`
3. La documentation Flask et Render 