
// Script pour tester l'API transports
async function testApiTransports() {
    console.log('🧪 Test de l'API transports');
    
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
