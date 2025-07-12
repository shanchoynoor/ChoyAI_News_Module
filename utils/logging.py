"""
Logging configuration for the Choy News application.

This module provides standardized logging setup for all components.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from .config import Config

def setup_logging(name, log_file=None):
    """
    Set up logging for a module with appropriate formatting and handlers.
    
    Args:
        name: The logger name (typically __name__ from the calling module)
        log_file: Optional specific log file path (defaults to Config.LOG_FILE)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # If no specific log file is provided, use the default from config
    if log_file is None:
        log_file = Config.LOG_FILE
        
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Get logger for the given name
    logger = logging.getLogger(name)
    
    # Only set up handlers if they haven't been added yet
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Set formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler with rotation
        file_handler = RotatingFileHandler(
            log_file, 
            mode='a',
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """
    Get a logger that's already been set up.
    
    Args:
        name: The logger name (typically the module name)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
