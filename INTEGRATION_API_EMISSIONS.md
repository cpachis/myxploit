# 🚀 Intégration des API de Calcul d'Émissions

## 📋 Vue d'ensemble

Ce système permet de calculer les émissions CO₂e côté serveur (Python/Flask) plutôt que côté client (JavaScript), ce qui est plus robuste et adapté pour un SaaS en ligne.

## 🔧 Installation

### 1. Ajouter le Blueprint dans votre app Flask

Dans votre fichier principal `app.py` ou `__init__.py` :

```python
from transport_api import transport_api

# Enregistrer le Blueprint
app.register_blueprint(transport_api)
```

### 2. Vérifier les modèles de base de données

Assurez-vous que vos modèles ont les champs nécessaires :

```python
class Transport(db.Model):
    # ... autres champs ...
    emis_kg = db.Column(db.Float, default=0.0)
    emis_tkm = db.Column(db.Float, default=0.0)
    niveau_calcul = db.Column(db.String(50))
    type_vehicule = db.Column(db.String(50))
    energie = db.Column(db.String(50))
    conso_vehicule = db.Column(db.Float)
    poids_tonnes = db.Column(db.Float)
    distance_km = db.Column(db.Float)

class Vehicule(db.Model):
    # ... autres champs ...
    consommation = db.Column(db.Float)  # L/100km
    emissions = db.Column(db.Float)     # g CO2e/km

class Energie(db.Model):
    # ... autres champs ...
    facteur = db.Column(db.Float)       # kg CO2e/L
```

## 🌐 Endpoints API disponibles

### 1. Recalcul de tous les transports
```
POST /api/transports/recalculer-emissions
Content-Type: application/json

{
  "action": "recalculer_tous"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Recalcul terminé: 5 succès, 0 erreurs",
  "succes": 5,
  "erreurs": 0,
  "resultats": [...]
}
```

### 2. Récupération de la liste mise à jour
```
GET /api/transports/liste-mise-a-jour
```

**Réponse :**
```json
{
  "success": true,
  "transports": [
    {
      "ref": "125",
      "emis_kg": 91.35,
      "emis_tkm": 0.010,
      "poids": 12.0,
      "distance": 89.4,
      "energie": "biognc",
      "niveau_calcul": "agregees_niveau_1"
    }
  ]
}
```

### 3. Recalcul d'un transport spécifique
```
POST /api/transports/{transport_id}/recalculer-emissions
```

## 🧮 Logique de calcul

### Niveau 1 (Agrégé)
- **Émissions totales** : `(distance/100) × consommation_véhicule × facteur_énergie`
- **kg CO₂e/t.km** : Imposé par le véhicule

### Niveaux 2-4 (Détaillés)
- **Émissions totales** : `(distance/100) × consommation_saisie × facteur_énergie`
- **kg CO₂e/t.km** : `émissions_total / (poids × distance)`

## 🚀 Utilisation côté client

### 1. Bouton de recalcul
```html
<button onclick="recalculerEmissionsServeur()">
  🚀 Recalculer émissions (serveur)
</button>
```

### 2. Fonction JavaScript
```javascript
async function recalculerEmissionsServeur() {
  try {
    const response = await fetch('/api/transports/recalculer-emissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'recalculer_tous' })
    });
    
    const resultat = await response.json();
    if (resultat.success) {
      // Mettre à jour l'affichage
      await mettreAJourListeAvecNouvellesDonnees();
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}
```

## 🔍 Logs et débogage

Le système génère des logs détaillés pour chaque calcul :

```
INFO:transport_api:Calcul des émissions pour le transport 125
INFO:transport_api:Transport 125: Calcul niveau 1
INFO:transport_api:Transport 125: Calcul avec facteur énergie 0.0
INFO:transport_api:Transport 125: Émissions calculées - 91.35 kg, 0.010 kg/t.km
```

## 🛡️ Gestion des erreurs

### Erreurs courantes
- **Données manquantes** : Poids, distance, véhicule, énergie
- **Véhicule non trouvé** : ID de véhicule invalide
- **Facteur d'émission manquant** : Énergie sans facteur CO₂
- **Erreurs de base de données** : Problèmes de sauvegarde

### Fallbacks
- **Niveau 1** : Utilise les émissions du véhicule si l'énergie n'est pas disponible
- **Validation** : Vérifie toutes les données avant calcul
- **Rollback** : Annule les modifications en cas d'erreur

## 🚀 Déploiement SaaS

### Avantages pour la production
1. **Calculs côté serveur** : Plus fiable et sécurisé
2. **Persistance des données** : Émissions sauvegardées en base
3. **Logs centralisés** : Traçabilité complète des calculs
4. **API REST** : Facilement intégrable avec d'autres services
5. **Gestion d'erreurs** : Robustesse en production

### Configuration recommandée
```python
# Production
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Logging en production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('emissions.log'),
        logging.StreamHandler()
    ]
)
```

## 🔄 Migration depuis l'ancien système

1. **Installer le nouveau Blueprint**
2. **Mettre à jour les modèles** si nécessaire
3. **Remplacer les fonctions JavaScript** par les appels API
4. **Tester** avec quelques transports
5. **Déployer** progressivement

## 📊 Monitoring et métriques

### Métriques à surveiller
- **Temps de calcul** : Performance des calculs
- **Taux de succès** : Pourcentage de calculs réussis
- **Erreurs** : Types et fréquences des erreurs
- **Utilisation** : Nombre de recalculs par jour

### Alertes recommandées
- **Temps de calcul > 30s** : Performance dégradée
- **Taux d'erreur > 5%** : Problème de données
- **Erreurs de base** : Problème de connectivité

---

## 🎯 Prochaines étapes

1. **Intégrer le Blueprint** dans votre app Flask
2. **Tester** avec un transport simple
3. **Valider** les calculs avec vos données
4. **Déployer** en production
5. **Monitorer** les performances

Pour toute question ou problème, consultez les logs et vérifiez la cohérence des données en base.
