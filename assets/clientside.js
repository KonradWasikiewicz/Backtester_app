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
        
        // Console error capture function
        capture_console_errors: function() {
            console.log("DEBUG: Uruchomiono przechwytywanie błędów konsoli");
            
            // Zapisywanie oryginalnych funkcji konsolowych
            const originalConsoleLog = console.log;
            const originalConsoleError = console.error;
            const originalConsoleWarn = console.warn;
            
            // Bufory dla komunikatów
            let errorMessages = [];
            let warnMessages = [];
            let logMessages = [];
            
            // Zastąpienie funkcji konsolowych
            console.log = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                logMessages.push("[LOG] " + message);
                originalConsoleLog.apply(console, args);
            };
            
            console.error = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                errorMessages.push("[ERROR] " + message);
                originalConsoleError.apply(console, args);
            };
            
            console.warn = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                warnMessages.push("[WARN] " + message);
                originalConsoleWarn.apply(console, args);
            };
            
            // Nasłuchiwanie niezłapanych błędów
            window.addEventListener('error', function(event) {
                const errorMsg = `[UNCAUGHT] ${event.message} at ${event.filename}:${event.lineno}`;
                errorMessages.push(errorMsg);
                document.getElementById('browser-errors-count').textContent = errorMessages.length;
                document.getElementById('browser-errors-count').style.display = 'inline-block';
                return false;
            });
            
            // Nasłuchiwanie odrzuconych Promise
            window.addEventListener('unhandledrejection', function(event) {
                const errorMsg = `[PROMISE] ${event.reason}`;
                errorMessages.push(errorMsg);
                document.getElementById('browser-errors-count').textContent = errorMessages.length;
                document.getElementById('browser-errors-count').style.display = 'inline-block';
                return false;
            });
            
            // Okresowe wysyłanie logów do serwera
            setInterval(function() {
                if (errorMessages.length > 0 || warnMessages.length > 0) {
                    const allMessages = {
                        errors: errorMessages,
                        warnings: warnMessages,
                        logs: logMessages
                    };
                    
                    // Aktualizacja widocznego licznika błędów
                    if (document.getElementById('browser-errors-count')) {
                        document.getElementById('browser-errors-count').textContent = errorMessages.length;
                    }
                    
                    fetch('/log-client-errors', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(allMessages)
                    }).then(function() {
                        // Wyczyszczenie buforów po wysłaniu
                        errorMessages = [];
                        warnMessages = [];
                        logMessages = [];
                    });
                }
            }, 2000);
            
            // Dodanie widocznego elementu informującego o liczbie błędów
            document.addEventListener('DOMContentLoaded', function() {
                const errorCounter = document.createElement('div');
                errorCounter.id = 'browser-errors-count';
                errorCounter.textContent = '0';
                errorCounter.style.position = 'fixed';
                errorCounter.style.bottom = '10px';
                errorCounter.style.right = '10px';
                errorCounter.style.backgroundColor = 'red';
                errorCounter.style.color = 'white';
                errorCounter.style.padding = '5px 10px';
                errorCounter.style.borderRadius = '10px';
                errorCounter.style.fontWeight = 'bold';
                errorCounter.style.zIndex = '9999';
                errorCounter.style.display = 'none';
                errorCounter.style.cursor = 'pointer';
                errorCounter.title = 'Kliknij, aby zobaczyć szczegóły błędów';
                
                errorCounter.onclick = function() {
                    console.log('Sprawdź plik backtest.log, aby zobaczyć przechwycone błędy');
                    alert('Zalogowano ' + errorCounter.textContent + ' błędów do pliku backtest.log');
                };
                
                document.body.appendChild(errorCounter);
                console.log("DEBUG: Dodano licznik błędów do DOM");
            });
            
            return "Przechwytywanie błędów aktywne";
        }
    }
});

// Automatyczne uruchomienie funkcji przechwytywania błędów
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM załadowany, uruchamiam przechwytywanie błędów konsoli");
    window.dash_clientside.clientside.capture_console_errors();
});