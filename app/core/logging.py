import logging
import sys

logger = logging.getLogger(__name__)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    # Confirm the active level without exposing any environment configuration values.
    logger.info("Application logging configured level=%s", level.upper())
