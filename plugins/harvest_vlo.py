import os
import sys
import json
import logging
import requests
import concurrent.futures
from typing import List, Dict
# local imports
from utils.utils import get_logger, remove_html_tags, shorten_list_or_string

logger = get_logger(__name__, logging.INFO)

# limits
title_limit: int | None = 65536
description_limit: int | None = None
more_characters: str = "..."
id_limit: int = 128


def _fetch_solr_records(query: str, solr_url: str, username, password, start=0, rows=10000, proxies=None) -> Dict:
    """
    Retrieve Solr records in parallel with a given query.
    """
    params = {
        "q": query,
        "wt": "json",
        "start": start,
        "rows": rows,
    }
    response = requests.get(
        f"{solr_url}/select",
        proxies=proxies,
        params=params,
        auth=(username, password))
    response.raise_for_status()  # Raise exception if the request failed
    data = response.json()
    return data["response"]


def fetch_solr_records(query: str, solr_url: str, username: str, password: str, start=0, rows=10000, proxies=None) -> \
List[Dict]:
    """
    Retrieve Solr records in parallel with a given query.
    """
    # Retrieve the total number of records
    response = _fetch_solr_records(query, solr_url, username, password, start=start, rows=0, proxies=proxies)
    total_records = response["numFound"]
    logger.debug(f"Total records in Solr: {total_records}")

    # Retrieve the records in parallel
    records = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for start in range(0, total_records, rows):
            futures.append(
                executor.submit(
                    _fetch_solr_records, query, solr_url, username, password, start=start, rows=rows, proxies=proxies
                )
            )
        for future in concurrent.futures.as_completed(futures):
            records.extend(future.result()["docs"])
    return records


def store_solr_response(base_query: str, solr_url: str, username, password, parsed_datasets_directory: str,
                        proxies: dict = None) -> None:
    """
    Store the list of records from fetch_solr_records into individual JSON files.
    """
    """
    Saves individual datasets as separate JSON files

    Args:
    parsed_datasets_directory (str): Path to the directory to save the parsed datasets.
    dataset_file_path (str): Path to the dataset JSON file.

    """
    # Create the parsed_datasets folder if it doesn't exist
    if not os.path.exists(parsed_datasets_directory):
        logger.info(f"Creating output folder: {parsed_datasets_directory}")
        os.makedirs(parsed_datasets_directory)

    # Get datasets
    logger.info(f"Getting and parsing datasets ...")
    docs: List[Dict] = fetch_solr_records(base_query, solr_url, username, password, proxies=proxies)
    logger.info(f"Total datasets retrieved: {len(docs)}")

    # Extract individual datasets from the 'docs' array
    for doc in docs:
        # remove HTML tags from the description field
        temp_list = []
        for elem in doc.get("description", []):
            temp_list.append(remove_html_tags(elem))
        doc["description"] = temp_list
        # shorten title and description
        doc["name"] = shorten_list_or_string(doc.get("name", ""), title_limit, more_characters)
        doc["description"] = shorten_list_or_string(doc.get("description", ""), description_limit, more_characters)

        # get the id of the dataset and shorten it to 128 characters if it is longer
        current_id: str | None = doc.get("id", None)
        if current_id is None:
            raise Exception(f"Dataset {doc} does not have 'id'!")
        if len(current_id) > id_limit:
            current_id = current_id[:id_limit]

        dataset_filename = os.path.join(parsed_datasets_directory, f"{current_id}.json")
        logger.debug(f"Saving dataset to {dataset_filename}")
        try:
            with open(dataset_filename, 'w') as dataset_file:
                json.dump(doc, dataset_file, indent=2)
        except Exception as ex:
            logger.error(f"Error saving dataset to {dataset_filename}: {ex}")
            logger.error(doc)
            sys.exit(1)


def harvest_vlo(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")
    base_query = params.get("base_query", "*:*")
    solr_url = params.get("solr_url", None)
    solr_username = params.get("solr_username", None)
    solr_password = params.get("solr_password", None)
    parsed_datasets_directory = params.get("output_folder", None)
    proxies = params.get("proxies", None)
    if not solr_url:
        raise ValueError("solr_url parameter is required")
    if not parsed_datasets_directory:
        raise ValueError("output_folder parameter is required")
    if not os.path.isdir(parsed_datasets_directory):
        # Create the directory if it doesn't exist
        logger.info(f"Creating output directory at {parsed_datasets_directory}")
        os.makedirs(parsed_datasets_directory, exist_ok=True)

    try:
        store_solr_response(base_query, solr_url, solr_username, solr_password, parsed_datasets_directory, proxies)
    except Exception as e:
        logger.error(f"Error during harvesting VLO: {e}")
        raise e
    logger.info(f"### Finished {name}. ###")
