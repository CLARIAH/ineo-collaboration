import harvester
import template
import ineo_sync
import logging
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime

def call_harvester():
    harvester.main()
    logging.info("Harvester called...")
    
def get_tool_counts_from_jsonl(jsonl_files: list[str]) -> dict:
    tool_counts = defaultdict(int) 
    file_counts = {}  
    
    for jsonl_file in jsonl_files:
        file_counts[jsonl_file] = 0 
        with open(jsonl_file, "r") as f:
            for line in f:
                json_line = json.loads(line)
                if "identifier" in json_line:
                    identifier = json_line["identifier"]
                    lowercase_identifier = identifier.lower()
                    tool_counts[lowercase_identifier] += 1 
                    file_counts[jsonl_file] += 1 
    
    for jsonl_file, count in file_counts.items():
        print(f"Number of unique tools in {jsonl_file}: {count}")
    
    return tool_counts


def get_ids_from_jsonl(jsonl_files: list[str]) -> list[str]:
    """
    This function reads multiple JSONL files and extracts the "identifier" field from each line. 
    It onverts the identifiers to lowercase because there is a discrepancy between the identifiers
    of the codemeta files (e.g. frog) and the Rich User Contents (e.g. Frog). 
    The identifiers are then merged and duplicates are removed using a set. 
    """
    all_ids = set()  # Use a set to automatically remove duplicates
    for jsonl_file in jsonl_files:
        with open(jsonl_file, "r") as f:
            for line in f:
                json_line = json.loads(line)
                if "identifier" in json_line:
                    identifier = json_line["identifier"]
                    lowercase_identifier = identifier.lower()
                    all_ids.add(lowercase_identifier)  
    
    all_ids_list = list(all_ids)  
    return all_ids_list
    

def call_template(jsonl_files: list[str]):
    for current_id in get_ids_from_jsonl(jsonl_files):
        path = "./data/rich_user_contents" 
        file_name = f"{current_id}.json"
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            print(f"Combining both RUC and CM of {file_name}...")
            template.main(current_id)
        else:
            print(f"The RUC of {file_name} does not exist in the directory.")

def is_empty_jsonl_file(file_path):
    """
    This function checks if the jsonl files are empty. If they are then it
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

def call_ineo_sync():
    ineo_sync.main()

if "__main__" == __name__:
    # Define the maximum number of runs to keep backups of the files fed to INEO
    max_backup_runs = 3  
    
    # Create the main backup folder if it doesn't exist
    main_backup_folder = "./backup_processed_jsonfiles"
    if not os.path.exists(main_backup_folder):
        os.makedirs(main_backup_folder)
    
    # Create a list to store backup timestamps
    backup_timestamps = []
    
    # harvest codemeta and Rich User Contents files 
    call_harvester()
    
    # Codemeta jsonl file
    codemeta_jsonl_file: str = "./data/codemeta.jsonl"
    # Rich User Contents jsonl file 
    ruc_jsonl_file: str = "./data/ruc.jsonl"
    jsonl_files = [codemeta_jsonl_file, ruc_jsonl_file]
    
    tool_counts = get_tool_counts_from_jsonl(jsonl_files)
    for tool, count in tool_counts.items():
        print(f"Tool: {tool}, Count: {count}")

    # If both jsonl files are empty, there are no updates
    if all(is_empty_jsonl_file(file) for file in jsonl_files):
        print(f"No new updates in the jsonl files of RUC and Codemeta")
    
    else:
        # the jsonl line files are not empty, merge them into a template for INEO
        call_template(jsonl_files)
        
        call_ineo_sync()

        # Generate a timestamp for the backup folder name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_folder = os.path.join(main_backup_folder, f"backup_{timestamp}")
        
        # Backup the processed_jsonfiles folder
        shutil.copytree("processed_jsonfiles", backup_folder)
        
        # Clear the processed_jsonfiles folder
        shutil.rmtree("processed_jsonfiles")
        
        # Add the current timestamp to the list
        backup_timestamps.append(timestamp)
        
        # Check if there are more than max_backup_runs backups
        if len(backup_timestamps) > max_backup_runs:
            # Sort the list and remove the oldest backup
            backup_timestamps.sort()
            oldest_backup = backup_timestamps.pop(0)
            oldest_backup_path = os.path.join(main_backup_folder, f"backup_{oldest_backup}")

            shutil.rmtree(oldest_backup_path)
        
        logging.info("All done")
    

