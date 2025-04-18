// --- DASH ERROR LOGGER: START ---
(function() {
    const originalError = console.error;
    const originalWarn = console.warn;
    const dashPatterns = [
        'nonexistent object',
        'object was used',
        'circular depend',
        'callback',
        'Input',
        'Output',
        'dash',
        'Dash',
        'has no prop',
        'TypeError'
    ];
    function isDashError(msg) {
        return dashPatterns.some(pattern => msg.includes(pattern));
    }
    function sendToServer(type, msg) {
        fetch('/log-client-errors', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                errors: type === 'error' ? [msg] : [],
                warnings: type === 'warning' ? [msg] : [],
                logs: []
            }),
            credentials: 'same-origin'
        }).catch(() => {});
    }
    console.error = function(...args) {
        originalError.apply(console, args);
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        if (isDashError(msg)) sendToServer('error', msg);
    };
    console.warn = function(...args) {
        originalWarn.apply(console, args);
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        if (isDashError(msg)) sendToServer('warning', msg);
    };
    setInterval(() => {
        document.querySelectorAll('.dash-error, ._dash-error').forEach(el => {
            const txt = el.textContent || el.innerText;
            if (txt && txt.trim() !== '') sendToServer('error', '[DOM] ' + txt.trim());
        });
    }, 2000);
    window.addEventListener('error', e => {
        if (e && e.message && isDashError(e.message)) sendToServer('error', '[window.onerror] ' + e.message);
    });
    window.addEventListener('unhandledrejection', e => {
        if (e && e.reason) sendToServer('error', '[unhandledrejection] ' + (e.reason.message || String(e.reason)));
    });
})();
// --- DASH ERROR LOGGER: END ---

// Add wizard step header interaction
if (document) {
    // Wait for DOM content to be loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Set up event listeners for step headers after a short delay to ensure React has rendered
        setTimeout(function() {
            setupStepHeaders();
        }, 1000);
    });

    // Re-setup listeners when the page changes
    window.addEventListener('load', function() {
        setupStepHeaders();
    });
}

// Function to set up step header click handlers
function setupStepHeaders() {
    const stepHeaders = document.querySelectorAll('[id$="-header"]');
    
    stepHeaders.forEach(header => {
        // Add visual indicator that headers are clickable
        header.style.cursor = 'pointer';
        
        // Add hover effect
        header.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#2a2e39';
        });
        
        header.addEventListener('mouseout', function() {
            this.style.backgroundColor = '#1e222d';
        });
        
        // Add focus effect for accessibility
        header.addEventListener('focus', function() {
            this.style.outline = '2px solid #0d6efd';
        });
        
        header.addEventListener('blur', function() {
            this.style.outline = 'none';
        });
        
        // Make the header focusable for keyboard navigation
        if (!header.getAttribute('tabindex')) {
            header.setAttribute('tabindex', '0');
        }
    });
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        // Function to sync risk management checkboxes based on the features list
        syncCheckboxesToList: function(featuresList) {
            // Define all features in the same order as the callback outputs
            const features = [
                "position_sizing", "stop_loss", "take_profit", 
                "risk_per_trade", "market_filter", "drawdown_protection",
                "continue_iterate"
            ];
            
            // Initialize result array with empty arrays (unchecked state)
            const result = features.map(() => []);
            
            // If featuresList is provided, update corresponding checkboxes
            if (featuresList) {
                features.forEach((feature, index) => {
                    if (featuresList.includes(feature)) {
                        result[index] = [feature];
                    }
                });
            }
            
            // Return array of arrays for each checkbox
            return result;
        }
    }
});