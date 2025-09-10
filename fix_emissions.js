// Script de correction pour les calculs d'émissions
function fixEmissionsCalculation() {
    console.log('🔧 Correction du calcul d\'émissions');
    
    // Vérifier que les champs existent
    const distanceField = document.getElementById('transport-distance');
    const poidsField = document.getElementById('transport-poids');
    const consoField = document.getElementById('transport-conso-vehicule');
    
    if (!distanceField || !poidsField || !consoField) {
        console.error('❌ Champs manquants pour le calcul');
        return false;
    }
    
    // Vérifier les valeurs
    const distance = parseFloat(distanceField.value) || 0;
    const poids = parseFloat(poidsField.value) || 0;
    const conso = parseFloat(consoField.value) || 0;
    
    console.log('📊 Valeurs actuelles :');
    console.log('   - Distance:', distance);
    console.log('   - Poids:', poids);
    console.log('   - Consommation:', conso);
    
    if (distance === 0 || poids === 0 || conso === 0) {
        console.warn('⚠️ Valeurs manquantes, utilisation de valeurs par défaut');
        
        // Valeurs par défaut pour le test
        if (distance === 0) {
            distanceField.value = '100';
            console.log('✅ Distance fixée à 100 km');
        }
        if (poids === 0) {
            poidsField.value = '2.5';
            console.log('✅ Poids fixé à 2.5 tonnes');
        }
        if (conso === 0) {
            consoField.value = '14';
            console.log('✅ Consommation fixée à 14 L/100km');
        }
        
        console.log('✅ Valeurs par défaut appliquées');
    }
    
    // Relancer le calcul
    if (typeof calculateEmissions === 'function') {
        calculateEmissions();
        console.log('✅ Calcul d\'émissions relancé');
    } else {
        console.error('❌ Fonction calculateEmissions non trouvée');
    }
    
    return true;
}

// Exécuter la correction automatiquement
console.log('🚀 Script de correction des émissions chargé');
console.log('💡 Exécutez fixEmissionsCalculation() dans la console pour corriger les calculs');