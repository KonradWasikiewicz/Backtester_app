import sys
import logging
import traceback
from pathlib import Path
import os
import re
import inspect
import warnings

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
sys.path.append(str(APP_ROOT))

# Import factory functions
try:
    from src.ui.app_factory import create_app, configure_logging
    from dash import html, dcc, ClientsideFunction
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configure application logging
configure_logging()
logger = logging.getLogger(__name__)

def configure_client_side_logging():
    """Configure client-side logging to capture browser console errors."""
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='client-error-container'),
        # Include the error tracking JavaScript directly to ensure it's loaded
        html.Script('''
        (function() {
            console.log("Initializing inline error capture");
            
            // Store original console functions
            var originalConsoleLog = console.log;
            var originalConsoleError = console.error;
            var originalConsoleWarn = console.warn;
            
            // Buffers for messages
            var logMessages = [];
            var errorMessages = [];
            var warnMessages = [];
            
            // Override console.error to capture Dash errors
            console.error = function() {
                var args = Array.prototype.slice.call(arguments);
                errorMessages.push("[ERROR] " + args.join(' '));
                originalConsoleError.apply(console, arguments);
                
                // Send Dash errors immediately
                var errorMsg = args.join(' ');
                if (errorMsg.includes('Dash') || 
                    errorMsg.includes('callback') || 
                    errorMsg.includes('nonexistent object') ||
                    errorMsg.includes('component') ||
                    errorMsg.includes('Input') || 
                    errorMsg.includes('Output')) {
                    sendLogs();
                }
            };
            
            // Override console.warn
            console.warn = function() {
                var args = Array.prototype.slice.call(arguments);
                warnMessages.push("[WARN] " + args.join(' '));
                originalConsoleWarn.apply(console, arguments);
            };
            
            // Override console.log
            console.log = function() {
                var args = Array.prototype.slice.call(arguments);
                logMessages.push("[LOG] " + args.join(' '));
                originalConsoleLog.apply(console, arguments);
            };
            
            // Listen for uncaught errors
            window.addEventListener('error', function(event) {
                errorMessages.push("[UNCAUGHT] " + event.message + " at " + event.filename + ":" + event.lineno);
                sendLogs();
                return false;
            });
            
            // Send logs every 3 seconds if there are any
            setInterval(sendLogs, 3000);
            
            function sendLogs() {
                if (errorMessages.length > 0 || warnMessages.length > 0 || logMessages.length > 0) {
                    var allMessages = {
                        errors: errorMessages,
                        warnings: warnMessages,
                        logs: logMessages
                    };
                    
                    fetch('/log-client-errors', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(allMessages)
                    }).then(function() {
                        // Clear buffers after sending
                        errorMessages = [];
                        warnMessages = [];
                        logMessages = [];
                    }).catch(function(err) {
                        originalConsoleError.call(console, "Error sending logs:", err);
                    });
                }
            }
            
            // Create visual error counter
            function createErrorCounter() {
                var errorCount = errorMessages.length;
                var counter = document.getElementById('browser-errors-count');
                
                if (!counter && errorCount > 0) {
                    counter = document.createElement('div');
                    counter.id = 'browser-errors-count';
                    counter.style.position = 'fixed';
                    counter.style.bottom = '10px';
                    counter.style.right = '10px';
                    counter.style.backgroundColor = 'red';
                    counter.style.color = 'white';
                    counter.style.padding = '5px 10px';
                    counter.style.borderRadius = '10px';
                    counter.style.fontWeight = 'bold';
                    counter.style.zIndex = '9999';
                    counter.style.cursor = 'pointer';
                    counter.title = 'Click to view error details';
                    
                    counter.onclick = function() {
                        sendLogs();
                        alert('Logged ' + errorCount + ' errors to backtest.log file');
                    };
                    
                    document.body.appendChild(counter);
                }
                
                if (counter) {
                    counter.textContent = errorCount;
                    counter.style.display = errorCount > 0 ? 'block' : 'none';
                }
            }
            
            // Update counter periodically
            setInterval(createErrorCounter, 1000);
            
            // Also capture DOM errors through mutation observer
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                        for (var i = 0; i < mutation.addedNodes.length; i++) {
                            var node = mutation.addedNodes[i];
                            if (node.nodeType === 1) {  // Element node
                                var errorElements = node.querySelectorAll('.dash-error');
                                if (errorElements.length > 0) {
                                    errorElements.forEach(function(errorEl) {
                                        var errorMsg = errorEl.textContent || errorEl.innerText;
                                        errorMessages.push("[DASH DOM] " + errorMsg);
                                    });
                                    sendLogs();
                                }
                            }
                        }
                    }
                });
            });
            
            // Start observing once DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                observer.observe(document.body, { childList: true, subtree: true });
                console.log("Error observer started");
                sendLogs(); // Send initial message
            });
        })();
        '''),
        # No need for the store component since we're using direct JS
    ])

def register_client_side_logging(app):
    """Register the client-side logging callback with the app"""
    # We're now using a direct inline script approach instead of callbacks
    # This function is kept for backwards compatibility
    logger.info("Client-side error logging enabled with direct script injection")
    pass

def apply_format_patches():
    """Apply runtime patches to fix invalid DataTable format strings."""
    try:
        logger.info("Applying format validation patches...")
        
        # Import dash components we need to patch
        from dash import dash_table
        
        # Original DataTable class
        original_datatable = dash_table.DataTable
        
        # Store original from_dict method
        original_from_dict = None
        if hasattr(dash_table, 'Format') and hasattr(dash_table.Format, 'from_dict'):
            original_from_dict = dash_table.Format.from_dict
        
        # Create a patched version that fixes format strings
        def fix_format_string(column_def):
            if isinstance(column_def, dict) and 'format' in column_def:
                fmt = column_def['format']
                if isinstance(fmt, str):
                    # Check for percentage formats
                    if re.search(r'\.(\d+)f%', fmt):
                        # Extract precision
                        match = re.search(r'\.(\d+)f%', fmt)
                        if match:
                            precision = int(match.group(1))
                            # Replace with proper format
                            logger.warning(f"Fixing invalid format: '{fmt}' -> FormatTemplate.percentage({precision})")
                            column_def['format'] = dash_table.FormatTemplate.percentage(precision)
                    # Add other format patterns that need fixing here
            return column_def
        
        # Patch DataTable format validation more aggressively
        def patched_datatable(*args, **kwargs):
            if 'columns' in kwargs and kwargs['columns']:
                fixed_columns = []
                for col in kwargs['columns']:
                    fixed_columns.append(fix_format_string(col))
                kwargs['columns'] = fixed_columns
                
            # Also check for data_table props that might have format strings
            if 'data' in kwargs and isinstance(kwargs['data'], list) and len(kwargs['data']) > 0:
                if 'style_data_conditional' in kwargs:
                    for style in kwargs['style_data_conditional']:
                        if isinstance(style, dict) and 'format' in style:
                            style = fix_format_string(style)
            
            return original_datatable(*args, **kwargs)
        
        # Also patch Format.from_dict if available
        def patched_from_dict(dict_):
            if isinstance(dict_, str) and re.search(r'\.(\d+)f%', dict_):
                match = re.search(r'\.(\d+)f%', dict_)
                if match:
                    precision = int(match.group(1))
                    logger.warning(f"Fixing invalid format in Format.from_dict: '{dict_}' -> percentage({precision})")
                    return dash_table.FormatTemplate.percentage(precision)
            
            if original_from_dict:
                return original_from_dict(dict_)
            return dict_
        
        # Apply our patches
        dash_table.DataTable = patched_datatable
        if hasattr(dash_table, 'Format') and hasattr(dash_table.Format, 'from_dict'):
            dash_table.Format.from_dict = patched_from_dict
            
        # Also monkey patch the percentage template for safety
        original_percentage = None
        if hasattr(dash_table.FormatTemplate, 'percentage'):
            original_percentage = dash_table.FormatTemplate.percentage
            
            def safe_percentage(precision=0):
                try:
                    return original_percentage(precision)
                except Exception as e:
                    logger.error(f"Error in percentage template: {e}")
                    # Return a failsafe format
                    return {'specifier': '.'+str(precision)+'%'}
                    
            dash_table.FormatTemplate.percentage = safe_percentage
        
        logger.info("Format validation patches applied successfully")
        print("ENHANCED Runtime format validation is active")
        return True
    except Exception as e:
        logger.error(f"Failed to apply format patches: {e}", exc_info=True)
        return False

def scan_for_format_issues():
    """Scan project files for potential DataTable format issues."""
    logger.info("Scanning for potential format issues in project files...")
    problematic_patterns = [r'\.2f%', r'\.1f%', r'\.0f%', r'%\.']
    src_dir = APP_ROOT / 'src'
    
    found_issues = False
    problem_files = []
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in problematic_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            rel_path = os.path.relpath(file_path, APP_ROOT)
                            logger.warning(f"Potential format issue in {rel_path}: {matches}")
                            print(f"WARNING: Potential format issue in {rel_path}: {matches}")
                            found_issues = True
                            problem_files.append(rel_path)
                except Exception as e:
                    logger.error(f"Error scanning {file}: {e}")
    
    if found_issues:
        print("\nSUGGESTIONS FOR FIXING FORMAT ISSUES:")
        print("1. Replace '.2f%' with dash_table.FormatTemplate.percentage(2)")
        print("2. Replace '.1f%' with dash_table.FormatTemplate.percentage(1)")
        print("3. Replace '.0f%' with dash_table.FormatTemplate.percentage(0)")
        print("4. For other numeric formats, use dash_table.Format() constructor\n")
        print("Files that need to be fixed:")
        for file in set(problem_files):
            print(f"- {file}")
    
    return found_issues

# Removed extreme callback validation bypass and improved error handling
try:
    logger.info("Initializing Backtester application")

    # Set debug mode - pass as parameter to create_app
    debug_mode = True

    # First scan for format issues
    format_issues_found = scan_for_format_issues()

    # Apply format patches to fix the issue at runtime
    patch_applied = apply_format_patches()
    if patch_applied:
        logger.info("Runtime format validation is active")

    # Create the Dash application with proper exception handling
    app = create_app(debug=debug_mode, suppress_callback_exceptions=True)

    # Define a function to check for existing routes
    def route_exists(route_path):
        """Check if a route already exists in the Flask app."""
        return any(rule.rule == route_path for rule in app.server.url_map.iter_rules())
    
    # Only register the route if it doesn't already exist
    if not route_exists('/log-client-errors'):
        @app.server.route('/log-client-errors', methods=['POST'])
        def log_client_errors():
            from flask import request, jsonify
            import json
            import datetime
            
            try:
                data = request.json
                
                # Bezpośrednie zapisanie do pliku dla pewności
                with open('dash_errors.log', 'a', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Log errors
                    if 'errors' in data and data['errors']:
                        for error in data['errors']:
                            error_line = f"{timestamp} - DASH ERROR: {error}\n"
                            f.write(error_line)
                            logger.error(f"CLIENT: {error}")
                            
                    # Log warnings
                    if 'warnings' in data and data['warnings']:
                        for warning in data['warnings']:
                            warning_line = f"{timestamp} - DASH WARNING: {warning}\n"
                            f.write(warning_line)
                            logger.warning(f"CLIENT: {warning}")
                            
                    # Log info messages
                    if 'logs' in data and data['logs']:
                        for log in data['logs']:
                            log_line = f"{timestamp} - DASH INFO: {log}\n"
                            f.write(log_line)
                            logger.info(f"CLIENT: {log}")
                            
                return jsonify({"status": "success", "message": "Logs saved to dash_errors.log"}), 200
            except Exception as e:
                logger.error(f"Error processing client logs: {e}", exc_info=True)
                # Również zapisz błąd do pliku
                with open('dash_errors.log', 'a', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp} - LOGGING ERROR: {str(e)}\n")
                    
                return jsonify({"status": "error", "message": str(e)}), 500
    else:
        logger.info("Route '/log-client-errors' already exists, skipping registration")

    # Application entry point
    if __name__ == "__main__":
        # Import the client-side logging
        from dash import html
        
        # Check for command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Run the Backtester application')
        parser.add_argument('--debug-client', action='store_true', default=True, help='Enable client-side debug logging')
        args = parser.parse_args()
        
        logger.info("Starting Backtester application")
        
        # Always enable client-side debug logging
        # Modify the app layout to include client-side debug component
        original_layout = app.layout
        app.layout = html.Div([
            configure_client_side_logging(),
            original_layout
        ])
        logger.info("Client-side debug logging enabled - browser console errors will be captured")
        
        # Register the client-side logging callback
        register_client_side_logging(app)
        
        app.run(debug=debug_mode, port=8050)

except ValueError as ve:
    if "invalid format" in str(ve).lower():
        logger.error("Format specification error in DataTable. Check all format strings in your table definitions.")
        logger.error("Common issues: Use dash_table.FormatTemplate.percentage(2) instead of '.2f%'")
        raise
    else:
        raise

except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    print(f"ERROR: Failed to initialize application: {e}")
    traceback.print_exc()
    # Display specific guidance for format errors
    if "invalid format" in str(e).lower():
        print("\nSUGGESTION: Check table format specifications in your code.")
        print("For percentages, use: dash_table.FormatTemplate.percentage(2) instead of string formats like '.2f%'")
        print("Likely locations to check:")
        print("- Files that define DataTable components")
        print("- Strategy result display components")
        print("- Performance metrics displays")
