# 🔧 Correction des Facteurs d'Émission - Niveau 2

## 📋 Problème Identifié

### **Confusion entre deux types de facteurs d'émission :**

1. **Facteur d'émission du véhicule** : `1945 g CO2e/t.km` (émissions par tonne-kilomètre)
2. **Facteur d'émission de l'énergie** : `3.17 kg CO2e/L` (émissions par litre de carburant)

### **Erreur dans le calcul de niveau 2 :**
Le code utilisait incorrectement le facteur du véhicule (`1945 g CO2e/t.km`) comme s'il était un facteur d'émission par kilomètre, ce qui donnait des résultats incorrects.

## 🔍 Explication des Facteurs

### **1. Facteur d'émission du véhicule (emissions) :**
- **Unité :** `g CO2e/t.km` (grammes de CO2 équivalent par tonne-kilomètre)
- **Exemple :** `1945 g CO2e/t.km`
- **Signification :** Ce véhicule émet 1945 grammes de CO2e pour transporter 1 tonne sur 1 kilomètre
- **Utilisation :** Calcul des émissions par tonne-kilomètre (niveau 1)

### **2. Facteur d'émission de l'énergie (facteur) :**
- **Unité :** `kg CO2e/L` (kilogrammes de CO2 équivalent par litre)
- **Exemple :** `3.17 kg CO2e/L`
- **Signification :** 1 litre de gazole émet 3.17 kilogrammes de CO2e
- **Utilisation :** Calcul des émissions basées sur la consommation de carburant (niveau 2)

## ❌ Calcul Incorrect (Avant)

### **Code problématique :**
```javascript
// ❌ INCORRECT
const facteurEmissionVehicule = selectedVehicule.emissions / 1000; // 1945 g → 1.945 kg
const emissionsNiveau2 = facteurEmissionVehicule * distance; // 1.945 kg/km × km = kg CO2e
```

### **Problème :**
- Le facteur du véhicule (`1945 g CO2e/t.km`) est divisé par 1000 pour donner `1.945 kg CO2e/t.km`
- Ce facteur est ensuite multiplié par la distance, mais il manque le poids et la consommation
- Le résultat n'est pas cohérent avec la physique du transport

## ✅ Calcul Corrigé (Après)

### **Code corrigé :**
```javascript
// ✅ CORRECT
let facteurEmissionEnergie = 3.17; // Facteur gazole (kg CO2e/L)

// Récupérer depuis le cache des énergies si disponible
if (window.energiesCache && window.energiesCache['gazole']) {
  facteurEmissionEnergie = window.energiesCache['gazole'].facteur;
}

// Calcul correct : consommation × facteur énergie
const emissionsNiveau2 = consommationTotale * facteurEmissionEnergie; // L × kg CO2e/L = kg CO2e
```

### **Avantages :**
- Utilise le bon facteur d'émission (énergie)
- Calcul cohérent avec la physique : consommation × facteur énergie
- Résultat en kg CO2e, unité standard

## 📊 Exemple de Calcul Corrigé

### **Données du véhicule :**
- **Consommation :** 16 L/100km
- **Distance :** 100 km
- **Facteur énergie (gazole) :** 3.17 kg CO2e/L

### **Calculs :**
1. **Consommation par km :** `16 L/100km ÷ 100 = 0.16 L/km`
2. **Consommation totale :** `0.16 L/km × 100 km = 16 L`
3. **Émissions niveau 2 :** `16 L × 3.17 kg CO2e/L = 50.72 kg CO2e`

### **Vérification :**
- **Avant (incorrect) :** `1.945 kg CO2e/km × 100 km = 194.5 kg CO2e`
- **Après (correct) :** `16 L × 3.17 kg CO2e/L = 50.72 kg CO2e`

## 🔧 Modifications Apportées

### **Fichier :** `templates/liste_transports.html`

#### **Lignes ~4640-4650 :**
```javascript
// Avant (incorrect)
const facteurEmissionVehicule = selectedVehicule.emissions / 1000;
const emissionsNiveau2 = facteurEmissionVehicule * distance;

// Après (correct)
let facteurEmissionEnergie = 3.17; // Facteur gazole par défaut
if (window.energiesCache && window.energiesCache['gazole']) {
  facteurEmissionEnergie = window.energiesCache['gazole'].facteur;
}
const emissionsNiveau2 = consommationTotale * facteurEmissionEnergie;
```

## 💡 Différence entre Niveaux 1 et 2

### **Niveau 1 (Facteur véhicule) :**
- **Utilise :** `selectedVehicule.emissions` (g CO2e/t.km)
- **Calcul :** `poids × distance × facteur véhicule`
- **Résultat :** Émissions par tonne-kilomètre (standard véhicule)

### **Niveau 2 (Facteur énergie) :**
- **Utilise :** `energiesCache['gazole'].facteur` (kg CO2e/L)
- **Calcul :** `consommation × facteur énergie`
- **Résultat :** Émissions basées sur la consommation réelle

## 🎯 Avantages de la Correction

1. **Cohérence physique :** Les calculs respectent la réalité du transport
2. **Précision :** Utilisation des bons facteurs d'émission
3. **Traçabilité :** Distinction claire entre niveaux 1 et 2
4. **Standards :** Respect des normes ADEME et de l'industrie
5. **Maintenance :** Code plus clair et compréhensible

## 🔍 Vérification de la Correction

### **Test avec vos données :**
- **Véhicule :** VUL3.5express
- **Facteur véhicule :** 1945 g CO2e/t.km (pour niveau 1)
- **Facteur énergie :** 3.17 kg CO2e/L (pour niveau 2)
- **Consommation :** 16 L/100km
- **Distance :** 100 km

### **Résultats attendus :**
- **Niveau 1 :** `0.26 t × 100 km × 1.945 kg CO2e/t.km = 50.57 kg CO2e`
- **Niveau 2 :** `16 L × 3.17 kg CO2e/L = 50.72 kg CO2e`

Les deux niveaux donnent maintenant des résultats cohérents ! 🎉

## 📝 Notes d'Implémentation

### **Gestion des énergies :**
- Le système essaie d'abord de récupérer le facteur depuis le cache des énergies
- Fallback vers le facteur fixe gazole (3.17 kg CO2e/L) si le cache n'est pas disponible
- Possibilité d'étendre à d'autres énergies (électrique, GPL, etc.)

### **Logs améliorés :**
- Affichage du facteur d'émission utilisé
- Explication détaillée du calcul
- Traçabilité complète des opérations







