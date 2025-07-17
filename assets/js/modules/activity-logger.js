// =====================================================
// FILE: assets/js/modules/activity-logger.js
// =====================================================
/**
 * Activity Logger Module
 * Handles real-time activity logging for the application
 */
class ActivityLogger {
    constructor() {
        this.startTime = null;
    }

    /**
     * Initialize the activity log
     */
    initialize() {
        const logContainer = document.getElementById('activityLog');
        if (logContainer) {
            logContainer.innerHTML = '';
        }
        this.updateTimer('Initializing');
    }

    /**
     * Log activity with timestamp and styling
     * @param {string} message - Log message
     * @param {string} type - Log type: 'info', 'success', 'warning', 'error'
     */
    log(message, type = 'info') {
        const logContainer = document.getElementById('activityLog');
        if (logContainer) {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.innerHTML = `<span style="color: #999; font-size: 0.8em;">[${new Date().toLocaleTimeString()}]</span> ${message}`;
            
            // Add fade-in animation
            logEntry.style.opacity = '0';
            logContainer.appendChild(logEntry);
            
            // Trigger animation
            setTimeout(() => {
                logEntry.style.opacity = '1';
                logEntry.style.transition = 'opacity 0.3s ease';
            }, 10);
            
            // Auto-scroll to bottom
            logContainer.scrollTop = logContainer.scrollHeight;
            
            // Keep only last 10 entries to prevent overflow
            const entries = logContainer.querySelectorAll('.log-entry');
            if (entries.length > 10) {
                entries[0].remove();
            }
        }
    }

    /**
     * Update the processing timer
     * @param {string} status - Timer status
     */
    updateTimer(status) {
        const timer = document.getElementById('processingTimer');
        if (timer) {
            timer.textContent = status;
            timer.className = `sidebar-timer ${status.toLowerCase()}`;
        }
    }

    /**
     * Start timing for analysis
     */
    startTiming() {
        this.startTime = performance.now();
    }

    /**
     * Get elapsed time since start
     */
    getElapsedTime() {
        return this.startTime ? performance.now() - this.startTime : 0;
    }
}