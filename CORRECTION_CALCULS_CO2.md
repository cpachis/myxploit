# 🚛 Correction des Calculs d'Émissions CO2e/t.km

## 📋 Problème Identifié

L'ancienne formule de calcul des émissions CO2e/t.km était **incorrecte** :

```javascript
// ❌ ANCIENNE FORMULE INCORRECTE
const emisTkm = (poids * dist) > 0 ? emisKg / (poids * dist) : 0;
```

Cette formule calculait les émissions par tonne-kilomètre en divisant les émissions totales par (poids × distance), ce qui donnait des résultats variables selon les paramètres du transport.

## ✅ Solution Implémentée

### **Nouvelle Formule Corrigée :**

```javascript
// ✅ NOUVELLE FORMULE CORRECTE
let emisTkm;
if (vehiculeFacteurEmissions > 0) {
    // Si on a le facteur du véhicule, l'utiliser directement
    emisTkm = vehiculeFacteurEmissions;
} else {
    // Sinon, calculer à partir des émissions totales (méthode de secours)
    emisTkm = (poids * dist) > 0 ? emisKg / (poids * dist) : 0;
}
```

### **Principe de la Correction :**

1. **CO2e/t.km = Facteur d'émission du véhicule** (valeur constante)
2. **CO2e total = Facteur d'émission × Poids × Distance**

## 🔧 Modifications Apportées

### **1. Fichier `transport_detail.js`**
- Ajout de la variable globale `vehiculeFacteurEmissions`
- Modification de la fonction `initializeData()` pour accepter le facteur du véhicule
- Correction de la fonction `recalcPhaseEmissions()` pour utiliser le facteur du véhicule

### **2. Fichier `phases.js`**
- Ajout de la variable globale `vehiculeFacteurEmissions`
- Ajout de la fonction `setVehiculeFacteur()` pour définir le facteur
- Correction de la fonction `recalcPhaseEmissions()`

### **3. Fichier `phases_simple.js`**
- Ajout de la même logique pour la cohérence

### **4. Template `transport_detail.html`**
- Ajout de la div cachée pour le facteur d'émission du véhicule
- Modification de l'initialisation JavaScript pour passer le facteur du véhicule

### **5. Application Flask (`app.py`)**
- Modification de la route `transport_detail()` pour déterminer le facteur d'émission du véhicule
- Ajout de la logique de recherche du véhicule dans les phases ou par l'énergie

## 📊 Exemple de Calcul Corrigé

### **Données du véhicule :**
- **Facteur d'émission :** 1945 g CO2e/t.km
- **Poids du transport :** 0.250 tonnes
- **Distance :** 100 km

### **Calculs :**
1. **CO2e/t.km = 1945 g CO2e/t.km** (facteur constant du véhicule)
2. **CO2e total = 1945 × 0.250 × 100 = 48,625 g = 48.625 kg**

### **Vérification :**
- **CO2e/t.km = 48.625 kg ÷ (0.250 t × 100 km) = 1.945 kg/t.km = 1945 g/t.km** ✅

## 💡 Avantages de la Correction

1. **Précision :** Les émissions par tonne-kilomètre sont maintenant constantes pour un véhicule donné
2. **Cohérence :** Respect des standards ADEME et des facteurs d'émission des véhicules
3. **Simplicité :** Plus besoin de recalculer le facteur à chaque modification de phase
4. **Traçabilité :** Les émissions totales sont calculées à partir du facteur standard du véhicule
5. **Fiabilité :** Les calculs respectent la physique et les standards de l'industrie

## 🧪 Test de la Correction

Un fichier de test a été créé : `test_calculs_vehicule_corrige.html`

Ce fichier permet de :
- Vérifier que la formule corrigée fonctionne correctement
- Comparer avec l'ancienne formule incorrecte
- Comprendre le principe du calcul corrigé
- Tester avec différentes valeurs

## 🔄 Rétrocompatibilité

La correction maintient la rétrocompatibilité :
- Si le facteur du véhicule n'est pas disponible, le système utilise l'ancienne méthode de calcul
- Les transports existants continuent de fonctionner
- Les nouvelles phases utilisent automatiquement le facteur du véhicule

## 📝 Notes d'Implémentation

- Le facteur d'émission du véhicule est recherché dans l'ordre suivant :
  1. Dans les phases du transport (champ `vehicule_id`)
  2. Par correspondance d'énergie entre le transport et les véhicules
- La fonction `setVehiculeFacteur()` est rendue globale pour être accessible depuis tous les scripts
- Les logs de console permettent de vérifier quelle méthode de calcul est utilisée

## 🎯 Prochaines Étapes

1. **Tests en production** pour vérifier le bon fonctionnement
2. **Migration des données** pour associer les transports existants aux véhicules appropriés
3. **Formation des utilisateurs** sur la nouvelle logique de calcul
4. **Documentation utilisateur** mise à jour avec les nouvelles formules















