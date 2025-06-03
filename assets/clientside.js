// --- General Error Handler (with enhanced logging and error suppression) ---
window.onerror = function (message, source, lineno, colno, error) {
  // Check if it's a connection refused error, which we want to suppress
  if (message && (
      message.includes('net::ERR_CONNECTION_REFUSED') || 
      message.includes('Failed to fetch') ||
      message.includes('message channel closed')
     )) {
    console.log("[window.onerror] Suppressing connection error:", message);
    return true; // Suppress error
  }
  
  console.log("[window.onerror] Caught error:", message, "at", source, lineno, colno);
  
  try {
    // Don't attempt to send errors to server if it's related to connection issues
    if (navigator.onLine && !message.includes('connection') && !message.includes('network')) {
      const errorData = {
        type: 'window.onerror',
        message: message,
        source: source,
        lineno: lineno,
        colno: colno,
        error: error ? error.stack : 'No error object available',
        url: window.location.href
      };
      
      console.log("[window.onerror] Preparing to send data:", errorData);
      
      fetch('/log-client-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            errors: [JSON.stringify(errorData)],
            warnings: [],
            logs: []
        }),
        credentials: 'same-origin',
        // Add timeout to prevent long-hanging requests
        signal: AbortSignal.timeout(3000)
      })
      .then(response => {
        if (!response.ok) {
          console.error('[window.onerror] Failed to send log to server. Status:', response.status, response.statusText);
        } else {
          console.log('[window.onerror] Log sent successfully.');
        }
      })
      .catch(networkError => {
        console.error('[window.onerror] Network error sending log:', networkError);
      });
    }
  } catch (e) {
    console.error("[window.onerror] Error within the handler itself:", e);
  }
  
  // Return true for React and message channel errors to prevent console spam
  if (message && (message.includes('React') || message.includes('message channel'))) {
    return true; // Suppress these errors
  }
  
  return false; // Allow default handling for other errors
};
// --- END General Error Handler ---

// --- Add handler for unhandled promise rejections ---
window.addEventListener('unhandledrejection', function(event) {
  // Check if it's a connection error and suppress it
  if (event.reason && (
      String(event.reason).includes('net::ERR_CONNECTION_REFUSED') || 
      String(event.reason).includes('Failed to fetch') ||
      String(event.reason).includes('NetworkError')
     )) {
    console.log("[unhandledrejection] Suppressing connection error:", event.reason);
    event.preventDefault(); // Prevent the error from showing in console
    return;
  }
  
  console.log("[unhandledrejection] Unhandled promise rejection:", event.reason);
});

// --- React Error Handler Fix ---
// This fixes the React-related errors in the web console
if (window.React && window.React.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED) {
  const originalConsoleError = console.error;
  console.error = function() {
    // Filter out specific React errors we want to suppress
    if (arguments[0] && typeof arguments[0] === 'string' && (
        arguments[0].includes('AppController.react.ts') || 
        arguments[0].includes('UnconnectedAppContainer.react.ts') ||
        arguments[0].includes('defaultProps will be removed') ||
        arguments[0].includes('listener indicated an asynchronous response')
       )) {
      return; // Suppress these specific errors
    }
    
    // Pass through all other errors
    originalConsoleError.apply(console, arguments);
  };
}

// Function to format number with spaces as thousand separators
function formatNumberWithSpaces(number) {
    // Remove existing spaces and non-digit characters (except decimal point)
    let numStr = String(number).replace(/\s+/g, '');
    // Allow only digits
    numStr = numStr.replace(/[^\d]/g, '');
    // Add spaces
    return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Function to apply formatting to relevant input fields
function applyInputFormatting() {
    const numericInputs = document.querySelectorAll('.numeric-input-formatted');
    numericInputs.forEach(input => {
        // Format on initial load
        input.value = formatNumberWithSpaces(input.value);

        // Format on input change
        input.addEventListener('input', function(e) {
            // Store cursor position
            let cursorPosition = e.target.selectionStart;
            let originalLength = e.target.value.length;
            
            // Format the value
            e.target.value = formatNumberWithSpaces(e.target.value);

            // Restore cursor position
            let newLength = e.target.value.length;
            cursorPosition += (newLength - originalLength);
            // Ensure cursor position is valid
            if (cursorPosition < 0) cursorPosition = 0;
            if (cursorPosition > newLength) cursorPosition = newLength;
            e.target.setSelectionRange(cursorPosition, cursorPosition);
        });
    });
}

// Add wizard step header interaction
if (document) {
    // Wait for DOM content to be loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Set up event listeners for step headers after a short delay to ensure React has rendered
        setTimeout(function() {
            setupStepHeaders();
            applyInputFormatting(); // Apply formatting after setup
        }, 1000);
    });

    // Re-setup listeners and formatting when the page changes or updates
    window.addEventListener('load', function() {
        setupStepHeaders();
        applyInputFormatting();
    });
}

// Function to set up step header click handlers
function setupStepHeaders() {
    const stepHeaders = document.querySelectorAll('[id$="-header"]');
    
    stepHeaders.forEach(header => {
        // Add visual indicator that headers are clickable
        header.style.cursor = 'pointer';
        
        // REMOVED JAVASCRIPT HOVER EFFECTS FOR BACKGROUND COLOR
        // header.addEventListener('mouseover', function() {
        //     this.style.backgroundColor = '#2a2e39';
        // });
        // 
        // header.addEventListener('mouseout', function() {
        //     this.style.backgroundColor = '#1e222d';
        // });
        
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

// --- Disabled Button Click Handler ---
// Handle clicks on disabled wizard confirmation buttons to show validation errors
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DisabledButtonClick] Setting up disabled button click handlers...');
    
    // Add click listeners to wizard confirmation buttons
    const wizardButtons = [
        { id: 'confirm-strategy-button', step: 1 },
        { id: 'confirm-dates-button', step: 2 },
        { id: 'confirm-tickers-button', step: 3 },
        { id: 'confirm-risk-button', step: 4 },
        { id: 'confirm-costs-button', step: 5 },
        { id: 'confirm-rebalancing-button', step: 6 }
    ];

    wizardButtons.forEach(buttonInfo => {
        // Use a timeout to ensure DOM is fully loaded
        setTimeout(() => {
            const button = document.getElementById(buttonInfo.id);
            if (button) {
                button.addEventListener('click', function(e) {
                    // Check if button is disabled
                    if (this.disabled || this.hasAttribute('disabled')) {
                        console.log(`[DisabledButtonClick] User clicked disabled button: ${buttonInfo.id}`);
                        e.preventDefault(); // Prevent default click behavior
                        e.stopPropagation(); // Stop event bubbling
                        
                        // Show a simple alert for now
                        alert('Please complete the required fields in this step before confirming.');
                        return false;
                    }
                });
                
                console.log(`[DisabledButtonClick] Added listener to button: ${buttonInfo.id}`);
            } else {
                console.warn(`[DisabledButtonClick] Button not found: ${buttonInfo.id}`);
            }
        }, 100);
    });
});