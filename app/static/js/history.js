/* History Page */

let currentPage = 1;
const ITEMS_PER_PAGE = 10;
let currentFilters = {};

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadHistory();
});

function setupEventListeners() {
    // Filter button
    const filterBtn = document.getElementById('filterBtn');
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            currentPage = 1;
            applyFilters();
            loadHistory();
        });
    }
    
    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            clearAllFilters();
            currentPage = 1;
            loadHistory();
        });
    }
    
    // Pagination
    document.getElementById('prevBtn')?.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadHistory();
        }
    });
    
    document.getElementById('nextBtn')?.addEventListener('click', () => {
        currentPage++;
        loadHistory();
    });
}

function applyFilters() {
    currentFilters = {};
    
    const sliceId = document.getElementById('filterSliceId')?.value;
    if (sliceId) currentFilters.slice_id = sliceId;
    
    const isAnomaly = document.getElementById('filterIsAnomaly')?.value;
    if (isAnomaly) currentFilters.is_anomaly = isAnomaly;
    
    const method = document.getElementById('filterMethod')?.value;
    if (method) currentFilters.method = method;
    
    const startDate = document.getElementById('filterStartDate')?.value;
    if (startDate) currentFilters.start_date = new Date(startDate).toISOString();
    
    const endDate = document.getElementById('filterEndDate')?.value;
    if (endDate) currentFilters.end_date = new Date(endDate).toISOString();
}

function clearAllFilters() {
    document.getElementById('filterSliceId').value = '';
    document.getElementById('filterIsAnomaly').value = '';
    document.getElementById('filterMethod').value = '';
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    currentFilters = {};
}

async function loadHistory() {
    const historyBody = document.getElementById('historyBody');
    showLoading(historyBody);
    
    try {
        // Construire les paramètres de requête
        const params = new URLSearchParams({
            limit: ITEMS_PER_PAGE,
            offset: (currentPage - 1) * ITEMS_PER_PAGE,
            ...currentFilters
        });
        
        const response = await fetchAPI(`/anomaly/history?${params.toString()}`);
        
        if (!response.success) {
            showError(historyBody, response.error);
            return;
        }
        
        const data = response.data;
        displayHistoryTable(data.anomalies);
        updatePaginationInfo(data.total, data.count);
    } catch (error) {
        showError(historyBody, error.message);
    }
}

function displayHistoryTable(anomalies) {
    const tbody = document.getElementById('historyBody');
    
    if (!anomalies || anomalies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Aucune anomalie trouvée</td></tr>';
        return;
    }
    
    tbody.innerHTML = anomalies.map(anomaly => `
        <tr class="${anomaly.is_anomaly ? 'anomaly-row' : ''}">
            <td>${anomaly.id}</td>
            <td>${anomaly.slice_id}</td>
            <td>
                <span class="badge ${anomaly.is_anomaly ? 'badge-active' : 'badge-degraded'}">
                    ${anomaly.is_anomaly ? 'Anomalie' : 'Normal'}
                </span>
            </td>
            <td>${formatNumber(anomaly.score, 4)}</td>
            <td>${getConfidenceLevel(anomaly.score)}</td>
            <td>${anomaly.method}</td>
            <td>${formatNumber(anomaly.isolation_forest_score, 4)}</td>
            <td>${formatNumber(anomaly.autoencoder_score, 4)}</td>
            <td>${formatDate(anomaly.created_at)}</td>
        </tr>
    `).join('');
}

function updatePaginationInfo(total, count) {
    document.getElementById('paginationInfo').textContent = 
        `Affichage ${(currentPage - 1) * ITEMS_PER_PAGE + 1}-${(currentPage - 1) * ITEMS_PER_PAGE + count} sur ${total}`;
    
    document.getElementById('pageInfo').textContent = `Page ${currentPage}`;
    
    document.getElementById('nextBtn').disabled = (currentPage - 1) * ITEMS_PER_PAGE + count >= total;
    document.getElementById('prevBtn').disabled = currentPage === 1;
}

// Style pour les lignes d'anomalies
const style = document.createElement('style');
style.textContent = `
    .anomaly-row {
        background-color: rgba(244, 67, 54, 0.05);
    }
    
    .history-table td {
        padding: 0.75rem;
    }
    
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-active {
        background: #ff9800;
        color: white;
    }
    
    .badge-degraded {
        background: #4caf50;
        color: white;
    }
`;
document.head.appendChild(style);
