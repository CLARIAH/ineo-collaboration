import harvester
import rating
import template
import ineo_sync
import logging
import ineo_get_properties
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from harvester import configure_logger

log_file_path = 'main.log'
log = configure_logger(log_file_path)

# location of the JSONL file within container ineo-sync
JSONL_c3 = "./data/c3.jsonl"
JSONL_datasets = "./data/datasets.jsonl"

# location of the (same) JSONL file within container rumbledb
JSONL_tools_rdb = "/data/c3.jsonl"
JSONL_datasets_rdb = "/data/datasets.jsonl"

# location of the templates for both tools and datasets
TOOLS_TEMPLATE = "./template_tools.json"
DATASETS_TEMPLATE = "./template_datasets.json"

def call_harvester():
    harvester.main(threshold = 3)
    log.info("Harvester called ...")
    

def call_rating():
    rating.main()
    log.info("Filtering for rating ...")


def call_get_properties():
    ineo_get_properties.main()
    log.info("Getting properties from the INEO API")

def is_empty_jsonl_file(file_path):
    """
    This function checks if a jsonl file is empty. If it is then it
    means that there are no updates to be fed into INEO. 
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
    

def call_template(jsonl_file: str, template_type: str = 'tools'):
    jsonl_ids = get_ids_from_jsonl(jsonl_file)

    if not jsonl_ids:
        log.error("ERROR: No IDs found in the JSONL file.")
        return

    for current_id in jsonl_ids:
        log.info(f"Making a json file for INEO for {current_id} ...")
        
        template_path = TOOLS_TEMPLATE if template_type == 'tools' else DATASETS_TEMPLATE
        rumbledb_jsonl_path = JSONL_tools_rdb if template_type == 'tools' else JSONL_datasets_rdb
        
        if template:
            template.main(current_id, template_path, rumbledb_jsonl_path)
        else:
            log.error("ERRORL no template provided to process.")


def call_ineo_sync():
    ineo_sync.main()
    log.info("sync with INEO ...")

if "__main__" == __name__:
    
    # Harvest codemeta tools, Rich User Contents files and datasets 
    #call_harvester()

    # Filter codemeta.jsonl for reviewRating > 3 (+ manual demand list and ruc without codemeta)
    #call_rating()


    tools_to_INEO = get_ids_from_jsonl(JSONL_c3)
    datasets_to_INEO = get_ids_from_jsonl(JSONL_datasets)
    
    # Check the IDs of the datasets
    num_ids = len(datasets_to_INEO)
    has_duplicates = len(datasets_to_INEO) != len(set(datasets_to_INEO))
    if has_duplicates:
        log.debug(f"There are {num_ids} datasets IDs in total, and there are duplicates.")
    else:
        log.debug(f"There are {num_ids} datasets IDs in total, and there are no duplicates.")

    # get INEO properties, e.g. research activities and domains from the api
    #call_get_properties()
    
    # If the jsonl file is empty, there are no updates to be fed into INEO:
    if is_empty_jsonl_file(JSONL_c3) and is_empty_jsonl_file(JSONL_datasets):
        log.info("No new updates in the JSONL files of RUC, Codemeta, and Datasets")
    else:
        log.info("At least one JSONL file is not empty, generating templates ...")
        if not is_empty_jsonl_file(JSONL_c3):
            log.info("Making template(s) for tools ...")
            call_template(JSONL_c3, 'tools')
        if not is_empty_jsonl_file(JSONL_datasets):
            log.info("Making template(s) for datasets ...")
            call_template(JSONL_datasets, 'datasets')
        
        exit()
        
        # Templates are ready, sync with the INEO api
        call_ineo_sync()

        log.info("sync completed. Begin backing-up and clearing of folders for the next run ...")
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
        shutil.copytree("processed_jsonfiles", os.path.join(backup_folder, "processed_json_templates"))

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
            
        log.info("backups created, clearing folders for the next run...")
        
        # Clear the processed_jsonfiles folder
        shutil.rmtree("processed_jsonfiles")
        shutil.rmtree(deleted_documents_path)

        for item in os.listdir("./data"):
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
        
        log.info("All done!")
    

