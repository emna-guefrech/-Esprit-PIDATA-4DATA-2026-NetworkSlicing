/* Statistics Page */

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('statsLoadBtn')?.addEventListener('click', loadStatistics);
    
    // Charger les statistiques par défaut au démarrage
    loadStatistics();
});

async function loadStatistics() {
    try {
        const sliceId = document.getElementById('statsSliceId')?.value || '';
        const days = document.getElementById('statsDays')?.value || 7;
        
        const params = new URLSearchParams();
        if (sliceId) params.append('slice_id', sliceId);
        params.append('days', days);
        
        const response = await fetchAPI(`/anomaly/stats?${params.toString()}`);
        
        if (!response.success) {
            console.error('Erreur:', response.error);
            return;
        }
        
        const data = response.data;
        displayStatistics(data);
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
    }
}

function displayStatistics(data) {
    // Afficher les stats résumées
    document.getElementById('totalDetections').textContent = data.total_detections;
    document.getElementById('totalAnomalies').textContent = data.total_anomalies;
    document.getElementById('anomalyRate').textContent = `${formatNumber(data.anomaly_rate, 2)}%`;
    
    // Stats par slice
    const bySliceContainer = document.getElementById('bySliceContainer');
    if (data.by_slice && Object.keys(data.by_slice).length > 0) {
        bySliceContainer.innerHTML = Object.entries(data.by_slice).map(([slice, stats]) => `
            <div class="stat-card">
                <div class="stat-value">${stats.anomalies}</div>
                <div class="stat-label">${slice}</div>
                <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                    Taux: ${stats.rate}%
                </div>
            </div>
        `).join('');
    } else {
        bySliceContainer.innerHTML = '<p class="text-center">Pas de données</p>';
    }
    
    // Stats par méthode
    const byMethodContainer = document.getElementById('byMethodContainer');
    if (data.by_method && Object.keys(data.by_method).length > 0) {
        byMethodContainer.innerHTML = Object.entries(data.by_method).map(([method, count]) => `
            <div class="stat-card">
                <div class="stat-value">${count}</div>
                <div class="stat-label">${method === 'isolation_forest' ? 'Isolation Forest' : 'Autoencoder'}</div>
            </div>
        `).join('');
    } else {
        byMethodContainer.innerHTML = '<p class="text-center">Pas de données</p>';
    }
    
    // Chart par période
    if (data.by_period && data.by_period.length > 0) {
        drawPeriodChart(data.by_period);
    }
}

function drawPeriodChart(periodData) {
    const canvas = document.getElementById('periodChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const padding = 40;
    const width = canvas.width - 2 * padding;
    const height = canvas.height - 2 * padding;
    
    // Effacer le canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Données
    const maxValue = Math.max(...periodData.map(d => d.total));
    const itemWidth = width / periodData.length;
    
    // Dessiner les axes
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, height + padding);
    ctx.lineTo(padding + width, height + padding);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height + padding);
    ctx.stroke();
    
    // Dessiner les barres
    periodData.forEach((item, index) => {
        const barHeight = (item.total / maxValue) * height;
        const x = padding + index * itemWidth + itemWidth / 4;
        const y = height + padding - barHeight;
        
        // Barre total
        ctx.fillStyle = '#e3f2fd';
        ctx.fillRect(x, y, itemWidth / 3, barHeight);
        ctx.strokeStyle = '#1e5ba8';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, itemWidth / 3, barHeight);
        
        // Barre anomalies
        const anomalyHeight = (item.anomalies / maxValue) * height;
        const anomalyY = height + padding - anomalyHeight;
        ctx.fillStyle = '#ff9800';
        ctx.fillRect(x + itemWidth / 3, anomalyY, itemWidth / 3, anomalyHeight);
        ctx.strokeStyle = '#ff6f00';
        ctx.lineWidth = 1;
        ctx.strokeRect(x + itemWidth / 3, anomalyY, itemWidth / 3, anomalyHeight);
        
        // Label (date)
        ctx.fillStyle = '#666';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(item.date.substring(5), x + itemWidth / 2, height + padding + 15);
    });
    
    // Légende
    ctx.fillStyle = '#e3f2fd';
    ctx.fillRect(padding + width - 150, padding + 10, 15, 15);
    ctx.fillStyle = '#666';
    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Total', padding + width - 130, padding + 22);
    
    ctx.fillStyle = '#ff9800';
    ctx.fillRect(padding + width - 150, padding + 30, 15, 15);
    ctx.fillStyle = '#666';
    ctx.fillText('Anomalies', padding + width - 130, padding + 42);
}

// Adapter la hauteur du canvas si nécessaire
window.addEventListener('resize', loadStatistics);
