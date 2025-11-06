import os
import sys
import json
import redis
import logging
# local imports
from utils.utils import (get_logger, diff_files, get_files_with_postfix,
                         delete_redis_key, get_redis_key, test_redis_connection, fetch_key_fron_json, set_redis_key)

logger = get_logger(__name__, logging.INFO)


def get_identifier(file_path: str, field_names: list) -> str:
    """
    Extract the identifier from the file name.
    Assumes the identifier is the file name without extension.
    """
    for field_name in field_names:
        try:
            identifier = fetch_key_fron_json(file_path, field_name)
            return identifier
        except:
            continue

    base_name = os.path.basename(file_path)
    identifier, _ = os.path.splitext(base_name)
    if not identifier:
        logger.error(f"Could not extract identifier from file: {file_path}")
        sys.exit(1)
    return identifier


def get_previous_file(current_file: str, previous_files_path: str) -> str | None:
    """
    Get the corresponding previous file path based on the current file name.
    """
    base_name = os.path.basename(current_file)
    previous_file = os.path.join(previous_files_path, base_name)
    if os.path.exists(previous_file):
        return previous_file
    else:
        return None


def get_updated_files(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    redis_host = params.get("redis_host", None)
    redis_port = params.get("redis_port", None)
    redis_db = params.get("redis_db", None)
    datasets = params.get("data_types", None)

    if not (redis_host and redis_port and redis_db is not None and datasets):
        logger.error("Missing required parameters for Redis connection or datasets.")
        logger.error(f"redis_host: {redis_host}, redis_port: {redis_port}, redis_db: {redis_db}, datasets: {datasets}")
        sys.exit(1)

    test_redis_connection(redis_host, redis_port, redis_db)

    # Process each type of dataset defined in the configuration
    for dataset in datasets:
        updated_keys = {
            # identifier: [file_path, type]
        }
        dataset_type = dataset.get("name", None)
        new_files_path = dataset.get("new_files_path", None)
        previous_files_path = dataset.get("previous_files_path", None)
        redis_key = dataset.get("redis_key", None)
        remove_key_before_update = dataset.get("remove_key_before_update", True)

        # preserve the existing key before deleting if specified
        if not remove_key_before_update:
            updated_keys = get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)
        delete_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)

        logger.info(f"updated_keys before processing {dataset_type}: {len(updated_keys)} entries.")
        new_files = get_files_with_postfix(new_files_path, ".json")
        # Check each new file against its previous version
        for file in new_files:
            logger.debug(f"Processing file: {file}")
            identifier = get_identifier(file, ["id", "identifier"])
            logger.debug(f"Extracted identifier: {identifier}")
            previous_file = get_previous_file(file, previous_files_path)
            if diff_files(file, previous_file):
                updated_keys[identifier] = [file, dataset_type]
                logger.debug(f"File updated: {file} (Identifier: {identifier})")
        logger.debug(f"Found {len(updated_keys)} updated files for dataset type: {dataset_type}")

        # Store updated keys back to Redis
        redis_value = json.dumps(updated_keys)
        try:
            set_redis_key(redis_host, int(redis_port), int(redis_db), redis_key, redis_value)
        except Exception as e:
            logger.error(f"Failed to set Redis key {redis_key}: {e}")
            sys.exit(1)
        if len(updated_keys.keys()) > 0:
            logger.info(f"Sample updated keys: {list(updated_keys.items())[:1]}")
            logger.info(
                f"Found {len(get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key))} updated keys in Redis for key: {redis_key}")
        logger.info("\n\n")

    logger.info(f"### Finished {name}. ###")
