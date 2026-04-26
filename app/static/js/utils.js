/* Utilities */

const API_BASE_URL = '/api';

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error: ${endpoint}`, error);
        throw error;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);
}

function formatDateTime(dateString) {
    return formatDate(dateString);
}

function getConfidenceLevel(score) {
    if (score >= 0.8) return 'HIGH';
    if (score >= 0.5) return 'MEDIUM';
    return 'LOW';
}

function formatNumber(number, decimals = 2) {
    return parseFloat(number).toFixed(decimals);
}

function showLoading(element) {
    if (element) {
        element.innerHTML = '<div class="loading-state">Chargement...</div>';
    }
}

function showError(element, message) {
    if (element) {
        element.innerHTML = `<div class="alert alert-danger">Erreur: ${message}</div>`;
    }
}

function showNotification(message, type = 'info') {
    // Simple notification (peut être amélioré)
    console.log(`[${type.toUpperCase()}] ${message}`);
}
