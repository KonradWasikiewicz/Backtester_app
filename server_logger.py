import os
import logging
import datetime
from flask import request, jsonify
from pathlib import Path
import json
import traceback
from logging.handlers import RotatingFileHandler

# Configure the logger
logger = logging.getLogger('dash_app')
logger.setLevel(logging.DEBUG)

def setup_logging():
    """Configure logging with rotation and formatting"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Main error log
    error_handler = RotatingFileHandler(
        log_dir / "dash_errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # Debug log
    debug_handler = RotatingFileHandler(
        log_dir / "dash_debug.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    
    # Format for all handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(exc_info)s\n'
    )
    error_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)

def log_client_errors_endpoint(app):
    """Add endpoint for client-side error logging"""
    def route_exists(route_path):
        return any(rule.rule == route_path for rule in app.server.url_map.iter_rules())
    
    if not route_exists('/log-client-errors'):
        @app.server.route('/log-client-errors', methods=['POST'])
        def log_client_errors():
            try:
                data = request.get_json(force=True)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Log errors with stack traces
                for error in data.get('errors', []):
                    error_msg = f"{timestamp} - DASH ERROR - {error.get('message', 'Unknown error')}"
                    if 'stack' in error:
                        error_msg += f"\nStack trace:\n{error['stack']}"
                    logger.error(error_msg)
                
                # Log warnings
                for warning in data.get('warnings', []):
                    warning_msg = f"{timestamp} - DASH WARNING - {warning.get('message', 'Unknown warning')}"
                    if 'stack' in warning:
                        warning_msg += f"\nStack trace:\n{warning['stack']}"
                    logger.warning(warning_msg)
                
                # Log debug messages
                for log in data.get('logs', []):
                    log_msg = f"{timestamp} - DASH LOG - {log.get('message', 'Unknown log')}"
                    logger.debug(log_msg)
                
                return jsonify({"status": "ok"}), 200
            except Exception as e:
                error_msg = f"Error logging client errors: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                return jsonify({"status": "error", "message": str(e)}), 500
        
        return True
    return False

def initialize_logger():
    """Initialize the logging system"""
    try:
        setup_logging()
        logger.info("Logging system initialized successfully")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to initialize logging: {str(e)}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}