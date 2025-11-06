import logging
# local imports
from utils.utils import get_logger

logger = get_logger(__name__, logging.INFO)


def fetch_property(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    logger.info(f"### Finished {name}. ###")