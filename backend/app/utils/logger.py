"""
Logging utilities for the application.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "%(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(levelname)s - %(message)s" + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default application logger
logger = setup_logger(
    name="modeling_platform",
    level=logging.INFO
)


# Request logger for API endpoints
request_logger = setup_logger(
    name="modeling_platform.requests",
    level=logging.INFO
)


# Database logger
db_logger = setup_logger(
    name="modeling_platform.db",
    level=logging.INFO
)


# Graph database logger
graph_logger = setup_logger(
    name="modeling_platform.graph",
    level=logging.INFO
)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[int] = None
) -> None:
    """
    Log an HTTP request.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
    """
    user_info = f"user_id={user_id}" if user_id else "anonymous"
    request_logger.info(
        f"{method} {path} - {status_code} - {duration_ms:.2f}ms - {user_info}"
    )


def log_db_query(
    operation: str,
    table: str,
    duration_ms: float,
    success: bool = True
) -> None:
    """
    Log a database query.
    
    Args:
        operation: Type of operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Query duration in milliseconds
        success: Whether query was successful
    """
    status = "SUCCESS" if success else "FAILED"
    db_logger.info(
        f"{operation} {table} - {status} - {duration_ms:.2f}ms"
    )


def log_graph_query(
    operation: str,
    query: str,
    duration_ms: float,
    success: bool = True
) -> None:
    """
    Log a graph database query.
    
    Args:
        operation: Type of operation
        query: Cypher query (truncated if too long)
        duration_ms: Query duration in milliseconds
        success: Whether query was successful
    """
    status = "SUCCESS" if success else "FAILED"
    truncated_query = query[:100] + "..." if len(query) > 100 else query
    graph_logger.info(
        f"{operation} - {status} - {duration_ms:.2f}ms - {truncated_query}"
    )