import logging
import os
import sys


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
