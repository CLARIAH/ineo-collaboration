import harvester
import template
import ineo_sync
import logging
import json
import os
from collections import defaultdict

# Codemeta jsonl file
codemeta_jsonl_file: str = "./data/codemeta.jsonl"

# Rich User Contents jsonl file 
ruc_jsonl_file: str = "./data/ruc.jsonl"

def call_harvester():
    harvester.main()
    logging.info("Harvester called...")

def get_tool_counts_from_jsonl(jsonl_files: list[str]) -> dict:
    tool_counts = defaultdict(int) 
    file_counts = {}  
    
    for jsonl_file in jsonl_files:
        file_counts[jsonl_file] = 0  # Initialize the count for each file to 0
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
    It converts the identifiers to lowercase because there is a discrepancy between the identifiers
    of the codemeta files (e.g. frog) and the Rich User Contents (e.g. Frog)
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
            print(f"Combining both RUC and CM of {file_name} for the INEO api...")
            template.main(current_id)
        else:
            print(f"The RUC of {file_name} does not exist in the directory.")

def is_empty_jsonl_file(file_path):
    try:
        with open(file_path, 'r') as jsonl_file:
            for line in jsonl_file:
                if line.strip():  
                    return False  
            return True  
    except FileNotFoundError:
        return True 

# TODO: call ineo_sync
def call_ineo_sync():
    ineo_sync.main()


if "__main__" == __name__:
    call_harvester()
    jsonl_files = [codemeta_jsonl_file, ruc_jsonl_file]
    if all(is_empty_jsonl_file(file) for file in jsonl_files):
        print(f"No new updates in the jsonl files of RUC and codemeta")
    else:
        call_template(jsonl_files)
        call_ineo_sync()
        logging.info("All done")
    
    
    # TODO: only the {id}_processed files that are changed, now they are all saved in the directory so it also takes the older ones. 
    # Solution: make a variable of the processed files in template.py?
    # TODO: the processed files are generated from the RUC. Without RUC no template to send to INEO. 
    

    #tool_counts = get_tool_counts_from_jsonl(jsonl_files)
    #for tool, count in tool_counts.items():
    #    print(f"Tool: {tool}, Count: {count}")