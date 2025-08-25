console.log('Script phases simple chargé');

// Variable globale pour le facteur d'émission du véhicule
let vehiculeFacteurEmissions = 0;

// Fonction pour définir le facteur d'émission du véhicule
window.setVehiculeFacteur = function(facteur) {
  vehiculeFacteurEmissions = parseFloat(facteur) || 0;
  console.log('Facteur d\'émission du véhicule défini:', vehiculeFacteurEmissions, 'g CO2e/t.km');
};

function addPhase() {
  console.log('addPhase appelée');
  
  var table = document.getElementById('phases-table');
  if (!table) {
    console.error('Table non trouvé');
    return;
  }
  
  var tbody = table.querySelector('tbody');
  if (!tbody) {
    console.error('Tbody non trouvé');
    return;
  }
  
  var noPhases = tbody.querySelector('.no-phases');
  if (noPhases) {
    noPhases.remove();
  }
  
  var today = new Date();
  var year = today.getFullYear();
  var month = String(today.getMonth() + 1).padStart(2, '0');
  var day = String(today.getDate()).padStart(2, '0');
  var todayStr = year + '-' + month + '-' + day;
  
  var newRow = document.createElement('tr');
  newRow.className = 'phase-row';
  
  var html = '';
  html += '<td><select class="phase-type"><option value="collecte">collecte</option><option value="traction">traction</option><option value="distribution">distribution</option></select></td>';
  html += '<td><select class="phase-energie"><option value="gazole">Gazole (3.17 kg/L)</option></select></td>';
  html += '<td><input type="text" class="phase-ville-depart" placeholder="Ville départ" value=""></td>';
  html += '<td><input type="text" class="phase-ville-arrivee" placeholder="Ville arrivée" value=""></td>';
  html += '<td><input type="number" step="0.01" class="phase-conso" value="0.00" min="0"></td>';
  html += '<td><input type="number" step="0.01" class="phase-distance" value="0.00" min="0"></td>';
  html += '<td><input type="date" class="phase-date" value="' + todayStr + '"></td>';
  html += '<td class="emis-kg">0.00</td>';
  html += '<td class="emis-tkm">0.000</td>';
  html += '<td><button type="button" class="btn-delete">🗑️</button></td>';
  
  newRow.innerHTML = html;
  tbody.appendChild(newRow);
  
  console.log('Phase ajoutée');
}

function deletePhase(button) {
  var row = button.closest('tr');
  if (row) {
    row.remove();
    
    var tbody = document.querySelector('#phases-table tbody');
    if (tbody && tbody.querySelectorAll('.phase-row').length === 0) {
      tbody.innerHTML = '<tr class="no-phases"><td colspan="11" style="text-align: center; color: #888; font-style: italic;">Aucune phase définie. Cliquez sur "Ajouter une phase" pour commencer.</td></tr>';
    }
  }
}

function savePhases(event) {
  console.log('savePhases appelée');
  
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  var form = document.getElementById('phases-form');
  if (!form) {
    console.error('Formulaire non trouvé');
    return false;
  }
  
  var transportRef = form.dataset.transportRef;
  if (!transportRef) {
    console.error('Référence transport non trouvée');
    return false;
  }
  
  var phases = [];
  var rows = document.querySelectorAll('.phase-row');
  
  if (rows.length === 0) {
    alert('Aucune phase à sauvegarder');
    return false;
  }
  
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    var phase = {
      type: row.querySelector('.phase-type').value,
      energie: row.querySelector('.phase-energie').value,
      ville_depart: row.querySelector('.phase-ville-depart').value,
      ville_arrivee: row.querySelector('.phase-ville-arrivee').value,
      conso: parseFloat(row.querySelector('.phase-conso').value) || 0,
      distance: parseFloat(row.querySelector('.phase-distance').value) || 0,
      date: row.querySelector('.phase-date').value,
      emis_kg: 0,
      emis_tkm: 0
    };
    phases.push(phase);
  }
  
  console.log('Phases à sauvegarder:', phases);
  
  fetch('/api/transport/' + transportRef + '/phases', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({phases: phases})
  })
  .then(function(response) {
    console.log('Réponse reçue:', response);
    if (!response.ok) {
      throw new Error('HTTP error! status: ' + response.status);
    }
    return response.json();
  })
  .then(function(data) {
    console.log('Données reçues:', data);
    if (data.success) {
      alert('Phases enregistrées avec succès !');
    } else {
      alert('Erreur lors de l\'enregistrement : ' + (data.error || 'Erreur inconnue'));
    }
  })
  .catch(function(error) {
    console.error('Erreur lors de l\'enregistrement:', error);
    alert('Erreur lors de l\'enregistrement : ' + error.message);
  });
  
  return false;
}

console.log('Script phases simple terminé');
