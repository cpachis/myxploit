// Variables globales injectées par Jinja2
let energiesData = {};
let transportPoids = 1;
let vehiculeFacteurEmissions = 0; // Facteur d'émission du véhicule en g CO2e/t.km

// Initialisation des données
function initializeData(energies, poids, facteurVehicule) {
    energiesData = energies;
    transportPoids = poids;
    vehiculeFacteurEmissions = facteurVehicule || 0;
    console.log('Données initialisées:', { energies, poids, facteurVehicule });
}

// --- Calcul dynamique des émissions pour toutes les phases ---
function recalcPhaseEmissions(tr) {
    const energie = tr.querySelector('.edit-phase-energie').value;
    const conso = parseFloat(tr.querySelector('.edit-phase-conso').value) || 0;
    const dist = parseFloat(tr.querySelector('.edit-phase-distance').value) || 0;
    const poids = transportPoids;
    
    // Récupérer le facteur d'émission de l'énergie
    const energieData = energiesData[energie];
    if (!energieData) {
        console.warn('Énergie non trouvée:', energie);
        return;
    }
    
    const facteurEnergie = energieData.facteur || 0;
    
    // Calcul des émissions selon le type d'énergie
    let emisKg = 0;
    if (energieData.unite && energieData.unite.toLowerCase().includes('l')) {
        // Énergie en litres (gazole, essence, etc.)
        const litres = conso * dist / 100;
        emisKg = facteurEnergie * litres;
    } else if (energieData.unite && energieData.unite.toLowerCase().includes('kg')) {
        // Énergie en kg (GPL, etc.)
        const kg = conso * dist / 100;
        emisKg = facteurEnergie * kg;
    } else if (energieData.unite && energieData.unite.toLowerCase().includes('kwh')) {
        // Énergie en kWh (électrique)
        const kwh = conso * dist / 100;
        emisKg = facteurEnergie * kwh;
    } else {
        // Facteur direct
        emisKg = facteurEnergie * conso * dist / 100;
    }
    
    // NOUVELLE FORMULE : Utiliser le facteur d'émission du véhicule
    let emisTkm;
    if (vehiculeFacteurEmissions > 0) {
        // Si on a le facteur du véhicule, l'utiliser directement
        emisTkm = vehiculeFacteurEmissions;
        console.log('Utilisation du facteur du véhicule:', vehiculeFacteurEmissions, 'g CO2e/t.km');
    } else {
        // Sinon, calculer à partir des émissions totales (méthode de secours)
        emisTkm = (poids * dist) > 0 ? emisKg / (poids * dist) : 0;
        console.log('Calcul du facteur à partir des émissions totales:', emisTkm, 'g CO2e/t.km');
    }
    
    // Mise à jour des cellules d'émissions
    tr.querySelector('.emis-kg').textContent = emisKg.toFixed(2);
    tr.querySelector('.emis-tkm').textContent = emisTkm.toFixed(3);
    
    console.log('Émissions recalculées:', { 
        energie, 
        conso, 
        dist, 
        poids, 
        facteurEnergie, 
        vehiculeFacteurEmissions,
        emisKg, 
        emisTkm 
    });
}

function highlightRow(tr) {
    tr.classList.add('highlight-row');
    // La surbrillance reste jusqu'à l'enregistrement
}

function addPhaseListeners(tr) {
    // Écouteurs pour la consommation
    tr.querySelector('.edit-phase-conso').addEventListener('input', function() { 
        recalcPhaseEmissions(tr); 
        highlightRow(tr); 
    });
    
    // Écouteurs pour la distance
    tr.querySelector('.edit-phase-distance').addEventListener('input', function() { 
        recalcPhaseEmissions(tr); 
        highlightRow(tr); 
    });
    
    // Écouteurs pour l'énergie
    tr.querySelector('.edit-phase-energie').addEventListener('change', function() { 
        recalcPhaseEmissions(tr); 
        highlightRow(tr); 
    });
    
    // Écouteurs pour le type de phase
    tr.querySelector('.edit-phase-type').addEventListener('change', function() { 
        highlightRow(tr); 
    });
    
    // Écouteurs pour la date
    tr.querySelector('.edit-phase-date').addEventListener('change', function() { 
        sortPhasesByDate(); 
        highlightRow(tr); 
    });
    
    // Écouteurs pour les villes
    tr.querySelector('.edit-phase-ville-depart').addEventListener('input', function() { 
        highlightRow(tr); 
    });
    
    tr.querySelector('.edit-phase-ville-arrivee').addEventListener('input', function() { 
        highlightRow(tr); 
    });
}

// --- Suppression de phase ---
function removePhase(tr) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette phase ?')) {
        tr.remove();
        
        // Vérifier s'il reste des phases
        const tbody = document.querySelector('#phases-table-edit tbody');
        if (tbody && tbody.querySelectorAll('.phase-row').length === 0) {
            tbody.innerHTML = '<tr class="no-phases"><td colspan="10" style="text-align: center; color: #888; font-style: italic;">Aucune phase définie. Cliquez sur "Ajouter une phase" pour commencer.</td></tr>';
        }
        
        console.log('Phase supprimée');
    }
}

// --- Ajout dynamique de phase ---
function addNewPhase() {
    const table = document.getElementById('phases-table-edit');
    if (!table) {
        console.error('Tableau des phases non trouvé');
        return;
    }
    
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error('Tbody non trouvé');
        return;
    }
    
    // Supprimer le message "aucune phase" s'il existe
    const noPhases = tbody.querySelector('.no-phases');
    if (noPhases) {
        noPhases.remove();
    }
    
    // Générer les options d'énergies
    const energieOptions = Object.entries(energiesData).map(([e_id, e]) => {
        const unite = e.unite || '';
        return `<option value="${e_id}">${e.nom} (${e.facteur} ${unite})</option>`;
    }).join('');
    
    // Date du jour par défaut
    const today = new Date().toISOString().split('T')[0];
    
    // Créer la nouvelle ligne
    const tr = document.createElement('tr');
    tr.className = 'phase-row';
    tr.setAttribute('data-index', Date.now()); // Index unique
    
    tr.innerHTML = `
        <td>
            <select class="edit-phase-type">
                <option value="collecte">collecte</option>
                <option value="traction">traction</option>
                <option value="distribution">distribution</option>
            </select>
        </td>
        <td>
            <select class="edit-phase-energie">${energieOptions}</select>
        </td>
        <td><input type="text" class="edit-phase-ville-depart" placeholder="Ville départ" value=""></td>
        <td><input type="text" class="edit-phase-ville-arrivee" placeholder="Ville arrivée" value=""></td>
        <td><input type="number" step="0.01" class="edit-phase-conso" value="0.00" min="0"></td>
        <td><input type="number" step="0.01" class="edit-phase-distance" value="0.00" min="0"></td>
        <td><input type="date" class="edit-phase-date" value="${today}"></td>
        <td class="emis-kg">0.00</td>
        <td class="emis-tkm">0.000</td>
        <td>
            <button type="button" class="btn-remove-phase" onclick="removePhase(this.closest('tr'))" title="Supprimer cette phase">🗑️</button>
        </td>
    `;
    
    tbody.appendChild(tr);
    
    // Ajouter les écouteurs d'événements
    addPhaseListeners(tr);
    
    // Recalculer les émissions pour la nouvelle phase
    setTimeout(() => {
        recalcPhaseEmissions(tr);
    }, 100);
    
    console.log('Nouvelle phase ajoutée');
}

// --- Tri des phases par date (ordre croissant) ---
function sortPhasesByDate() {
    const tbody = document.getElementById('phases-table-edit').querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('.phase-row'));
    if (rows.length === 0) return;
    
    rows.sort((a, b) => {
        const da = a.querySelector('.edit-phase-date').value || '';
        const db = b.querySelector('.edit-phase-date').value || '';
        return da.localeCompare(db);
    });
    
    // Réorganiser les lignes dans le DOM
    rows.forEach(tr => tbody.appendChild(tr));
    console.log('Phases triées par date');
}

// --- Validation des phases avant enregistrement ---
function validatePhases() {
    const rows = document.querySelectorAll('#phases-table-edit tbody .phase-row');
    let hasErrors = false;
    let errorMessages = [];
    
    if (rows.length === 0) {
        errorMessages.push('Aucune phase à enregistrer');
        hasErrors = true;
    }
    
    rows.forEach((tr, index) => {
        const type = tr.querySelector('.edit-phase-type').value;
        const energie = tr.querySelector('.edit-phase-energie').value;
        const villeDepart = tr.querySelector('.edit-phase-ville-depart').value.trim();
        const villeArrivee = tr.querySelector('.edit-phase-ville-arrivee').value.trim();
        const conso = tr.querySelector('.edit-phase-conso').value;
        const distance = tr.querySelector('.edit-phase-distance').value;
        const date = tr.querySelector('.edit-phase-date').value;
        
        // Validation des données
        if (!type || !energie || !villeDepart || !villeArrivee || !conso || !distance || !date) {
            errorMessages.push(`Phase ${index + 1}: Données manquantes`);
            hasErrors = true;
            tr.style.border = '2px solid #ff4444';
        } else {
            // Retirer la bordure d'erreur
            tr.style.border = '';
        }
        
        // Validation des valeurs numériques
        if (parseFloat(conso) < 0 || parseFloat(distance) < 0) {
            errorMessages.push(`Phase ${index + 1}: Valeurs négatives non autorisées`);
            hasErrors = true;
            tr.style.border = '2px solid #ff4444';
        }
    });
    
    if (hasErrors) {
        alert('Erreurs de validation:\n' + errorMessages.join('\n'));
        return false;
    }
    
    return true;
}

// --- Collecte des données des phases ---
function collectPhasesData() {
    const rows = document.querySelectorAll('#phases-table-edit tbody .phase-row');
    const phases = [];
    
    rows.forEach((tr, index) => {
        const phase = {
            type: tr.querySelector('.edit-phase-type').value,
            energie: tr.querySelector('.edit-phase-energie').value,
            ville_depart: tr.querySelector('.edit-phase-ville-depart').value.trim(),
            ville_arrivee: tr.querySelector('.edit-phase-ville-arrivee').value.trim(),
            conso: parseFloat(tr.querySelector('.edit-phase-conso').value) || 0,
            distance: parseFloat(tr.querySelector('.edit-phase-distance').value) || 0,
            date: tr.querySelector('.edit-phase-date').value,
            emis_kg: parseFloat(tr.querySelector('.emis-kg').textContent.replace(',', '.')) || 0,
            emis_tkm: parseFloat(tr.querySelector('.emis-tkm').textContent.replace(',', '.')) || 0
        };
        phases.push(phase);
        
        // Retirer la surbrillance après enregistrement
        tr.classList.remove('highlight-row');
    });
    
    return phases;
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM chargé, initialisation des phases...');
    
    // Vérifier que les données sont bien chargées
    console.log('Énergies disponibles:', energiesData);
    console.log('Poids du transport:', transportPoids);
    
    // Initialiser les listeners sur les lignes existantes
    document.querySelectorAll('#phases-table-edit tbody .phase-row').forEach(tr => {
        addPhaseListeners(tr);
    });

    // Bouton d'ajout de phase
    const addButton = document.getElementById('btn-add-phase');
    console.log('Bouton trouvé:', addButton);
    console.log('ID du bouton:', addButton ? addButton.id : 'non trouvé');
    
    if (addButton) {
        addButton.addEventListener('click', function(e) {
            console.log('Clic sur le bouton d\'ajout de phase');
            e.preventDefault();
            addNewPhase();
        });
        console.log('Event listener ajouté sur le bouton d\'ajout de phase');
    } else {
        console.log('Bouton d\'ajout de phase non trouvé');
        // Vérifier si le bouton existe dans le DOM
        const allButtons = document.querySelectorAll('button');
        console.log('Tous les boutons trouvés:', allButtons);
        allButtons.forEach(btn => {
            console.log('Bouton:', btn.id, btn.textContent, btn.className);
        });
    }

    // Tri initial au chargement
    sortPhasesByDate();

    // Gestion du formulaire
    const form = document.getElementById('edit-phases-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Empêcher la soumission par défaut
            
            console.log('Soumission du formulaire des phases');
            
            // Validation des phases
            if (!validatePhases()) {
                return;
            }
            
            // Collecter les données des phases
            const phases = collectPhasesData();
            console.log('Phases à enregistrer:', phases);
            
            // Mettre à jour le champ caché avec les données des phases
            document.getElementById('phases_edit_input').value = JSON.stringify(phases);
            
            // Soumettre le formulaire
            this.submit();
        });
        console.log('Event listener ajouté sur le formulaire des phases');
    } else {
        console.log('Formulaire des phases non trouvé');
    }
    
    console.log('Initialisation des phases terminée');
});

// Fonctions utilitaires pour la compatibilité
function editCell(td) {
    if(td.querySelector('input')) return;
    const field = td.dataset.field;
    const oldValue = td.textContent.trim();
    let input;
    if(field === 'date') {
        input = document.createElement('input');
        input.type = 'date';
        input.value = toISODate(oldValue);
    } else {
        input = document.createElement('input');
        input.type = 'number';
        input.step = '0.01';
        input.value = oldValue.replace(',', '.');
    }
    input.onblur = function() {
        td.textContent = (field === 'date') ? formatDateFr(input.value) : input.value;
    };
    input.onkeydown = function(e) {
        if(e.key === 'Enter') input.blur();
    };
    td.textContent = '';
    td.appendChild(input);
    input.focus();
}

function toISODate(frDate) {
    // Convertit '13 Juillet 2025' en '2025-07-13' si possible
    const mois = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
    const m = frDate.toLowerCase().match(/(\d{1,2})\s+([a-zéû]+)\s+(\d{4})/);
    if(m) {
        let month = mois.indexOf(m[2])+1;
        return `${m[3]}-${month.toString().padStart(2,'0')}-${m[1].toString().padStart(2,'0')}`;
    }
    return '';
}

function formatDateFr(iso) {
    if(!iso) return '';
    const d = new Date(iso);
    const mois = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'];
    return `${d.getDate()} ${mois[d.getMonth()]} ${d.getFullYear()}`;
}
