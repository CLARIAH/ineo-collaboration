import os
import json
import httpx
import shutil
import logging
from typing import List
from bs4 import BeautifulSoup
# local imports
from utils.utils import get_logger, shorten_list_or_string, title_limit, description_limit, more_characters

logger = get_logger(__name__, logging.INFO)


def backup_json_files(source_directory: str, backup_directory: str) -> None:
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


def download_json_files(url: str, save_directory: str, backup_directory: str) -> List[str]:
    """
    Download and count all individual json files using beautifulsoup to harvest contents from the given URL.

    """
    # first backup previous JSON files
    backup_json_files(save_directory, backup_directory)

    files_list = []

    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = httpx.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    count = 0

    for link in links:
        href = link.get('href')
        if href.endswith('.codemeta.json'):
            file_url = url + href
            logger.debug(f"Downloading {file_url}")
            response = httpx.get(file_url)
            file_name = os.path.join(save_directory, href)
            files_list.append(file_name)
            # loads binary response content as string and dump it to json file
            with open(file_name, 'w') as file:
                content = response.content.decode('utf-8')
                content_json = json.loads(content)
                # shorten name and description
                content_json["name"] = shorten_list_or_string(content_json.get("name", ""), title_limit,
                                                              more_characters)
                content_json["description"] = shorten_list_or_string(content_json.get("description", ""),
                                                                     description_limit, more_characters)
                json.dump(content_json, file, indent=2)
            count += 1

    logger.info(f"Downloaded all the tools metadata! Total JSON files: {count}")
    return files_list


def harvest_codemeta(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")
    url = params.get("url", None)
    output_path_data = params.get("output_path_data", None)
    backup_directory = params.get("backup_directory", None)
    download_json_files(url, output_path_data, backup_directory)
    logger.info(f"### Finished {name}. ###")
