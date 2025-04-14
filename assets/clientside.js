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

// Helper function to batch-send logs to server
function sendBrowserLogsToServer(logs, type) {
    // Make sure we have something to send
    if (!logs || logs.length === 0) return;
    
    // Prepare data in the correct format
    const payload = {};
    payload[type] = logs;
    
    // Send data to server
    fetch('/log-client-errors', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    }).catch(err => {
        console.error('Error sending logs to server:', err);
    });
}

// Enhanced browser error capturing
(function() {
    console.log("Initializing browser error capturing");
    
    // Buffers for messages
    const errorBuffer = [];
    const warnBuffer = [];
    const logBuffer = [];
    
    // Error counter
    let errorCount = 0;
    
    // Store original console functions
    const originalConsoleLog = console.log;
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;
    
    // Override console.error
    console.error = function(...args) {
        // Call original function
        originalConsoleError.apply(console, args);
        
        try {
            // Convert parameters to string
            const errorMsg = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            
            // Add to buffer
            errorBuffer.push("[ERROR] " + errorMsg);
            errorCount++;
            
            // Update error counter if element exists
            updateErrorCounter();
            
            // Send errors to server every 5 seconds
            if (errorBuffer.length === 1) {
                setTimeout(() => {
                    sendBrowserLogsToServer(errorBuffer.slice(), 'errors');
                    errorBuffer.length = 0;
                }, 5000);
            }
        } catch (e) {
            originalConsoleError.call(console, "Error capturing console.error:", e);
        }
    };
    
    // Override console.warn
    console.warn = function(...args) {
        // Call original function
        originalConsoleWarn.apply(console, args);
        
        try {
            // Convert parameters to string
            const warnMsg = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            
            // Add to buffer
            warnBuffer.push("[WARN] " + warnMsg);
            
            // Send warnings to server every 10 seconds
            if (warnBuffer.length === 1) {
                setTimeout(() => {
                    sendBrowserLogsToServer(warnBuffer.slice(), 'warnings');
                    warnBuffer.length = 0;
                }, 10000);
            }
        } catch (e) {
            originalConsoleError.call(console, "Error capturing console.warn:", e);
        }
    };
    
    // Listen for uncaught errors
    window.addEventListener('error', function(event) {
        try {
            const errorMsg = `[UNCAUGHT] ${event.message} at ${event.filename}:${event.lineno}`;
            errorBuffer.push(errorMsg);
            errorCount++;
            
            updateErrorCounter();
            
            // Send uncaught errors immediately
            sendBrowserLogsToServer([errorMsg], 'errors');
        } catch (e) {
            originalConsoleError.call(console, "Error handling window.onerror:", e);
        }
        return false;  // Allow error propagation
    });
    
    // Listen for rejected Promises
    window.addEventListener('unhandledrejection', function(event) {
        try {
            const errorMsg = `[PROMISE] ${event.reason}`;
            errorBuffer.push(errorMsg);
            errorCount++;
            
            updateErrorCounter();
            
            // Send Promise errors immediately
            sendBrowserLogsToServer([errorMsg], 'errors');
        } catch (e) {
            originalConsoleError.call(console, "Error handling unhandledrejection:", e);
        }
        return false;  // Allow error propagation
    });
    
    // Function to update error counter
    function updateErrorCounter() {
        // Defer counter creation until after DOM is loaded
        if (document.readyState === "loading") {
            document.addEventListener('DOMContentLoaded', createErrorCounter);
        } else {
            createErrorCounter();
        }
    }
    
    // Function to create or update error counter
    function createErrorCounter() {
        let errorCounter = document.getElementById('browser-errors-count');
        
        if (!errorCounter) {
            errorCounter = document.createElement('div');
            errorCounter.id = 'browser-errors-count';
            errorCounter.style.position = 'fixed';
            errorCounter.style.bottom = '10px';
            errorCounter.style.right = '10px';
            errorCounter.style.backgroundColor = 'red';
            errorCounter.style.color = 'white';
            errorCounter.style.padding = '5px 10px';
            errorCounter.style.borderRadius = '10px';
            errorCounter.style.fontWeight = 'bold';
            errorCounter.style.zIndex = '9999';
            errorCounter.style.cursor = 'pointer';
            errorCounter.title = 'Click to see error details';
            
            errorCounter.onclick = function() {
                alert('Logged ' + errorCount + ' errors to backtest.log file');
            };
            
            document.body.appendChild(errorCounter);
        }
        
        errorCounter.textContent = errorCount;
        errorCounter.style.display = errorCount > 0 ? 'block' : 'none';
    }
    
    console.log("Browser error capturing active");
})();