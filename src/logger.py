"""
Advanced Logging System for VibeCode Bot
Provides colorized console output and file logging with rotation
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog
from rich.console import Console
from rich.logging import RichHandler


class AdvancedLogger:
    """Advanced logging system with color support and file rotation"""
    
    def __init__(self, name: str = "VibeCodeBot", log_dir: str = "./logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.console = Console()
        
        # Create main logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_handler()
    
    def _setup_console_handler(self):
        """Setup colorized console handler"""
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(logging.INFO)
        
        # Color formatter
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        console_handler.setFormatter(color_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup rotating file handler for general logs"""
        log_file = self.log_dir / f"{self.name.lower()}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_error_handler(self):
        """Setup separate handler for errors"""
        error_file = self.log_dir / f"{self.name.lower()}_errors.log"
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d\n'
            'Message: %(message)s\n'
            'Exception: %(exc_info)s\n'
            '---\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def log_code_generation(self, user_id: str, prompt: str, success: bool):
        """Log code generation attempts"""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"CODE_GEN [{status}] User: {user_id} | Prompt: {prompt[:100]}...")
    
    def log_code_test(self, project_name: str, test_result: dict):
        """Log code testing results"""
        status = "PASS" if test_result.get('success', False) else "FAIL"
        errors = len(test_result.get('errors', []))
        self.info(f"CODE_TEST [{status}] Project: {project_name} | Errors: {errors}")
    
    def log_correction_attempt(self, project_name: str, attempt: int, strategy: str):
        """Log code correction attempts"""
        self.info(f"CODE_CORRECTION Attempt {attempt} | Project: {project_name} | Strategy: {strategy}")
    
    def log_user_command(self, user_id: str, username: str, command: str, guild_id: Optional[str] = None):
        """Log user commands"""
        guild_info = f"Guild: {guild_id}" if guild_id else "DM"
        self.info(f"COMMAND | User: {username} ({user_id}) | {guild_info} | Command: {command}")
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics"""
        details_str = f" | Details: {details}" if details else ""
        self.info(f"PERFORMANCE | Operation: {operation} | Duration: {duration:.2f}s{details_str}")


# Global logger instance
logger = AdvancedLogger()


def get_logger(name: str = None) -> AdvancedLogger:
    """Get logger instance"""
    if name:
        return AdvancedLogger(name)
    return logger