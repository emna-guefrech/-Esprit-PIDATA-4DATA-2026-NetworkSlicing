// Toast Notification System
class Toast {
    static show(message, type = 'info', duration = 4000) {
        const toastContainer = this.getContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${this.getIcon(type)}</span>
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove();">&times;</button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }
    
    static success(message, duration = 4000) {
        this.show(message, 'success', duration);
    }
    
    static error(message, duration = 5000) {
        this.show(message, 'error', duration);
    }
    
    static warning(message, duration = 4000) {
        this.show(message, 'warning', duration);
    }
    
    static info(message, duration = 4000) {
        this.show(message, 'info', duration);
    }
    
    static getContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    static getIcon(type) {
        const icons = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        };
        return icons[type] || icons['info'];
    }
}

// Auto-show Flask flash messages as toasts
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const type = alert.classList.contains('alert-success') ? 'success' :
                     alert.classList.contains('alert-danger') ? 'error' :
                     alert.classList.contains('alert-warning') ? 'warning' : 'info';
        const message = alert.textContent.trim();
        if (message) {
            Toast[type](message);
        }
        alert.style.display = 'none'; // Hide original alert
    });
});
