"""Logging configuration with auto-rotation and cleanup."""

import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from bot.config import get_settings


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""
    
    SENSITIVE_PATTERNS = [
        "api_key",
        "password",
        "secret",
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log message."""
        msg = str(record.msg)
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern.lower() in msg.lower():
                record.msg = "[REDACTED]"
        return True


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    
    # Set log level
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create formatters
    if settings.log_format == "json":
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if settings.log_file_enabled:
        log_dir = Path(settings.log_file_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(file_handler)
        
        # Cleanup old logs
        cleanup_old_logs(log_dir, settings.log_file_retention_days)
    
    # Reduce noise from libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def cleanup_old_logs(log_dir: Path, retention_days: int) -> None:
    """Delete log files older than retention period."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    for log_file in log_dir.glob("*.log*"):
        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff:
                log_file.unlink()
                logging.debug(f"Deleted old log file: {log_file}")
        except Exception as e:
            logging.warning(f"Failed to delete log file {log_file}: {e}")
