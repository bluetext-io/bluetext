import os
import sys
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime


class EnvironmentLogger:
    """
    Environment-aware logger that outputs different formats based on environment.
    
    - development: Human-readable format with colors and emojis
    - staging/production: Structured JSON format for log aggregation
    """
    
    def __init__(self, name: str, environment: Optional[str] = None):
        self.name = name
        self.environment = environment or os.getenv('ENVIRONMENT', 'development').lower()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger based on environment."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level from environment
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, log_level, logging.INFO)
        self.logger.setLevel(level)
        
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Set formatter based on environment
        if self.environment in ['production', 'prod', 'staging']:
            handler.setFormatter(self._get_json_formatter())
        else:
            handler.setFormatter(self._get_development_formatter())
        
        self.logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _get_development_formatter(self):
        """Human-readable formatter for development."""
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': '\033[36m',      # Cyan
                'INFO': '\033[32m',       # Green
                'WARNING': '\033[33m',    # Yellow
                'ERROR': '\033[31m',      # Red
                'CRITICAL': '\033[35m',   # Magenta
                'ENDC': '\033[0m',        # End color
            }
            
            def format(self, record):
                level_color = self.COLORS.get(record.levelname, '')
                end_color = self.COLORS['ENDC']
                
                # Format timestamp
                timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
                
                # Create colored level name
                colored_level = f"{level_color}{record.levelname:8s}{end_color}"
                
                # Format module name
                module_name = record.name if record.name != '__main__' else 'main'
                
                return f"[{timestamp}] {colored_level} [{module_name}] {record.getMessage()}"
        
        return ColoredFormatter()
    
    def _get_json_formatter(self):
        """JSON formatter for production/staging."""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'module': record.name,
                    'message': record.getMessage(),
                    'environment': os.getenv('ENVIRONMENT', 'unknown')
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                # Add extra fields if present
                if hasattr(record, 'extra') and record.extra:
                    log_entry.update(record.extra)
                
                return json.dumps(log_entry)
        
        return JsonFormatter()
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.critical(message, extra=extra)
    
    def exception(self, message: str, **kwargs):
        """Log exception with stack trace."""
        extra = {'extra': kwargs} if kwargs else {}
        self.logger.exception(message, extra=extra)


def get_logger(name: str) -> EnvironmentLogger:
    """
    Factory function to get an environment-aware logger.
    
    Args:
        name: Logger name (usually __name__ or module name)
        
    Returns:
        Configured EnvironmentLogger instance
    """
    return EnvironmentLogger(name)