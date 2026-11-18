import logging
import sys

from app.core.config import settings


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(settings.PROJECT_NAME)
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logger()
