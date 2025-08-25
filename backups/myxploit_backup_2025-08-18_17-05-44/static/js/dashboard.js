// Dashboard JavaScript - Gestion des graphiques et données
(function() {
    'use strict';
    
    // Variables globales pour les données du dashboard
    let emissionsData = {};
    let clientsData = {};
    
    // Initialisation des données
    function initializeDashboardData(emissions, clients) {
        try {
            emissionsData = emissions || {};
            clientsData = clients || {};
            createCharts();
        } catch (error) {
            console.error('Erreur lors de l\'initialisation du dashboard:', error);
        }
    }
    
    // Création des graphiques
    function createCharts() {
        try {
            createEmissionsChart();
            createClientsChart();
            createActivityChart();
        } catch (error) {
            console.error('Erreur lors de la création des graphiques:', error);
        }
    }
    
    // Graphique Émissions
    function createEmissionsChart() {
        const emissionsCtx = document.getElementById('emissionsChart');
        if (!emissionsCtx) {
            console.warn('Élément emissionsChart non trouvé');
            return;
        }
        
        try {
            const ctx = emissionsCtx.getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Total', 'Ce mois', 'Cette semaine'],
                    datasets: [{
                        data: [
                            emissionsData.total || 0,
                            emissionsData.monthly || 0,
                            emissionsData.weekly || 0
                        ],
                        backgroundColor: ['#667eea', '#38a169', '#ed8936'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Erreur lors de la création du graphique émissions:', error);
        }
    }
    
    // Graphique Clients
    function createClientsChart() {
        const clientsCtx = document.getElementById('clientsChart');
        if (!clientsCtx) {
            console.warn('Élément clientsChart non trouvé');
            return;
        }
        
        try {
            const ctx = clientsCtx.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: clientsData.labels || [],
                    datasets: [{
                        label: 'Émissions CO₂e (kg)',
                        data: clientsData.values || [],
                        backgroundColor: '#667eea',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#e2e8f0'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Erreur lors de la création du graphique clients:', error);
        }
    }
    
    // Graphique Activité (simulation de données sur 7 jours)
    function createActivityChart() {
        const activityCtx = document.getElementById('activityChart');
        if (!activityCtx) {
            console.warn('Élément activityChart non trouvé');
            return;
        }
        
        try {
            const ctx = activityCtx.getContext('2d');
            const activityData = [12, 19, 15, 25, 22, 30, 28]; // Données simulées
            const activityLabels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
    
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: activityLabels,
                    datasets: [{
                        label: 'Transports',
                        data: activityData,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#e2e8f0'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Erreur lors de la création du graphique activité:', error);
        }
    }
    
    // Fonction publique pour l'initialisation
    window.initializeDashboardData = initializeDashboardData;
    
    // Initialisation au chargement de la page
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Dashboard JavaScript chargé avec succès');
        
        // Vérifier si Chart.js est disponible
        if (typeof Chart === 'undefined') {
            console.error('Chart.js n\'est pas chargé');
            return;
        }
        
        // Attendre un peu que les éléments DOM soient prêts
        setTimeout(function() {
            const emissionsDataElement = document.getElementById('emissions-data');
            const clientsDataElement = document.getElementById('clients-data');
            
            if (emissionsDataElement && clientsDataElement) {
                try {
                    const emissionsData = JSON.parse(emissionsDataElement.textContent);
                    const clientsData = JSON.parse(clientsDataElement.textContent);
                    initializeDashboardData(emissionsData, clientsData);
                } catch (error) {
                    console.error('Erreur lors du parsing des données:', error);
                }
            } else {
                console.warn('Éléments de données non trouvés, initialisation différée');
            }
        }, 100);
    });
    
})();
