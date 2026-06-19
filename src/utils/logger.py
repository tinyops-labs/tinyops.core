import logging
import logging.handlers
import os
from pathlib import Path


class TinyOpsLogger:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TinyOpsLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            self._initialized = True
    
    def _setup_logger(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('tinyops')
        self.logger.setLevel(logging.DEBUG)
        
        self.logger.handlers.clear()
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        log_file = log_dir / "tinyops.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        env_log_level = os.getenv("LOG_LEVEL")
        if env_log_level:
            try:
                console_handler.setLevel(getattr(logging, env_log_level, logging.INFO))
            except Exception:
                self.logger.error("Failed to set Log Level, allowed options are: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET")

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("TinyOps Logger initialized")
    
    def get_logger(self):
        return self.logger
    
    def get_log_file_path(self):
        return Path("logs/tinyops.log")


_logger_instance = TinyOpsLogger()


def get_logger():
    return _logger_instance.get_logger()


def get_log_file_path():
    return _logger_instance.get_log_file_path()


def debug(message):
    get_logger().debug(message)


def info(message):
    get_logger().info(message)


def warning(message):
    get_logger().warning(message)


def error(message):
    get_logger().error(message)


def critical(message):
    get_logger().critical(message)
