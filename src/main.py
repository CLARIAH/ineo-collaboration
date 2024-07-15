import os.path
from datetime import datetime
from typing import Tuple

import concurrent.futures
import requests
import rating
import ineo_sync
import ineo_get_properties
import json
import logging
import harvester
from tqdm import tqdm
from template import main as templating
from utils import get_logger, call_basex, call_basex_with_file, call_basex_with_query

log_file_path = 'main.log'
logger = get_logger(log_file_path, __name__, level=logging.INFO)

# location of the JSONL file within container ineo-sync
JSONL_c3 = "./data/c3.jsonl"
JSONL_datasets = "./data/datasets.jsonl"

# location of the (same) JSONL file within container rumbledb
JSONL_tools_rdb = "/data/c3.jsonl"
JSONL_datasets_rdb = "/data/datasets.jsonl"

# location of the templates for both tools and datasets
TOOLS_TEMPLATE = "./template_tools.json"
DATASETS_TEMPLATE = "./template_datasets.json"


def call_harvester(threshold: int = 3, debug: bool = False) -> Tuple:
    logger.info("Harvesting ...")
    return harvester.harvest(threshold=threshold, debug=debug)


def call_rating():
    logger.info("Filtering for rating ...")
    rating.main()


def call_get_properties():
    logger.info("Getting properties from the INEO API")
    ineo_get_properties.main()


def is_empty(file_path: str) -> bool:
    """
    This function checks if a jsonl file is empty. If it is then it
    means that there are no updates to be fed into INEO.

    file_path (str): The full path to the jsonl file to be checked
    returns (bool): True if the file is empty, False otherwise
    """
    try:
        with open(file_path, 'r') as jsonl_file:
            for line in jsonl_file:
                if line.strip():
                    return False
            return True
    except FileNotFoundError:
        return True


def get_ids_from_jsonl(jsonl_file: str) -> list[str]:
    """
    This function reads a JSONL files and extracts the "identifier" or "id" field from each line. 
    Returns a list of Ids from the JSONL file 
    """
    all_ids = []
    with open(jsonl_file, "r") as f:
        for line in f:
            json_line = json.loads(line)
            if "identifier" in json_line:
                identifier = json_line["identifier"]
                all_ids.append(identifier)

            if "ruc" in json_line and "identifier" in json_line["ruc"]:
                ruc_identifier = json_line["ruc"]["identifier"]
                all_ids.append(ruc_identifier)

            if "id" in json_line:
                datasets_identifier = json_line["id"]
                all_ids.append(datasets_identifier)

    return all_ids


def call_template_subprocess(ids: list, template_type: str = 'tools'):
    for current_id in tqdm(ids):
        template_path = TOOLS_TEMPLATE if template_type == 'tools' else DATASETS_TEMPLATE
        logger.debug(f"Making a json file for INEO for {current_id} with template [{template_path}]...")

        try:
            if os.path.isfile(f"processed_jsonfiles_datasets/{current_id}_processed.json"):
                continue
            else:
                templating(current_id, template_path, template_type)
        except Exception:
            logger.error(f"Cannot template the file: [{current_id}] with template: [{template_path}]")
            raise


def split_list(input_list, num_sublists):
    sublist_length = len(input_list) // num_sublists
    return [input_list[i:i + sublist_length] for i in range(0, len(input_list), sublist_length)]


def call_template(ids: list, template_type: str = 'tools', workers: int = 12):
    if len(ids) <= 0:
        logger.info(f"No IDs found for {template_type}. ids list contains {len(ids)} ids.")
        return

    logger.debug(f"Templating for {len(ids)} {template_type} ...")
    logger.debug(f"first 5 ids: {ids[:5]} ...")
    call_template_subprocess(ids, template_type)


def call_ineo_sync(record_type: str, limit: int = 0, remove_before_create: bool = False):
    logger.info("Calling sync with INEO ...")
    ineo_sync.main(record_type, limit, remove_before_create)


def prepare_basex_tables(table_name: str,
                         folder: str,
                         host: str = "basex",
                         port: int = 8080,
                         user: str = "admin",
                         password: str = "pass",
                         action: str = "post") -> None:
    """
    This function prepares the basex tables for the tools and datasets

    table_name (str): The name of the table to be created
    folder (str): The folder containing the json files to be inserted into the basex table

    return (None)
    """
    logger.info(f"Preparing basex table {table_name} with folder {folder} ...")
    content_type: str = "application/xml"

    content = """
    <query>
        <text><![CDATA[
    import module namespace db = "http://basex.org/modules/db";

    db:create(
      "{table_name}",
      "{folder}",
      (),
      map {{
        "createfilter": "*.json",
        "parser": "json",
        "jsonparser": "format=basic,liberal=yes,encoding=UTF-8"
      }}
    )
    ]]></text>
    </query>
    """.format(table_name=table_name, folder=folder)

    # Create the basex table
    response = call_basex(content, host, port, user, password, action, content_type=content_type)
    if 199 < response.status_code < 300:
        logger.info(f"Basex table {table_name} created with folder {folder} ...")
    else:
        logger.error(f"Failed to create the basex table {table_name} with folder {folder} ...")
        logger.error(f"Response: {response.text}")
        raise Exception(f"Failed to create the basex table {table_name} with folder {folder} ...")


def _init_basex():
    """
    # NOTE: The folder should be the path on basex container, which is mounted in docker compose file
    """
    # prepare basex tables
    # for tools
    tools_table_name: str = "tools"
    tools_folder: str = "/data/tools_metadata"
    prepare_basex_tables(tools_table_name, tools_folder)
    # for datasets
    datasets_table_name: str = "datasets"
    datasets_folder: str = "/data/parsed_datasets"
    prepare_basex_tables(datasets_table_name, datasets_folder)


def main():
    """
    The main function of the program. 
    Harvest codemeta tools, Rich User Contents files and datasets
    
    Used folders: 
    - Find downloaded json files in ./data ### TODO: is this still accurate?
    - For code_meta, ./data/tools_metadata
    - For code_meta RUC, ./data/rich_user_contents
    - For datasets, ./data/parsed_datasets (The data source is solr API, 
        now simulated using ./data/datasets/vlo-response.json) 
    - codemeta.jsonl and datasets.jsonl will be generated in ./data
    - deleted files will be moved to ./src/deleted_documents (which is a text file contains ids to be deleted)
    """
    tools_to_INEO, datasets_to_INEO = call_harvester(threshold=3, debug=False)
    logger.info(f"Harvested {len(tools_to_INEO)} tools and {len(datasets_to_INEO)} datasets ...")

    # init basex first
    _init_basex()

    """
    Get INEO properties, e.g. research activities and domains from the INEO API
    If folder exsits and 2 or more json files present, the download of new properties is skipped
    """
    call_get_properties()

    # If the id lists are empty, there are no updates to be fed into INEO:
    if len(tools_to_INEO) == 0 and len(datasets_to_INEO) == 0:
        logger.info("No new updates in the JSONL files of RUC, Codemeta, and Datasets")
    else:
        if len(tools_to_INEO) > 0:
            logger.info(f"Making template(s) for {len(tools_to_INEO)} tools ...")
            call_template(tools_to_INEO, 'tools')
        if len(datasets_to_INEO) > 0:
            logger.info(f"Making template(s) for {len(datasets_to_INEO)} datasets ...")
            call_template(datasets_to_INEO, 'datasets')

        logger.info("Done preparation. Going to sync with INEO ...")

        # Templates are ready, sync with the INEO api.
        # Also, researchdomains and researchactivities are further processed here.
        logger.info("Syncing with INEO ...")
        logger.info("Syncing datasets ...")
        call_ineo_sync("datasets", 0, True)

        logger.info("Syncing tools ...")
        call_ineo_sync("tools", 0, False)

        logger.info("Syncing Huuygens ...")
        call_ineo_sync("huygens", 0, False)
        logger.info("DONE!")
        exit("All done!")

        # TODO: The code below does house keeping after the sync with INEO is completed.
        logger.info("sync completed. Begin backing-up and clearing of folders for the next run ...")
        # Define the maximum number of runs to keep backups of the c3 JSONL file
        max_backup_runs = 3

        # Create the main backup folder if it doesn't exist
        main_backup_folder = "./backups"
        os.makedirs(main_backup_folder, exist_ok=True)

        # Create a list to store backup timestamps
        backup_timestamps = []

        # Generate a timestamp for the backup folder name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_folder = os.path.join(main_backup_folder, f"backup_{timestamp}")

        # Backup the processed_jsonfiles folder
        shutil.copytree("processed_jsonfiles_tools", os.path.join(backup_folder, "processed_json_templates"))

        # Backup the rich_user_contents folder
        shutil.copytree("./data/rich_user_contents", os.path.join(backup_folder, "rich_user_contents_json"))

        # Create a folder for jsonl_files
        jsonl_files_folder = os.path.join(backup_folder, "jsonl_files")
        os.makedirs(jsonl_files_folder, exist_ok=True)

        # Backup individual files within jsonl_files folder
        shutil.copy("./data/c3.jsonl", os.path.join(jsonl_files_folder, "c3.jsonl"))
        shutil.copy("./data/codemeta.jsonl", os.path.join(jsonl_files_folder, "codemeta.jsonl"))

        # Copy the tools_metadata_backup folder to the backup folder
        shutil.copytree("./data/tools_metadata_backup", os.path.join(backup_folder, "tools_metadata_backup"))

        # Check if the deleted_documents folder exists and back it up if present. Then delete it. 
        deleted_documents_path = "./deleted_documents"
        if os.path.exists(deleted_documents_path) and os.path.isdir(deleted_documents_path):
            shutil.copytree(deleted_documents_path, os.path.join(backup_folder, "deleted_documents_backup"))

        logger.info("backups created, clearing folders for the next run...")

        # Clear the processed_jsonfiles folder
        shutil.rmtree("processed_jsonfiles")
        shutil.rmtree(deleted_documents_path)

        for item in os.listdir("./data"):
            # the database cannot be deleted because it needs to get track of the inactive tools and md5 comparison.
            # Implement way to delete old entries (e.g. > 3 runs) in the databases.
            if item != "ineo.db":
                item_path = os.path.join("./data", item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        # Add the current timestamp to the list
        backup_timestamps.append(timestamp)

        # Check if there are more than max_backup_runs backups
        if len(backup_timestamps) > max_backup_runs:
            # Sort the list and remove the oldest backup
            backup_timestamps.sort()
            oldest_backup = backup_timestamps.pop(0)
            oldest_backup_path = os.path.join(main_backup_folder, f"backup_{oldest_backup}")

            shutil.rmtree(oldest_backup_path)

        logger.info("All done!")


if __name__ == "__main__":
    main()
