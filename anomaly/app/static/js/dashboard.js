/* Dashboard */

let dashboardRefreshInterval;

document.addEventListener('DOMContentLoaded', async () => {
    // Charger les données du dashboard au démarrage
    await loadDashboardData();
    
    // Refresh automatique toutes les 10 secondes
    dashboardRefreshInterval = setInterval(loadDashboardData, 10000);
});

async function loadDashboardData() {
    try {
        const response = await fetchAPI('/dashboard-data');
        
        if (!response.success) {
            console.error('Erreur:', response.error);
            return;
        }
        
        const data = response.data;
        
        // Mettre à jour la dernière mise à jour
        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            const now = new Date();
            lastUpdated.textContent = `Last updated: ${now.toLocaleTimeString('fr-FR')}`;
        }
        
        // Afficher les slices
        displaySlices(data.slices);
        
        // Afficher les alertes
        displayAlerts(data.alerts);
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
    }
}

function displaySlices(slices) {
    const container = document.getElementById('slicesContainer');
    
    if (!slices || slices.length === 0) {
        container.innerHTML = '<p class="loading-state">Pas de données</p>';
        return;
    }
    
    container.innerHTML = slices.map(slice => `
        <div class="slice-card ${slice.status === 'DEGRADED' ? 'degraded' : ''}">
            <div class="slice-header">
                <div>
                    <div class="slice-name">${slice.slice_id}</div>
                    <div class="slice-ue-count">UE Count: ${slice.total_detections}</div>
                </div>
                <span class="slice-badge ${slice.status === 'ACTIVE' ? 'badge-active' : 'badge-degraded'}">
                    ${slice.status}
                </span>
            </div>
            <div class="slice-metrics">
                <div class="metric">
                    <div class="metric-label">Bandwidth</div>
                    <div class="metric-value">${formatNumber(slice.bandwidth, 1)} Mbps</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Latency</div>
                    <div class="metric-value">${formatNumber(slice.latency, 1)} ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Jitter</div>
                    <div class="metric-value">${formatNumber(slice.jitter, 1)} ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Packet Loss</div>
                    <div class="metric-value">${formatNumber(slice.packet_loss, 2)}%</div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="no-alerts">No active alerts</p>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.level === 'CRITICAL' ? 'critical' : ''}">
            <strong>${alert.level}</strong> - ${alert.message}
        </div>
    `).join('');
}

// Nettoyer l'intervalle quand la page se ferme
window.addEventListener('beforeunload', () => {
    if (dashboardRefreshInterval) {
        clearInterval(dashboardRefreshInterval);
    }
});
