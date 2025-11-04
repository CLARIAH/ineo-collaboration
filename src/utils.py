import logging
import os
import re
import sys
import time
from tqdm import tqdm

import requests
from typing import List, Optional
from markdown_plain_text.extention import convert_to_plain_text

utils_logger_level = logging.WARNING


def get_logger(log_file: str, logger_name: str,
               level: int = utils_logger_level, logs_folder: str = "logs") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Ensure the "logs" folder exists
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    log_file = os.path.join(logs_folder, log_file)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add a stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    return logger


def get_files(folder_name: str, file_postfix: str = "json") -> Optional[List[str]]:
    """
    get all the files in the folder, if postfix is None
    :param folder_name: str
    :param file_postfix: str
    :return: List[str] | None in case of folder not exists

    """
    if not os.path.exists(folder_name):
        return None
    files_list = os.listdir(folder_name)

    # If file_postfix is None, return all the files
    if not file_postfix:
        return [os.path.join(folder_name, f) for f in files_list]

    # If file_postfix is not None, return the files with the postfix
    results: List[str] = []
    for f in files_list:
        if f.endswith(f".{file_postfix}"):
            results.append(os.path.join(folder_name, f))
    return results


def call_basex(query: str, host: str, port: int, user: str, password: str, action: str,
               db: str = None, content_type: str = "application/json", http_caller=requests, cooldown: int = 300) -> requests.Response:
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
        url: str = f"http://{user}:{password}@{host}:{port}/rest/{db}"
    else:
        url: str = f"http://{user}:{password}@{host}:{port}/rest"

    # print(f"Executing the basex query: {query} on {url=} with {action=} ...")
    # logger.info(f"Executing the basex query: {query} on {url=} with {action=} ...")
    if action == "get":
        response = http_caller.get(url, data=query, headers={"Content-Type": content_type})
    elif action == "post":
        response = http_caller.post(url, data=query, headers={"Content-Type": content_type})
    else:
        raise Exception(f"Invalid action {action}; Valid actions are 'get' and 'post'")

    return response


def call_basex_with_file(file_path: str,
                         host: str,
                         port: int,
                         user: str,
                         password: str,
                         action: str,
                         db: str) -> requests.Response:
    """
    This function calls the basex query

    file_path (str): The file path to the query to be executed
    host (str): The host of the basex server
    port (int): The port of the basex server
    user (str): The user of the basex server
    password (str): The password of the basex server

    return (str): The response of the basex query
    """
    with open(file_path, "r") as file:
        content = file.read()
        content = content.replace("<js:", "&lt;js:")
        content = content.replace("</js:", "&lt;/js:")
        query = """
        <query>
            <text>
                {query}
            </text>
        </query>
        """.format(query=content)
        response = call_basex(query, host, port, user, password, action, db)
    return response


def call_basex_with_query(query: str,
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
    response = call_basex(query, host, port, user, password, action, db, content_type, http_caller)
    return response


def get_ids_from_basex_by_query(query_file: str,
                                host: str = "basex",
                                port: int = 8080,
                                user: str = "admin",
                                password: str = "pass",
                                db: str = "tools") -> list[str]:
    """
    This function gets the IDs from the basex table by executing a query

    query_file (str): The file path to the query to be executed
    table_name (str): The name of the table to be queried

    return (list[str]): The list of IDs from the basex table
    """
    logger = get_logger("basex.log", "basex")
    logger.info(f"Getting IDs from basex table {db} by executing the query {query_file} ...")
    response = call_basex_with_file(file_path=query_file,
                                    host=host,
                                    port=port,
                                    user=user,
                                    password=password,
                                    action="post",
                                    db=db)
    if 199 < response.status_code < 300:
        logger.info(
            f"Status: {response.status_code} Got IDs from basex table {db} by executing the query {query_file} ...")
        return response.text
    else:
        logger.error(f"Failed to get IDs from basex table {db} by executing the query {query_file} ...")
        raise Exception(f"Failed to get IDs from basex table {db} by executing the query {query_file} ...")


def remove_html_tags(text):
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def shorten_text(text: str, limit: int, more_characters: str = "...") -> str:
    """
    Shorten the text to a given limit and add more characters if the text is longer than the limit.
    """
    text = convert_to_plain_text(text)
    if text.startswith("{}"):
        text = "{code:und}" + text[2:]
    return text[:limit] + more_characters if len(text) > limit else text


def shorten_list_or_string(long_text: str | list, limit: int, more_characters: str):
    """
    Shorten the text to the given limit and add more_characters at the end.
    """
    if isinstance(long_text, list):
        shortened = [shorten_text(elem, limit, more_characters) for elem in long_text]
    elif isinstance(long_text, str):
        shortened = shorten_text(long_text, limit, more_characters)
    else:
        raise TypeError(f"Name field is not a string or a list: {type(long_text)} - {long_text}")
    return shortened


def get_id_from_file_name(file_name: str) -> str:
    parts = file_name.split(".")[0:-1]
    parts = ".".join(parts)
    # return file_name.split(".")[0:-1].split("/")[-1]
    return parts.split("/")[-1]
