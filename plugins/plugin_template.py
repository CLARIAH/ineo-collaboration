import json
import logging
# local imports
from utils.utils import get_logger

logger = get_logger(__name__, logging.INFO)


def plugin_template(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    logger.info(f"### Finished {name}. ###")