import pytest
import os
import shutil
from pathlib import Path
from crypto_twitter_bot.logger import get_logger

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup and cleanup for logger tests"""
    # Setup
    if Path("logs").exists():
        shutil.rmtree("logs")
    
    yield
    
    # Cleanup
    if Path("logs").exists():
        shutil.rmtree("logs")

def test_logger_directory_creation():
    """Test that the logs directory is created"""
    assert not Path("logs").exists()
    _ = get_logger("test")
    assert Path("logs").exists()
    assert Path("logs/debug.log").exists()
    assert Path("logs/error.log").exists()

def test_logger_instance():
    """Test logger instance creation and basic functionality"""
    logger = get_logger("test_module")
    assert logger is not None
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Verify log files exist and have content
    assert os.path.getsize("logs/debug.log") > 0
    assert os.path.getsize("logs/error.log") > 0

def test_logger_error_with_exception():
    """Test error logging with exception"""
    logger = get_logger("test_exception")
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        logger.error("Error occurred: {}", e)
    
    # Verify error was logged
    assert os.path.getsize("logs/error.log") > 0

def test_logger_name_binding():
    """Test that logger name is properly bound"""
    test_name = "test_binding"
    logger = get_logger(test_name)
    
    # Log a message and verify it contains the module name
    logger.info("Test message")
    
    with open("logs/debug.log", "r") as f:
        log_content = f.read()
        assert test_name in log_content 