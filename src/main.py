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
JSONL_c3 = "./data/c3.jsonl"


def call_harvester():
    harvester.main(threshold = 3)
    log.info("Harvester called...")
    

def call_rating():
    rating.main()
    log.info("Filtering for rating...")


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
    This function reads a JSONL files and extracts the "identifier" field from each line. 
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
    
    return all_ids
    

def call_template(jsonl_file: str):
    c3_ids = get_ids_from_jsonl(jsonl_file)
    if c3_ids:
        for current_id in c3_ids:
            log.info(f"Making a json file for INEO for {current_id}...")
            template.main(current_id)
    else:
        log.error("ERROR: No IDs found in the JSONL file.")


def call_ineo_sync():
    ineo_sync.main()
    log.info("sync with INEO ...")

if "__main__" == __name__:
    
    # Harvest codemeta and Rich User Contents files 
    call_harvester()

    # Filter codemeta.jsonl for reviewRating > 3 (+ manual demand list and ruc without codemeta)
    call_rating()
   
    tools_to_INEO = get_ids_from_jsonl(JSONL_c3)
    call_get_properties()
 
    # If the jsonl file is empty, there are no updates:
    if is_empty_jsonl_file(JSONL_c3):
        log.info(f"No new updates in the jsonl files of RUC and Codemeta")
    else:
        # The jsonl line file is not empty, make a template for INEO
        log.info(f"Jsonl file is not empty, making templates ...")
        call_template(JSONL_c3)

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
    

