import sys
import logging
# local imports
from utils.utils import (get_logger, get_redis_key, set_redis_key,
                         delete_redis_key, get_files_with_postfix, get_identifier)

logger = get_logger(__name__, logging.INFO)


def get_file_list(paths: list) -> dict:
    """

    """
    all_files = {
        # identifier: [file_path, type]
    }
    for file_path in paths:
        new_files = get_files_with_postfix(file_path, ".json")
        # Check each new file against its previous version
        for file in new_files:
            identifier = get_identifier(file, ["id", "identifier"])
            all_files[identifier] = file
    return all_files


def update_redis_key(redis_host: str, redis_port: int, redis_db: int, redis_key: str, new_data: dict) -> None:
    """
    Update a Redis key with new data by merging dictionaries.
    """
    existing_data = get_redis_key(redis_host, redis_port, redis_db, redis_key)
    if existing_data is None:
        existing_data = {}

    # Merge new data into existing data
    for k, v in new_data.items():
        existing_data[k] = v

    # Set the updated data back to Redis
    try:
        set_redis_key(redis_host, redis_port, redis_db, redis_key, existing_data)
        logger.info(f"Updated Redis key {redis_key} with {len(new_data)} new entries. Total now: {len(existing_data)}")
    except Exception as e:
        logger.error(f"Failed to set Redis key {redis_key} after updating: {e}")


def get_updated_ruc(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    redis_host = params.get("redis_host", None)
    redis_port = params.get("redis_port", None)
    redis_db = params.get("redis_db", None)
    files_path = params.get("files_path", [])
    to_merge = params.get("to_merge", None)
    if to_merge:
        to_merge_key = to_merge.get("redis_key", None)
        merge_with_key = to_merge.get("merge_with", None)
    else:
        raise ValueError("to_merge parameter is required.")

    updated_ruc = get_redis_key(redis_host, int(redis_port), int(redis_db), to_merge_key)
    updated_files = get_redis_key(redis_host, int(redis_port), int(redis_db), merge_with_key)

    if updated_ruc is None:
        logger.info(f"No RUC to update")
        return

    all_files = get_file_list(files_path)
    logger.info(f"Total files available for RUC update: {len(all_files)}; all_files sample: {list(all_files.items())[:1]}")
    # Merge RUC datasets to updated_keys and set the path rightly
    for ruc_id, _ in updated_ruc.items():
        if ruc_id in all_files.keys():
            updated_files[ruc_id] = (all_files[ruc_id],)
        else:
            logger.warning(f"RUC ID {ruc_id} not found in provided file paths.")
    logger.info(f"Merging {len(updated_ruc)} RUC entries into {len(updated_files)} updated_files ... {list(updated_files.items())[-1]}")


    # debugging
    # for k, v in updated_files.items():
    #     try:
    #         if len(v) < 2:
    #             print(f"{k}: {v}")
    #     except IndexError:
    #         print(f"{k}: {v}")
    #         exit()
    # exit()


    # # Delete to merge key after merging
    delete_redis_key(redis_host, int(redis_port), int(redis_db), to_merge_key)
    # # Delete and update the merged key
    update_redis_key(redis_host, int(redis_port), int(redis_db), merge_with_key, updated_files)
    logger.info(f"### Finished {name}. ###")