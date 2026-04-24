/*
 * Dashboard JavaScript - Interactive Components
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers if using Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Sidebar mobile toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(event) {
            const sidebar = document.querySelector('.sidebar');
            const toggle = document.getElementById('sidebarToggle');
            
            if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
                sidebar.classList.remove('active');
            }
        });
    }
});

/**
 * Fetch dashboard metrics via API
 */
function updateDashboardMetrics() {
    fetch('/api/dashboard/metrics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update metric cards
                const metricsData = data.data;
                console.log('Dashboard metrics updated:', metricsData);
                // Update UI elements here based on metricsData
            }
        })
        .catch(error => console.error('Error fetching metrics:', error));
}

/**
 * Auto-refresh dashboard metrics every 30 seconds
 */
setInterval(function() {
    updateDashboardMetrics();
}, 30000);

// Initial update
updateDashboardMetrics();

/**
 * Confirm before deleting or deactivating
 */
function confirmAction(message) {
    return confirm(message);
}

/**
 * Format timestamp to readable date
 */
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        console.log('Copied to clipboard: ' + text);
    });
}
