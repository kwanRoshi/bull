import sys
import os
from loguru import logger
from pathlib import Path

def setup_logger():
    """Setup logger with console and file handlers"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler for debug logs
    logger.add(
        "logs/debug.log",
        rotation="500 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[name]}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    # Add file handler for errors
    logger.add(
        "logs/error.log",
        rotation="100 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[name]}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        backtrace=True,
        diagnose=True
    )

def get_logger(name):
    """Get a logger instance with the given name"""
    setup_logger()
    return logger.bind(name=name) 