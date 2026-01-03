"""
Logging configuration for Visitor Management System.
Sets up structured logging with console and file handlers.
"""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(app=None, log_level='INFO', log_file='app.log'):
    """
    Configure application logging.
    
    Args:
        app: Flask application instance (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
    if log_dir and log_dir != 'logs':
        os.makedirs(log_dir, exist_ok=True)
    elif log_dir == 'logs':
        os.makedirs('logs', exist_ok=True)
        log_file = os.path.join('logs', os.path.basename(log_file))
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler with rotation (max 10MB per file, keep 5 backups)
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.warning(f"Could not create file handler: {e}")
    
    # Configure Flask app logger if provided
    if app:
        app.logger.setLevel(numeric_level)
        # Flask will use the root logger handlers
    
    # Log startup message
    logging.info("=" * 60)
    logging.info("Visitor Management System - Logging Initialized")
    logging.info(f"Log Level: {log_level}")
    logging.info(f"Log File: {log_file}")
    logging.info("=" * 60)
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
