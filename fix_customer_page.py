#!/usr/bin/env python3
"""
Script pour corriger la page customer et les calculs d'émissions
"""

def create_customer_fix_script():
    """Créer un script de correction pour la page customer"""
    
    script_content = '''
// Script de correction pour la page customer
function fixCustomerPage() {
    console.log('🔧 Correction de la page customer');
    
    // 1. Vérifier que les champs existent
    const fields = {
        distance: document.getElementById('transport-distance'),
        poids: document.getElementById('transport-poids'),
        conso: document.getElementById('transport-conso-vehicule'),
        niveau: document.getElementById('transport-niveau-calcul'),
        typeVehicule: document.getElementById('transport-type-vehicule')
    };
    
    console.log('📋 Vérification des champs :');
    for (const [name, field] of Object.entries(fields)) {
        if (field) {
            console.log(`   ✅ ${name}: ${field.value || 'vide'}`);
        } else {
            console.log(`   ❌ ${name}: champ manquant`);
        }
    }
    
    // 2. Ajouter des valeurs par défaut si nécessaire
    if (fields.distance && !fields.distance.value) {
        fields.distance.value = '100';
        console.log('✅ Distance fixée à 100 km');
    }
    
    if (fields.poids && !fields.poids.value) {
        fields.poids.value = '2.5';
        console.log('✅ Poids fixé à 2.5 tonnes');
    }
    
    if (fields.conso && !fields.conso.value) {
        fields.conso.value = '14';
        console.log('✅ Consommation fixée à 14 L/100km');
    }
    
    if (fields.niveau && !fields.niveau.value) {
        fields.niveau.value = 'niveau1';
        console.log('✅ Niveau fixé à niveau1');
    }
    
    // 3. S'assurer qu'un type de véhicule est sélectionné
    if (fields.typeVehicule && !fields.typeVehicule.value) {
        // Sélectionner le premier option disponible
        const options = fields.typeVehicule.querySelectorAll('option');
        if (options.length > 1) {
            fields.typeVehicule.value = options[1].value; // Skip l'option vide
            console.log('✅ Type de véhicule sélectionné');
        }
    }
    
    // 4. Relancer les calculs
    if (typeof calculateEmissions === 'function') {
        calculateEmissions();
        console.log('✅ Calcul d\'émissions relancé');
    }
    
    // 5. Vérifier les résultats
    setTimeout(() => {
        const emisKg = document.querySelector('[data-emis-kg]');
        const emisTkm = document.querySelector('[data-emis-tkm]');
        
        if (emisKg) console.log('📊 Émissions kg:', emisKg.textContent);
        if (emisTkm) console.log('📊 Émissions t.km:', emisTkm.textContent);
    }, 1000);
    
    console.log('✅ Correction de la page customer terminée');
    return true;
}

// Exécuter automatiquement
console.log('🚀 Script de correction customer chargé');
console.log('💡 Exécutez fixCustomerPage() dans la console pour corriger la page');

// Auto-exécution si on est sur la page customer
if (window.location.pathname.includes('customer') || window.location.pathname.includes('mes_transports')) {
    setTimeout(fixCustomerPage, 2000); // Attendre 2 secondes que la page soit chargée
}
'''
    
    with open('fix_customer.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de correction customer créé : fix_customer.js")

def create_api_test_script():
    """Créer un script pour tester l'API transports"""
    
    script_content = '''
// Script pour tester l'API transports
async function testApiTransports() {
    console.log('🧪 Test de l\'API transports');
    
    try {
        const response = await fetch('/api/transports');
        console.log('📡 Réponse API:', response.status, response.statusText);
        
        if (response.ok) {
            const data = await response.json();
            console.log('📊 Données reçues:', data);
            
            if (data.success && data.transports) {
                console.log(`✅ ${data.transports.length} transports chargés`);
                
                // Afficher le premier transport
                if (data.transports.length > 0) {
                    const transport = data.transports[0];
                    console.log('📋 Premier transport:', transport);
                }
            } else {
                console.warn('⚠️ Format de données inattendu:', data);
            }
        } else {
            console.error('❌ Erreur API:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('❌ Erreur de connexion:', error);
    }
}

// Exécuter le test
testApiTransports();
'''
    
    with open('test_api.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de test API créé : test_api.js")

if __name__ == "__main__":
    print("🔧 Création des scripts de correction")
    print("=" * 50)
    
    create_customer_fix_script()
    create_api_test_script()
    
    print("\n📋 Instructions :")
    print("1. Ouvrez la page customer sur Render")
    print("2. Ouvrez la console du navigateur (F12)")
    print("3. Copiez-collez le contenu de fix_customer.js")
    print("4. Exécutez fixCustomerPage()")
    print("5. Vérifiez que les calculs d'émissions fonctionnent")
