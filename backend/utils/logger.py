# =============================================================================
# backend/utils/logger.py
#
# Structured JSON logger setup using structlog.
# =============================================================================

import logging
import structlog
import sys

def setup_logger():
    """
    Configures structlog to output machine-readable JSON logs in production,
    and pretty console logs in development.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging to pass through to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    return structlog.get_logger()

# Export a global logger instance
log = setup_logger()
