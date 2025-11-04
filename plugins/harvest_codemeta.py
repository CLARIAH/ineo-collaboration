import logging
# local imports
from utils.utils import get_logger


logger = get_logger(__name__, logging.INFO)
def harvest_codemeta(name: str, params: dict[str, str]) -> None:
    logger.info(f"Harvesting: {name}")
    logger.info(f"Parameters: {params}")
