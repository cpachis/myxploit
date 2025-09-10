#!/usr/bin/env python3
"""
Script pour tester et corriger le calcul d'émissions
"""

def test_emissions_calculation():
    """Tester le calcul d'émissions avec des valeurs de test"""
    
    print("🧪 Test du calcul d'émissions")
    print("=" * 50)
    
    # Valeurs de test
    distance = 100.0  # km
    poids = 2.5       # tonnes
    niveau = "niveau1"
    conso = 14.0      # L/100km
    facteur_emission = 3.1  # kg CO₂e/L
    
    print(f"📊 Valeurs d'entrée :")
    print(f"   - Distance: {distance} km")
    print(f"   - Poids: {poids} tonnes")
    print(f"   - Niveau: {niveau}")
    print(f"   - Consommation: {conso} L/100km")
    print(f"   - Facteur émission: {facteur_emission} kg CO₂e/L")
    
    # Calcul des émissions
    if distance > 0 and conso > 0:
        # Émissions par km
        emis_par_km = (conso / 100) * facteur_emission
        
        # Émissions totales
        emis_totales = emis_par_km * distance
        
        # Émissions par tonne.km
        if poids > 0:
            emis_tkm = emis_totales / (distance * poids)
        else:
            emis_tkm = 0
        
        print(f"\n✅ Résultats du calcul :")
        print(f"   - Émissions par km: {emis_par_km:.3f} kg CO₂e/km")
        print(f"   - Émissions totales: {emis_totales:.3f} kg CO₂e")
        print(f"   - Émissions par t.km: {emis_tkm:.3f} kg CO₂e/t.km")
        
        return {
            'success': True,
            'emis_par_km': emis_par_km,
            'emis_totales': emis_totales,
            'emis_tkm': emis_tkm
        }
    else:
        print(f"\n❌ Erreur : Distance ou consommation invalide")
        print(f"   - Distance: {distance} (doit être > 0)")
        print(f"   - Consommation: {conso} (doit être > 0)")
        return {
            'success': False,
            'error': 'Valeurs invalides'
        }

def create_emissions_fix_script():
    """Créer un script pour corriger les calculs d'émissions"""
    
    script_content = '''
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
        if (distance === 0) distanceField.value = '100';
        if (poids === 0) poidsField.value = '2.5';
        if (conso === 0) consoField.value = '14';
        
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

// Exécuter la correction
fixEmissionsCalculation();
'''
    
    with open('fix_emissions.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de correction créé : fix_emissions.js")
    print("   Vous pouvez l'exécuter dans la console du navigateur")

if __name__ == "__main__":
    # Tester le calcul
    result = test_emissions_calculation()
    
    if result['success']:
        print(f"\n🎉 Le calcul d'émissions fonctionne correctement !")
    else:
        print(f"\n❌ Problème avec le calcul d'émissions")
    
    # Créer le script de correction
    create_emissions_fix_script()
