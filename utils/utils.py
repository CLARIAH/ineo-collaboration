import os
import re
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
