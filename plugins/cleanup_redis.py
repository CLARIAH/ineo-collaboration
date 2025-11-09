import json
import logging
# local imports
from utils.utils import get_logger, delete_redis_keys

logger = get_logger(__name__, logging.INFO)


def cleanup_redis(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    redis_host = params.get("redis_host", None)
    redis_port = params.get("redis_port", 6379)
    redis_db = params.get("redis_db", 0)
    keys_to_delete = params.get("keys_to_delete", [])

    if not redis_host or not keys_to_delete:
        logger.error("redis_host and keys_to_delete parameters are required.")
        return

    delete_redis_keys(redis_host, redis_port, redis_db, keys_to_delete)

    logger.info(f"### Finished {name}. ###")