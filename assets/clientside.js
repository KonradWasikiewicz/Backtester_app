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
        },
        
        // New function to initialize error capturing
        initErrorCapture: function() {
            console.log("Initializing error capture from clientside callback");
            
            // Error counter
            let errorCount = 0;
            
            // Helper function to check if error is Dash related
            function isDashError(errorMsg) {
                // Check for common Dash error patterns
                return (
                    errorMsg.includes('nonexistent object was used') ||
                    errorMsg.includes('circular dependencies') ||
                    errorMsg.includes('callback') ||
                    errorMsg.includes('component') ||
                    errorMsg.includes('Dash') ||
                    errorMsg.includes('property') ||
                    errorMsg.includes('prop') ||
                    errorMsg.includes('Input') ||
                    errorMsg.includes('Output') ||
                    errorMsg.includes('has no prop') ||
                    errorMsg.includes('object was used') ||
                    errorMsg.includes('TypeError')
                );
            }
            
            // Helper function to send logs to server
            function sendLogsToServer(logs, type) {
                if (!logs || logs.length === 0) return;
                
                const payload = {};
                payload[type] = logs;
                
                fetch('/log-client-errors', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                }).catch(e => console.log("Error sending logs:", e));
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
            
            // Function to update error counter
            function updateErrorCounter() {
                if (document.readyState === "loading") {
                    document.addEventListener('DOMContentLoaded', createErrorCounter);
                } else {
                    createErrorCounter();
                }
            }
            
            // Capture Dash errors from DOM
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                        for (let i = 0; i < mutation.addedNodes.length; i++) {
                            const node = mutation.addedNodes[i];
                            if (node.nodeType === 1) {  // Element node
                                const errorElements = node.querySelectorAll('.dash-error');
                                if (errorElements.length > 0) {
                                    errorElements.forEach(errorEl => {
                                        const errorMsg = errorEl.textContent || errorEl.innerText;
                                        errorCount++;
                                        updateErrorCounter();
                                        sendLogsToServer([`[DASH DOM ERROR] ${errorMsg}`], 'errors');
                                    });
                                }
                            }
                        }
                    }
                });
            });
            
            // Start observing the document for Dash errors
            if (document.readyState === "loading") {
                document.addEventListener('DOMContentLoaded', () => {
                    observer.observe(document.body, { childList: true, subtree: true });
                });
            } else {
                observer.observe(document.body, { childList: true, subtree: true });
            }
            
            // Send initialization message
            sendLogsToServer(['Client-side error logging initialized'], 'logs');
            
            return "Error capture initialized";
        }
    }
});