# Guide de Dépannage - Déploiement Myxploit

## 🚨 Problèmes Courants et Solutions

### 1. Erreur de Build sur Render

#### Symptôme
```
Build failed: pip install -r requirements.txt
```

#### Solutions
- Vérifiez que `requirements-render.txt` existe et contient toutes les dépendances
- Assurez-vous que la version de Python est compatible (3.11.7)
- Vérifiez la syntaxe des fichiers de dépendances

#### Commande de vérification
```bash
python deploy_check.py
```

### 2. Erreur de Base de Données

#### Symptôme
```
OperationalError: (psycopg2.OperationalError) could not connect to server
```

#### Solutions
- Vérifiez que la base de données PostgreSQL est créée sur Render
- Assurez-vous que `DATABASE_URL` est correctement configurée
- Vérifiez que `psycopg2-binary` est dans `requirements-render.txt`

#### Vérification
- Consultez les logs de Render
- Testez le point `/health` de votre application

### 3. Erreur de Port

#### Symptôme
```
Address already in use
```

#### Solutions
- Utilisez `$PORT` dans votre configuration (Render le gère automatiquement)
- Vérifiez que Gunicorn écoute sur `0.0.0.0:$PORT`

#### Configuration correcte
```yaml
startCommand: gunicorn --bind 0.0.0.0:$PORT app:app
```

### 4. Erreur de Variables d'Environnement

#### Symptôme
```
KeyError: 'SECRET_KEY'
```

#### Solutions
- Vérifiez que `SECRET_KEY` est générée automatiquement par Render
- Assurez-vous que `FLASK_ENV=production`
- Vérifiez la configuration dans `render.yaml`

### 5. Erreur de Dépendances Manquantes

#### Symptôme
```
ModuleNotFoundError: No module named 'psycopg2'
```

#### Solutions
- Utilisez `requirements-render.txt` au lieu de `requirements.txt`
- Assurez-vous que `psycopg2-binary` est inclus
- Vérifiez que le build command pointe vers le bon fichier

### 6. Erreur de Logs

#### Symptôme
```
Permission denied: emissions.log
```

#### Solutions
- Utilisez `/tmp/emissions.log` en production
- Vérifiez les permissions sur Render
- Configurez `LOG_FILE=/tmp/emissions.log` dans `render.yaml`

## 🔧 Commandes de Diagnostic

### Vérification locale
```bash
# Vérifier la configuration
python deploy_check.py

# Tester l'application
python app.py

# Vérifier les dépendances
pip list
```

### Vérification sur Render
- Consultez les logs de build
- Consultez les logs de démarrage
- Testez le point `/health`
- Vérifiez les variables d'environnement

## 📋 Checklist de Déploiement

### Avant le déploiement
- [ ] `python deploy_check.py` passe sans erreur
- [ ] `requirements-render.txt` contient toutes les dépendances
- [ ] `render.yaml` est correctement configuré
- [ ] Code poussé sur GitHub

### Après le déploiement
- [ ] Build réussi sur Render
- [ ] Application accessible via l'URL fournie
- [ ] Point `/health` fonctionne
- [ ] Base de données connectée
- [ ] Logs sans erreur critique

## 🆘 Support

### Ressources utiles
1. [Documentation Render](https://render.com/docs)
2. [Documentation Flask](https://flask.palletsprojects.com/)
3. [Documentation SQLAlchemy](https://docs.sqlalchemy.org/)
4. Logs de votre application sur Render

### En cas de problème persistant
1. Vérifiez les logs de Render
2. Testez localement avec `python deploy_check.py`
3. Vérifiez la configuration dans `render.yaml`
4. Consultez la documentation des outils utilisés


