"""Unified logging for the honk CLI."""

import os
import json
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE_PATH = os.path.expanduser("~/.local/state/honk/honk.log")

def setup_logging():
    """Configure the global logger for structured JSON logging."""
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("honk")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10*1024*1024, backupCount=5)
        formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "data": %(message)s}')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_event(event_type: str, data: dict):
    """Log a structured event to the global logger."""
    logger = logging.getLogger("honk")
    if not logger.handlers:
        setup_logging()
    
    log_message = json.dumps({"event_type": event_type, **data})
    logger.info(log_message)
