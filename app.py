import sys
import logging
import traceback
from pathlib import Path
import os
import re

# Ensure src is in the path
APP_ROOT = Path(__file__).resolve().parent
sys.path.append(str(APP_ROOT))

# Funkcja upraszczająca logowanie błędów Dash
def configure_client_side_logging():
    """
    Konfiguruje logowanie błędów po stronie klienta.
    Skrypt JavaScript jest ładowany automatycznie z folderu assets.
    """
    return html.Div([
        html.Div(id='client-error-container'),
        # Dodajemy komponent store, który będzie używany do odbierania błędów z localStorage
        dcc.Store(id='dash-errors-store'),
    ])

# Funkcja dodająca endpoint do odczytu localStorage
def add_browser_storage_reader(app):
    """
    Dodaje endpoint do odczytywania błędów z localStorage przeglądarki.
    """
    # Sprawdź, czy trasa już istnieje
    def route_exists(route_path):
        return any(rule.rule == route_path for rule in app.server.url_map.iter_rules())
    
    # Dodaj specjalny plik JavaScript do każdego żądania HTML
    @app.server.after_request
    def add_js_to_html(response):
        if response.content_type and 'text/html' in response.content_type:
            script_tag = '''
            <script type="text/javascript">
            (function() {
                function sendStoredErrorsToServer() {
                    const STORAGE_KEY = 'dashErrorLogs';
                    const logs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                    
                    if (logs.length > 0) {
                        fetch('/log-client-errors', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                errors: logs.filter(log => log.type === 'error'),
                                warnings: logs.filter(log => log.type === 'warning'),
                                logs: logs.filter(log => log.type === 'info')
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'ok') {
                                console.log(`Zapisano ${logs.length} logów do pliku na serwerze`);
                                localStorage.removeItem(STORAGE_KEY);
                                localStorage.removeItem('hasNewDashErrors');
                            }
                        })
                        .catch(error => console.error('Błąd wysyłania logów:', error));
                    }
                }
                
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', sendStoredErrorsToServer);
                } else {
                    sendStoredErrorsToServer();
                }
            })();
            </script>
            '''
            
            response.data = response.data.replace(b'</body>', script_tag.encode('utf-8') + b'</body>')
            
        return response
    
    # Register the client error logging endpoint
    log_client_errors_endpoint(app)
    
    logger.info("Zarejestrowano endpoint /log-client-errors")
    return True

# Import factory functions
try:
    from src.ui.app_factory import (
        create_app,
        configure_logging,
        create_app_layout,
        register_callbacks,
        register_version_callbacks,
        register_debug_callbacks
    )
    from dash import html, dcc
    from server_logger import initialize_logger, log_client_errors_endpoint
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Initialize the enhanced logging system
logging_result = initialize_logger()
if logging_result["status"] == "error":
    print(f"Failed to initialize logging: {logging_result['message']}")
    sys.exit(1)

# Configure application logging
configure_logging()
logger = logging.getLogger(__name__)

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

try:
    # Create the Dash application
    app = create_app(suppress_callback_exceptions=True)

    # Register client errors endpoint
    log_client_errors_endpoint(app)

    # Register all callbacks
    register_callbacks(app)
    register_version_callbacks(app)
    register_debug_callbacks(app)
    
    # Register wizard callbacks
    from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks
    register_wizard_callbacks(app)

    # Get the original layout
    original_layout = create_app_layout()

    # Add error logging components to the original layout
    app.layout = html.Div([
        # Error logging components
        html.Div([
            dcc.Store(id='error-store', storage_type='local'),
            html.Div(id='error-notifier', style={'display': 'none'}),
        ]),
        
        # Original layout
        original_layout
    ])

    # Configure client-side error logging
    configure_client_side_logging()
    add_browser_storage_reader(app)

    if __name__ == '__main__':
        app.run(debug=True, dev_tools_hot_reload=False)

except Exception as e:
    logger.error(f"Error initializing application: {e}", exc_info=True)
    print(f"Error initializing application: {e}")
    traceback.print_exc()
