#!/usr/bin/env python3
"""
Logging Utility - Centralized logging system
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory
logs_dir = Path(__file__).parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Log file path
log_file = logs_dir / f"upwork_assistant_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logger(name: str = 'upwork_assistant', level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Default logger instance
logger = setup_logger()

