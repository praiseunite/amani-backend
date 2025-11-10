"""
Logging configuration for structured logging and audit trails.
"""
import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    """
    Configure structured logging for the application.
    Supports both console and file logging with JSON formatting for audits.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # JSON Formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler (human-readable for development)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "development":
        # Use simple format for development
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
    else:
        # Use JSON format for production
        console_handler.setFormatter(json_formatter)
    
    logger.addHandler(console_handler)
    
    # File Handler (JSON format for auditing)
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Log startup information
    logger.info(
        "Logging initialized",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "log_file": settings.LOG_FILE
        }
    )
    
    return logger


# Initialize logging
app_logger = setup_logging()
