import json
import logging
# local imports
from utils.utils import get_logger, get_redis_key

logger = get_logger(__name__, logging.INFO)


def generate_ineo_record(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    # logger.info(f"Parameters: {params}")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    redis_host = params.get("redis_host", None)
    redis_port = params.get("redis_port", None)
    redis_db = params.get("redis_db", None)
    redis_key = params.get("redis_key", None)
    basex_protocol = params.get("basex_protocol", None)
    basex_host = params.get("basex_host", None)
    basex_port = params.get("basex_port", None)
    basex_user = params.get("basex_user", None)
    basex_password = params.get("basex_password", None)
    ruc_path = params.get("ruc_path", None)
    datasets = params.get("datasets", None)

    # Fetch updated files from Redis
    updated_files = get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)
    logger.info(f"Fetched {len(updated_files)} updated files from Redis.")

    counters = {}
    for identifier, file_info in list(updated_files.items()):
        if len(file_info) == 1:
            file_path = file_info[0]
            file_type = "unknown"
        elif len(file_info) == 2:
            file_path = file_info[0]
            file_type = file_info[1]
        else:
            logger.warning(f"Unexpected file info format for {identifier}: {file_info}")
            continue

        if file_type == "unknown":
            logger.info(f"Processing file: {identifier} with {file_info} bytes")
        if file_type not in counters:
            counters[file_type] = 1
        else:
            counters[file_type] += 1

    logger.info(f"Processing summary: {json.dumps(counters, indent=2)}")




    logger.info(f"### Finished {name}. ###")