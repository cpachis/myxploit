// Gestion des phases de transport
console.log('Script des phases chargé');

// Variable globale pour le facteur d'émission du véhicule
let vehiculeFacteurEmissions = 0;

// Attendre que le script soit complètement chargé
setTimeout(() => {
  console.log('=== VÉRIFICATION DES FONCTIONS ===');
  console.log('addPhase disponible:', typeof window.addPhase);
  console.log('deletePhase disponible:', typeof window.deletePhase);
  console.log('Script complètement initialisé');
}, 100);

// Empêcher la fermeture de la modal lors des clics sur les éléments du formulaire
document.addEventListener('click', function(event) {
  console.log('=== CLIC DÉTECTÉ ===', event.target.tagName, event.target.className, event.target.id);
  
  // Si on clique sur un élément du formulaire des phases, empêcher la fermeture
  if (event.target.closest('#phases-form') || event.target.closest('.btn-save') || event.target.closest('.btn-add-phase')) {
    console.log('Clic sur élément du formulaire - propagation arrêtée');
    event.stopPropagation();
    event.preventDefault();
    return false;
  }
  
  // Si on clique sur le bouton de sauvegarde spécifiquement
  if (event.target.classList.contains('btn-save')) {
    console.log('Bouton de sauvegarde cliqué - traitement spécial');
    event.stopPropagation();
    event.preventDefault();
    savePhases(event);
    return false;
  }
});

// Empêcher TOUS les événements de soumission
document.addEventListener('submit', function(event) {
  console.log('=== ÉVÉNEMENT SUBMIT DÉTECTÉ ===', event.target.id);
  
  if (event.target && event.target.id === 'phases-form') {
    console.log('Soumission du formulaire des phases interceptée');
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    savePhases(event);
    return false;
  }
});

// Charger les données d'énergie depuis l'API
fetch('/api/energies')
  .then(response => response.json())
  .then(data => {
    window.energiesData = data;
    console.log('Données d\'énergie chargées depuis l\'API:', window.energiesData);
  })
  .catch(error => {
    console.error('Erreur lors du chargement des énergies:', error);
    window.energiesData = {};
  });

// Fonction pour ajouter une phase - RENDUE GLOBALE
window.addPhase = function() {
  console.log('=== FONCTION addPhase APPELÉE ===');
  
  const phasesTable = document.getElementById('phases-table');
  if (!phasesTable) {
    console.error('Tableau des phases non trouvé');
    return;
  }
  
  const tbody = phasesTable.querySelector('tbody');
  if (!tbody) {
    console.error('Tbody du tableau des phases non trouvé');
    return;
  }
  
  const noPhasesRow = tbody.querySelector('.no-phases');
  if (noPhasesRow) {
    noPhasesRow.remove();
  }
  
  // Date du jour par défaut - formatage plus robuste
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  const todayFormatted = `${year}-${month}-${day}`;
  
  console.log('Date du jour formatée:', todayFormatted);
  
  const newRow = document.createElement('tr');
  newRow.className = 'phase-row';
  
  newRow.innerHTML = `
    <td>
      <select class="phase-type">
        <option value="collecte">collecte</option>
        <option value="traction">traction</option>
        <option value="distribution">distribution</option>
      </select>
    </td>
    <td>
      <select class="phase-energie">
        <option value="gazole">Gazole (3.17 kg/L)</option>
      </select>
    </td>
    <td><input type="text" class="phase-ville-depart" placeholder="Ville départ" value=""></td>
    <td><input type="text" class="phase-ville-arrivee" placeholder="Ville arrivée" value=""></td>
    <td><input type="number" step="0.01" class="phase-conso" value="0.00" min="0"></td>
    <td><input type="number" step="0.01" class="phase-distance" value="0.00" min="0"></td>
    <td><input type="date" class="phase-date" value="${todayFormatted}"></td>
    <td class="emis-kg">0.00</td>
    <td class="emis-tkm">0.000</td>
    <td><button type="button" class="btn-delete">🗑️</button></td>
  `;
  
  tbody.appendChild(newRow);
  
  // Mettre à jour les options d'énergie si les données sont disponibles
  if (window.energiesData && Object.keys(window.energiesData).length > 0) {
    updateEnergieOptions(newRow);
  }
  
  // Ajouter les listeners après avoir mis à jour les options
  addPhaseListeners(newRow);
  
  // Recalculer les émissions pour la nouvelle phase
  setTimeout(() => {
    recalcPhaseEmissions(newRow);
  }, 100);
  
  console.log('Nouvelle phase ajoutée avec succès');
};

// Fonction pour mettre à jour les options d'énergie
function updateEnergieOptions(row) {
  const energieSelect = row.querySelector('.phase-energie');
  if (!energieSelect || !window.energiesData) return;
  
  energieSelect.innerHTML = '';
  for (const [energieId, energieData] of Object.entries(window.energiesData)) {
    const nom = energieData.nom || energieId;
    const facteur = energieData.facteur || '0';
    const unite = energieData.unite || energieData.unit || '';
    
    let displayText;
    if (unite.toLowerCase().includes('l') || unite.toLowerCase().includes('litre')) {
      displayText = `${nom} (${facteur} kg/L)`;
    } else if (unite.toLowerCase().includes('kg') || unite.toLowerCase().includes('kilo')) {
      displayText = `${nom} (${facteur} kg/kg)`;
    } else if (unite.toLowerCase().includes('kwh')) {
      displayText = `${nom} (${facteur} kg/kWh)`;
    } else {
      displayText = `${nom} (${facteur})`;
    }
    
    const selected = energieId === 'gazole' ? 'selected' : '';
    energieSelect.innerHTML += `<option value="${energieId}" ${selected}>${displayText}</option>`;
  }
}

// Fonction pour supprimer une phase - RENDUE GLOBALE
window.deletePhase = function(button) {
  const row = button.closest('tr');
  if (row) {
    row.remove();
    
    const tbody = document.querySelector('#phases-table tbody');
         if (tbody && tbody.querySelectorAll('.phase-row').length === 0) {
       tbody.innerHTML = `
         <tr class="no-phases">
           <td colspan="11" style="text-align: center; color: #888; font-style: italic;">
             Aucune phase définie. Cliquez sur "Ajouter une phase" pour commencer.
           </td>
         </tr>
       `;
     }
  }
};

// Fonction pour ajouter les event listeners à une ligne
function addPhaseListeners(row) {
  const consoInput = row.querySelector('.phase-conso');
  const distanceInput = row.querySelector('.phase-distance');
  const typeSelect = row.querySelector('.phase-type');
  const energieSelect = row.querySelector('.phase-energie');
  const deleteButton = row.querySelector('.btn-delete');
  
  if (consoInput) {
    consoInput.addEventListener('input', function() { recalcPhaseEmissions(row); });
  }
  if (distanceInput) {
    distanceInput.addEventListener('input', function() { recalcPhaseEmissions(row); });
  }
  if (typeSelect) {
    typeSelect.addEventListener('change', function() { recalcPhaseEmissions(row); });
  }
  if (energieSelect) {
    energieSelect.addEventListener('change', function() { recalcPhaseEmissions(row); });
  }
  if (deleteButton) {
    deleteButton.addEventListener('click', function() { deletePhase(this); });
  }
}

// Fonction pour recalculer les émissions
function recalcPhaseEmissions(row) {
  const conso = parseFloat(row.querySelector('.phase-conso').value) || 0;
  const dist = parseFloat(row.querySelector('.phase-distance').value) || 0;
  const energie = row.querySelector('.phase-energie').value;
  
  let facteur = 2.6;
  if (window.energiesData && window.energiesData[energie]) {
    facteur = parseFloat(window.energiesData[energie].facteur) || 2.6;
  }
  
  const litres = conso * dist / 100;
  const emisKg = facteur * litres;
  
  // NOUVELLE FORMULE : Utiliser le facteur du véhicule si disponible
  let emisTkm;
  if (vehiculeFacteurEmissions > 0) {
    // Si on a le facteur du véhicule, l'utiliser directement
    emisTkm = vehiculeFacteurEmissions;
    console.log('Utilisation du facteur du véhicule:', vehiculeFacteurEmissions, 'g CO2e/t.km');
  } else {
    // Sinon, calculer à partir des émissions totales (méthode de secours)
    emisTkm = dist > 0 ? emisKg / dist : 0;
    console.log('Calcul du facteur à partir des émissions totales:', emisTkm, 'g CO2e/t.km');
  }
  
  const emisKgCell = row.querySelector('.emis-kg');
  const emisTkmCell = row.querySelector('.emis-tkm');
  
  if (emisKgCell) emisKgCell.textContent = emisKg.toFixed(2);
  if (emisTkmCell) emisTkmCell.textContent = emisTkm.toFixed(3);
  
  row.classList.add('highlight-row');
}

// Fonction pour sauvegarder les phases
function savePhases(event) {
  console.log('=== FONCTION savePhases APPELÉE ===');
  
  // Empêcher le comportement par défaut du formulaire
  if (event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Événement intercepté et arrêté');
  }
  
  console.log('=== DÉBUT DE LA SAUVEGARDE ===');
  
  const form = document.getElementById('phases-form');
  if (!form) {
    console.error('Formulaire des phases non trouvé');
    return false; // Empêcher la soumission
  }
  
  const transportRef = form.dataset.transportRef;
  if (!transportRef) {
    console.error('Référence du transport non trouvée');
    return false; // Empêcher la soumission
  }
  
  const phases = [];
  const rows = document.querySelectorAll('.phase-row');
  
  if (rows.length === 0) {
    alert('Aucune phase à sauvegarder. Ajoutez d\'abord une phase.');
    return false; // Empêcher la soumission
  }
  
  rows.forEach(function(row, index) {
    const phase = {
      type: row.querySelector('.phase-type').value,
      energie: row.querySelector('.phase-energie').value,
      ville_depart: row.querySelector('.phase-ville-depart').value,
      ville_arrivee: row.querySelector('.phase-ville-arrivee').value,
      conso: parseFloat(row.querySelector('.phase-conso').value) || 0,
      distance: parseFloat(row.querySelector('.phase-distance').value) || 0,
      date: row.querySelector('.phase-date').value,
      emis_kg: parseFloat(row.querySelector('.emis-kg').textContent) || 0,
      emis_tkm: parseFloat(row.querySelector('.emis-tkm').textContent) || 0
    };
    phases.push(phase);
  });
  
  console.log('Phases à sauvegarder:', phases);
  
  // Désactiver le bouton pendant la sauvegarde
  const saveButton = document.querySelector('.btn-save');
  if (saveButton) {
    saveButton.disabled = true;
    saveButton.textContent = 'Sauvegarde en cours...';
  }
  
  fetch(`/api/transport/${transportRef}/phases`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({phases: phases})
  })
  .then(function(response) { 
    console.log('Réponse reçue:', response);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json(); 
  })
  .then(function(data) {
    console.log('Données reçues:', data);
    if (data.success) {
      alert('Phases enregistrées avec succès !');
      rows.forEach(function(row) { 
        row.classList.remove('highlight-row'); 
      });
    } else {
      alert('Erreur lors de l\'enregistrement : ' + (data.error || 'Erreur inconnue'));
    }
  })
  .catch(function(error) {
    console.error('Erreur lors de l\'enregistrement:', error);
    alert('Erreur lors de l\'enregistrement : ' + error.message);
  })
  .finally(function() {
    // Réactiver le bouton
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.textContent = 'Enregistrer les phases';
    }
  });
  
  // Retourner false pour empêcher la soumission du formulaire
  return false;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM chargé, initialisation des phases...');
  initializePhases();
});

// Initialisation des phases quand le contenu est chargé dynamiquement
function initializePhases() {
  console.log('Initialisation des phases...');
  
  // Attendre un peu que le DOM soit prêt
  setTimeout(() => {
    const form = document.getElementById('phases-form');
    if (form) {
      console.log('Formulaire trouvé, ajout des event listeners');
      
      // Supprimer tous les event listeners existants
      const newForm = form.cloneNode(true);
      form.parentNode.replaceChild(newForm, form);
      
      // Ajouter le nouveau listener
      newForm.addEventListener('submit', function(e) {
        console.log('Événement submit intercepté');
        return savePhases(e);
      });
      
      // Ajouter les listeners sur les phases existantes
      const existingRows = document.querySelectorAll('.phase-row');
      existingRows.forEach(row => {
        addPhaseListeners(row);
      });
      
      console.log('Event listeners ajoutés avec succès');
    } else {
      console.log('Formulaire non trouvé, réessai dans 100ms...');
      setTimeout(initializePhases, 100);
    }
  }, 100);
}

// Observer les changements dans le DOM pour détecter quand la modal est chargée
const observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.type === 'childList') {
      mutation.addedNodes.forEach(function(node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Vérifier si une nouvelle phase a été ajoutée
          if (node.classList && node.classList.contains('phase-row')) {
            addPhaseListeners(node);
            console.log('Nouvelle phase détectée, listeners ajoutés');
          }
          
          // Vérifier si le formulaire des phases est maintenant présent
          if (node.id === 'phases-form' || node.querySelector('#phases-form')) {
            console.log('Formulaire des phases détecté, initialisation...');
            setTimeout(initializePhases, 50);
          }
        }
      });
    }
  });
});

// Démarrer l'observation
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Gestion du clic sur le bouton de sauvegarde et d'ajout de phase
document.addEventListener('click', function(event) {
  if (event.target && event.target.classList.contains('btn-save')) {
    console.log('Bouton de sauvegarde cliqué via fallback');
    event.preventDefault();
    event.stopPropagation();
    savePhases(event);
  }
  
  if (event.target && event.target.classList.contains('btn-add-phase')) {
    console.log('Bouton d\'ajout de phase cliqué via fallback');
    event.preventDefault();
    event.stopPropagation();
    addPhase();
  }
});

// Empêcher la fermeture de la modal lors de la soumission
document.addEventListener('submit', function(event) {
  if (event.target && event.target.id === 'phases-form') {
    console.log('Soumission du formulaire interceptée globalement');
    event.preventDefault();
    event.stopPropagation();
    savePhases(event);
  }
});

console.log('Script des phases chargé avec succès');
