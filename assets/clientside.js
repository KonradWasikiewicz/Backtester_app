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
    
    // Function to check if error is Dash related
    function isDashError(errorMsg) {
        // Check for common Dash error patterns
        return (
            errorMsg.includes('dash') || 
            errorMsg.includes('callback') || 
            errorMsg.includes('component') ||
            errorMsg.includes('layout') ||
            errorMsg.includes('prop') ||
            errorMsg.includes('property') ||
            errorMsg.includes('nonexistent object was used') ||
            errorMsg.includes('of a Dash') ||
            errorMsg.includes('circular dependencies') ||
            errorMsg.includes('invalid prop') ||
            errorMsg.includes('_clickData') ||
            errorMsg.includes('has no prop') ||
            errorMsg.includes('TypeError') ||
            errorMsg.includes('component ID') ||
            // Additional patterns from your screenshot
            errorMsg.includes('nonrepresistent object was used') ||
            errorMsg.includes('Input') ||
            errorMsg.includes('Output') ||
            errorMsg.includes('property') ||
            errorMsg.includes('callbacks') ||
            errorMsg.includes('circular dependencies') ||
            errorMsg.includes('Dash') ||
            errorMsg.includes('Property') ||
            errorMsg.includes('_clicks') ||
            errorMsg.includes('object was used') ||
            errorMsg.includes('style') ||
            errorMsg.includes('className')
        );
    }
    
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
            
            // Check if this is a Dash-related error
            const dashError = isDashError(errorMsg);
            
            // Send Dash errors immediately
            if (dashError) {
                sendBrowserLogsToServer(["[DASH ERROR] " + errorMsg], 'errors');
            }
            // Send other errors every 5 seconds
            else if (errorBuffer.length === 1) {
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
            
            // Check if this is a Dash-related warning
            const dashWarning = isDashError(warnMsg);
            
            // Send Dash warnings immediately
            if (dashWarning) {
                sendBrowserLogsToServer(["[DASH WARNING] " + warnMsg], 'warnings');
            }
            // Send other warnings every 10 seconds 
            else if (warnBuffer.length === 1) {
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
            
            // Check if this is a Dash-related error
            const dashError = isDashError(errorMsg);
            
            // Send with appropriate tag
            if (dashError) {
                sendBrowserLogsToServer(["[DASH UNCAUGHT ERROR] " + errorMsg], 'errors');
            } else {
                sendBrowserLogsToServer([errorMsg], 'errors');
            }
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
            
            // Check if this is a Dash-related promise rejection
            const dashError = isDashError(String(event.reason));
            
            // Send with appropriate tag
            if (dashError) {
                sendBrowserLogsToServer(["[DASH PROMISE ERROR] " + errorMsg], 'errors');
            } else {
                sendBrowserLogsToServer([errorMsg], 'errors');
            }
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

// Error handling for browser and Dash errors
(function() {
    // Function to check if error is Dash related
    function isDashError(errorMsg) {
        // Check for common Dash error patterns
        return (
            errorMsg.includes('dash') || 
            errorMsg.includes('callback') || 
            errorMsg.includes('component') ||
            errorMsg.includes('layout') ||
            errorMsg.includes('prop') ||
            errorMsg.includes('property') ||
            errorMsg.includes('nonexistent object was used') ||
            errorMsg.includes('nonrepresistent object was used') ||
            errorMsg.includes('of a Dash') ||
            errorMsg.includes('circular dependencies') ||
            errorMsg.includes('invalid prop') ||
            errorMsg.includes('_clickData') ||
            errorMsg.includes('has no prop') ||
            errorMsg.includes('TypeError') ||
            errorMsg.includes('component ID') ||
            errorMsg.includes('Input') ||
            errorMsg.includes('Output') ||
            errorMsg.includes('callbacks') ||
            errorMsg.includes('Property') ||
            errorMsg.includes('_clicks') ||
            errorMsg.includes('object was used') ||
            errorMsg.includes('style') ||
            errorMsg.includes('className')
        );
    }

    // Function to send errors to the server for logging
    function sendErrorToServer(errorInfo) {
        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/log-client-error', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(errorInfo));
        } catch (e) {
            console.error('Failed to send error to server:', e);
        }
    }

    // Capture uncaught exceptions
    window.onerror = function(message, source, lineno, colno, error) {
        const errorInfo = {
            type: 'uncaught',
            message: message,
            source: source,
            lineno: lineno,
            colno: colno,
            stack: error && error.stack,
            timestamp: new Date().toISOString()
        };
        
        sendErrorToServer(errorInfo);
        return false;
    };

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        const errorInfo = {
            type: 'unhandledrejection',
            message: event.reason && event.reason.message ? event.reason.message : 'Unhandled Promise rejection',
            stack: event.reason && event.reason.stack,
            timestamp: new Date().toISOString()
        };
        
        sendErrorToServer(errorInfo);
    });

    // Override console.error to capture Dash errors specifically
    const originalConsoleError = console.error;
    console.error = function(...args) {
        originalConsoleError.apply(console, args);
        
        // Convert args to string for analysis
        const errorMsg = args.map(arg => 
            typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        ).join(' ');
        
        // If this is a Dash error, send it to the server
        if (isDashError(errorMsg)) {
            const errorInfo = {
                type: 'dash-error',
                message: errorMsg,
                timestamp: new Date().toISOString()
            };
            
            sendErrorToServer(errorInfo);
        }
    };

    // Special capture for Dash errors that appear in the error info box
    // Using MutationObserver to detect when new errors are added to the DOM
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1) {  // Element node
                        // Look for Dash error messages in the DOM
                        const errorElements = node.querySelectorAll('.dash-error');
                        if (errorElements.length > 0) {
                            errorElements.forEach(errorEl => {
                                const errorMsg = errorEl.textContent || errorEl.innerText;
                                const errorInfo = {
                                    type: 'dash-dom-error',
                                    message: errorMsg,
                                    timestamp: new Date().toISOString()
                                };
                                sendErrorToServer(errorInfo);
                            });
                        }
                    }
                }
            }
        });
    });

    // Start observing the document for Dash error messages
    document.addEventListener('DOMContentLoaded', function() {
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Send initial message to indicate clientside error logging is active
        sendErrorToServer({
            type: 'info',
            message: 'Client-side error logging initialized',
            timestamp: new Date().toISOString()
        });
    });
})();