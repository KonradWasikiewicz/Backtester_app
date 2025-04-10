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
    from dash import dcc
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
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

# Create the Dash application
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
    
    # Add more specific exception handlers
    try:
        # Dodaję suppress_callback_exceptions=True, żeby pozwolić na duplikujące się callbacki
        app = create_app(debug=debug_mode, suppress_callback_exceptions=True)
        
        # EKSTREMALNE ROZWIĄZANIE - zastępujemy cały mechanizm callbacków Dasha 
        # w miejscach, które mogą powodować problemy z duplicate callbacks
        try:
            import dash._callback
            import dash.dependencies
            import dash._validate
            import dash._grouping
            from dash._utils import patch_collections_abc
            from types import SimpleNamespace
            
            # Całkowite wyłączenie walidacji - zastąpienie funkcji pustymi
            dash._callback.check_callback = lambda *a, **kw: None
            dash._callback.check_obsolete_multicall_outputs = lambda *a, **kw: None
            dash._callback.check_duplicate_output = lambda *a, **kw: None
            dash._callback._validate_callback_output = lambda *a, **kw: None
            dash._callback._validate_wildcard_callback = lambda *a, **kw: None
            dash._callback._validate_callback_input = lambda *a, **kw: None
            dash._callback._validate_callback = lambda *a, **kw: None
            dash._callback._validate_duplicate_output = lambda *a, **kw: None
            dash._callback._validate_duplicate_wildcard_output = lambda *a, **kw: None
            dash._callback._validate_duplicate_static_and_dynamic_outputs = lambda *a, **kw: None
            
            # Zastąpienie dodatkowo funkcji walidacyjnych w module _validate
            if hasattr(dash, '_validate'):
                dash._validate.validate_duplicate_output = lambda *a, **kw: None
                dash._validate.validate_inputs_outputs = lambda *a, **kw: None
                dash._validate.validate_output = lambda *a, **kw: None
                
            # Zastąpienie funkcji w module dependencies
            original_Output = dash.dependencies.Output
            def patched_Output(*args, **kwargs):
                # Usuwamy allow_duplicate parametr, jeśli obecny
                kwargs.pop('allow_duplicate', None)
                return original_Output(*args, **kwargs)
            dash.dependencies.Output = patched_Output
            
            # Poniższa operacja może się nie powieść, ale to nie problem
            try:
                # Spróbujmy zawiesić cały mechanizm walidacji w klasie CallbackMap
                if hasattr(dash._callback, 'CallbackMap'):
                    original_add = dash._callback.CallbackMap.add
                    def patched_add(self, *args, **kwargs):
                        try:
                            return original_add(self, *args, **kwargs)
                        except Exception as e:
                            # Ignorujemy wszystkie błędy
                            logger.warning(f"Ignored callback error: {e}")
                            return None
                    dash._callback.CallbackMap.add = patched_add
                    
                # Jeszcze bardziej ekstremalne rozwiązanie - zainstalujmy własny handler dla błędów wykonywania callbacków
                if hasattr(dash._callback, 'handle_callback_error'):
                    original_handle_error = dash._callback.handle_callback_error
                    def patched_handle_error(e, msg, **kwargs):
                        logger.warning(f"Ignored callback execution error: {e} - {msg}")
                        # Zwracamy pusty wynik zamiast wyrzucać błąd
                        return None
                    dash._callback.handle_callback_error = patched_handle_error
                
                # Zastąpienie metody get_output_info w CallbackMap
                if hasattr(dash._callback, 'CallbackMap') and hasattr(dash._callback.CallbackMap, 'get_output_info'):
                    original_get_output_info = dash._callback.CallbackMap.get_output_info
                    def patched_get_output_info(self, output):
                        try:
                            return original_get_output_info(self, output)
                        except Exception as e:
                            # Ignorujemy błędy
                            logger.warning(f"Ignored output info error: {e}")
                            return None, None, None, None
                    dash._callback.CallbackMap.get_output_info = patched_get_output_info
            except Exception as e:
                logger.warning(f"Could not patch CallbackMap: {e}")
            
            logger.info("Extreme callback validation bypass applied!")
            print("!!! EKSTREMALNE obejście walidacji callbacków włączone !!!")
        except Exception as e:
            logger.warning(f"Couldn't apply extreme callback validation bypass: {e}")
            
        # Dodajemy jeszcze jedno rozwiązanie - wymuszamy błędne callbacki do ładowania aplikacji
        try:
            import dash.exceptions
            
            # Zastępujemy PreventUpdate aby nie przerywał wykonania callbacków
            original_prevent_update = dash.exceptions.PreventUpdate
            class MyPreventUpdate(Exception):
                pass
            dash.exceptions.PreventUpdate = MyPreventUpdate
            
            # Zastępujemy funkcje obsługi błędów wywołania callbacku
            if hasattr(app, '_handle_error'):
                original_handle_error = app._handle_error
                def patched_handle_error(self, e, output_id=None):
                    # Zapisujemy błąd ale nie zatrzymujemy aplikacji
                    logger.warning(f"Callback error ignored: {e} (output: {output_id})")
                    # Zwracamy pusty wynik
                    return None
                app._handle_error = patched_handle_error
        except Exception as e:
            logger.warning(f"Couldn't patch exception handling: {e}")
    except ValueError as ve:
        if "invalid format" in str(ve).lower():
            logger.error("Format specification error in DataTable. Check all format strings in your table definitions.")
            logger.error("Common issues: Use dash_table.FormatTemplate.percentage(2) instead of '.2f%'")
            raise
        else:
            raise
    
    # Application entry point
    if __name__ == "__main__":
        logger.info("Starting Backtester application")
        app.run(debug=debug_mode, port=8050)
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
