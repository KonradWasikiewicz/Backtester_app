# This file makes Python treat the directory as a package.

print("--- Executing: src/ui/callbacks/__init__.py ---")

# Import standard callbacks
from src.ui.callbacks.backtest_callbacks import register_backtest_callbacks
from src.ui.callbacks.wizard_callbacks import register_wizard_callbacks

# Import the run_backtest_callback module directly
print("--- In __init__.py: Attempting to import register_run_backtest_callback ---")
try:
    from .run_backtest_callback import register_run_backtest_callback
    print("--- In __init__.py: Successfully imported register_run_backtest_callback ---")
    
    # Add to __all__ to make it available when importing from this package
    __all__ = ['register_backtest_callbacks', 'register_wizard_callbacks', 'register_run_backtest_callback']
except ImportError as e:
    print(f"--- In __init__.py: FAILED to import register_run_backtest_callback. Error: {e} ---")
    __all__ = ['register_backtest_callbacks', 'register_wizard_callbacks']

print("--- src/ui/callbacks/__init__.py finished execution ---")
