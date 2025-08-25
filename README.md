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

Pour la production, utilisez Gunicorn :
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 Support

Pour toute question ou problème, consultez la documentation ou contactez l'équipe de développement. 