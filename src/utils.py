import logging
import os
import sys
from typing import List, Optional


def get_logger(log_file: str, logger_name: str,
               level: int = logging.DEBUG, logs_folder: str = "logs") -> logging.Logger:
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
        if f.endswith('.json'):
            results.append(os.path.join(folder_name, f))
    return results
