"""
Application Logging Configuration.
Sets up structured console logging with sensitive data masking.
"""

import logging
import sys
from typing import Optional


class SensitiveFilter(logging.Filter):
    """Ensure sensitive credentials and tokens are masked in log records."""

    SENSITIVE_KEYS = ["api_key", "secret", "token", "password", "authorization"]

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.getMessage()).lower()
        for key in self.SENSITIVE_KEYS:
            if f"{key}=" in message or f'"{key}"' in message:
                record.msg = "[LOG FILTERED: SENSITIVE DATA DETECTED]"
                record.args = ()
                break
        return True


def setup_logging(log_level: Optional[str] = "INFO") -> logging.Logger:
    """Configure root and application loggers."""
    numeric_level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    for handler in logging.root.handlers:
        handler.addFilter(SensitiveFilter())

    logger = logging.getLogger("sahayakai")
    logger.setLevel(numeric_level)
    return logger
