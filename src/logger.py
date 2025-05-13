"""
Logging system for the Prod CLI tool.
"""
import logging
import os
from datetime import datetime
from typing import Optional


class Logger:
    """
    Handles logging functionality with support for multiple verbosity levels and log rotation.
    """
    def __init__(self, log_level: str = 'INFO', log_file: Optional[str] = None):
        """
        Initializes the logger with the specified log level and file.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to the log file, if None logs will only be sent to console
        """
        self.logger = self._setup_logger(log_level, log_file)
    
    def _setup_logger(self, log_level: str, log_file: Optional[str] = None):
        """
        Sets up the logging system.
        
        Args:
            log_level: Logging level
            log_file: Path to the log file
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('prod')
        
        # Clear any existing handlers
        if logger.handlers:
            logger.handlers.clear()
            
        # Set log level
        logger.setLevel(getattr(logging, log_level))
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler if log file is specified
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: Message to log
        """
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Message to log
        """
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Message to log
        """
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """
        Log a critical message.
        
        Args:
            message: Message to log
        """
        self.logger.critical(message)
    
    def set_log_level(self, log_level: str) -> None:
        """
        Set the log level.
        
        Args:
            log_level: New log level
        """
        self.logger.setLevel(getattr(logging, log_level))
    
    @staticmethod
    def get_log_file_path(production: Optional[str] = None) -> str:
        """
        Get a path for the log file based on the date and production.
        
        Args:
            production: Production name
            
        Returns:
            Path to the log file
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_dir = os.path.expanduser('~/.prod/logs')
        
        if production:
            log_dir = os.path.join(log_dir, production)
            
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        return os.path.join(log_dir, f'prod_{date_str}.log') 