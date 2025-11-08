import os
import re
import sys
import json
import redis
import httpx
import shutil
import logging
import requests
from markdown_plain_text.extention import convert_to_plain_text

# limits
title_limit: int | None = 65536
description_limit: int | None = None
more_characters: str = "..."
id_limit: int = 128

logger = logging.getLogger(__name__)


def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def fetch_key_fron_json(file_path: str, key: str) -> str:
    """
    Fetch a specific key from a JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if key in data:
            return data[key]
        else:
            raise KeyError(f"Key '{key}' not found in {file_path}")


def get_files_with_postfix(folder_path: str, postfix: str = ".json", skip_files: list | None = None) -> list[str]:
    matched_files = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            if filename.endswith(postfix) and (skip_files is None or full_path not in skip_files):
                matched_files.append(full_path)
    return matched_files


def remove_html_tags(html_str: str) -> str:
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_str)


def shorten_text(text: str, limit: int, more_characters: str = "...") -> str:
    """
    Shorten the text to a given limit and add more characters if the text is longer than the limit.
    """
    text = convert_to_plain_text(text)
    if text.startswith("{}"):
        text = "{code:und}" + text[2:]
    return text[:limit] + more_characters if len(text) > limit else text


def shorten_list_or_string(long_text: str | list, limit: int | None, more_characters: str):
    """
    Shorten the text to the given limit and add more_characters at the end.
    """
    if limit is None:
        return long_text
    if isinstance(long_text, list):
        shortened = [shorten_text(elem, limit, more_characters) for elem in long_text]
    elif isinstance(long_text, str):
        shortened = shorten_text(long_text, limit, more_characters)
    else:
        raise TypeError(f"Name field is not a string or a list: {type(long_text)} - {long_text}")
    return shortened


def test_basex_connection(protocol: str,
                          host: str,
                          port: int,
                          user: str,
                          password: str) -> bool:
    """
    Tests connection to the BaseX server.
    Returns True if connection is successful, False otherwise.
    """
    response = call_basex(protocol, "", host, port, user, password, action="get")
    return 199 < response.status_code < 300


def call_basex_with_query(query: str,
                          protocol: str,
                          host: str,
                          port: int,
                          user: str,
                          password: str,
                          action: str,
                          db: str,
                          content_type: str = "application/json",
                          http_caller=requests
                          ) -> requests.Response:
    """
    This function calls the basex query

    file_path (str): The file path to the query to be executed
    host (str): The host of the basex server
    port (int): The port of the basex server
    user (str): The user of the basex server
    password (str): The password of the basex server

    return (str): The response of the basex query
    """
    query = query.replace("<js:", "&lt;js:")
    query = query.replace("</js:", "&lt;/js:")
    query = """
    <query>
        <text>
            {query}
        </text>
    </query>
    """.format(query=query)
    response = call_basex(protocol, query, host, port, user, password, action, db, content_type, http_caller)
    return response


def call_basex(protocol: str, query: str, host: str, port: int, user: str, password: str, action: str,
               db: str = None, content_type: str = "application/json", http_caller=requests,
               cooldown: int = 300) -> requests.Response:
    """
    This function calls the basex query

    query (str): The query to be executed
    host (str): The host of the basex server
    port (int): The port of the basex server
    user (str): The user of the basex server
    password (str): The password of the basex server

    return (str): The response of the basex query
    """
    if db:
        url: str = f"{protocol}://{user}:{password}@{host}:{port}/rest/{db}"
    else:
        url: str = f"{protocol}://{user}:{password}@{host}:{port}/rest"

    # print(f"Executing the basex query: {query} on {url=} with {action=} ...")
    # logger.info(f"Executing the basex query: {query} on {url=} with {action=} ...")
    if action == "get":
        response = http_caller.get(url, data=query, headers={"Content-Type": content_type})
    elif action == "post":
        response = http_caller.post(url, data=query, headers={"Content-Type": content_type})
    else:
        raise Exception(f"Invalid action {action}; Valid actions are 'get' and 'post'")

    return response


def backup_files(source_directory: str, backup_directory: str) -> None:
    """
    Make a backup copy of the previously downloaded JSON files.
    """
    if not os.path.exists(source_directory):
        logger.warning(f"Source directory does not exist, skipping backup: {source_directory}")
        return

    if not os.path.exists(backup_directory):
        logger.info(f"Creating backup directory: {backup_directory}")
        os.makedirs(backup_directory)

    for file_name in os.listdir(source_directory):
        source_file = os.path.join(source_directory, file_name)
        backup_file = os.path.join(backup_directory, file_name)
        if os.path.isfile(source_file):
            try:
                shutil.copy2(source_file, backup_file)
            except Exception as e:
                logger.error(f"Failed to copy {source_file} to {backup_file}: {e}")
    logger.info("Backup of previous JSON files created.")


def diff_files(file1: str | None, file2: str | None) -> bool:
    """
    Compare two files and return True if they are different, False otherwise.
    """
    if file1 is None:
        raise ValueError("file1 cannot be None")

    if file2 is None:
        return True

    if not os.path.exists(file1):
        raise FileNotFoundError(f"File not found: {file1}")

    if not os.path.exists(file2):
        return True

    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        content1 = f1.read()
        content2 = f2.read()
        return content1 != content2


def test_redis_connection(host: str | None, port: str | None, db: str | None) -> None:
    try:
        r = redis.Redis(host=host or "localhost", port=int(port or 6379), db=int(db or 0))
        r.ping()
        logger.debug("Redis connection successful.")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)


def delete_redis_key(host: str, port: int, db: int, key: str) -> None:
    """
    Delete a key from Redis database.
    """
    try:
        r = redis.Redis(host=host, port=port, db=db)
        r.delete(key)
        logger.info(f"Deleted Redis key: {key}")
    except Exception as e:
        logger.error(f"Failed to delete Redis key {key}: {e}")


def delete_redis_keys(host: str, port: int, db: int, keys: list[str]) -> None:
    """
    Delete multiple keys from Redis database.
    """
    try:
        r = redis.Redis(host=host, port=port, db=db)
        logger.info(f"Deleting Redis keys: {keys}")
        for key in keys:
            r.delete(key)
            logger.debug(f"Deleted Redis key: {key}")
    except Exception as e:
        logger.error(f"Failed to delete Redis keys: {e}")


def get_redis_key(host: str, port: int, db: int, key: str) -> dict | list | str | None:
    """
    Get a key from Redis database. Decodes JSON if possible.
    """
    try:
        r = redis.Redis(host=host, port=port, db=db)
        value = r.get(key)
        if value is None:
            logger.info(f"Redis key not found: {key}")
            return None
        value = value.decode("utf-8")
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        logger.error(f"Failed to get Redis key {key}: {e}")
        return None


def set_redis_key(host: str, port: int, db: int, key: str, value: str | dict | list) -> None:
    """
    Set a key in Redis database. Serializes dict or list to JSON.
    """
    try:
        r = redis.Redis(host=host, port=port, db=db)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        r.set(key, value)
        logger.info(f"Set Redis key: {key}")
    except Exception as e:
        logger.error(f"Failed to set Redis key {key}: {e}")


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
