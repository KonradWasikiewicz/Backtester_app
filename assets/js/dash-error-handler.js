// Dash Error Handler
(function() {
    const STORAGE_KEY = 'dashErrorLogs';
    
    // Function to store error in localStorage
    function storeError(type, message) {
        const logs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        logs.push({
            timestamp: new Date().toISOString(),
            type: type,
            message: message
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
        localStorage.setItem('hasNewDashErrors', 'true');
    }

    // Override console methods to catch Dash-related errors
    const originalConsole = {
        error: console.error,
        warn: console.warn,
        log: console.log
    };

    console.error = function(...args) {
        const message = args.join(' ');
        if (message.includes('Dash')) {
            storeError('error', message);
        }
        originalConsole.error.apply(console, args);
    };

    console.warn = function(...args) {
        const message = args.join(' ');
        if (message.includes('Dash')) {
            storeError('warning', message);
        }
        originalConsole.warn.apply(console, args);
    };

    // Send stored errors to server periodically
    function sendStoredErrors() {
        if (localStorage.getItem('hasNewDashErrors') === 'true') {
            const logs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            if (logs.length > 0) {
                fetch('/collect-dash-errors', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ logs: logs })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        localStorage.removeItem(STORAGE_KEY);
                        localStorage.removeItem('hasNewDashErrors');
                    }
                })
                .catch(error => originalConsole.error('Error sending logs:', error));
            }
        }
    }

    // Send errors every 5 seconds if there are any new ones
    setInterval(sendStoredErrors, 5000);
})(); 