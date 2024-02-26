import requests
import json
import logging
import os
from harvester import get_logger

log_file_path = 'rating.log'
log = get_logger(log_file_path, __name__)

RUMBLEDB = "http://rumbledb:8001/jsoniq"
JSONL_cc = "/data/codemeta.jsonl"
JSONL_cc_ineo = "./data/codemeta.jsonl"


def get_ruc_ids(jsonl_file: str) -> list:
    ruc_identifiers_without_cm = []
    desired_key = "ruc"
    # Read the JSONL file line by line
    with open(jsonl_file, "r") as file:
        for line in file:
            data = json.loads(line)
            if desired_key in data:
                ruc_identifiers_without_cm.append(data[desired_key]["identifier"])
    return ruc_identifiers_without_cm


def query_rumbledb(query_file: str, jsonl_file: str) -> dict:
    """
    This function queries against RumbleDB and retrieves codemeta IDs with a rating greater than or equal to the threshold.
    query_file (str): Path to the external query file in the queries folder
    jsonl_file (str): Path to the codemeta JSONL file used in the query (codemeta.jsonl)
    threshold (str): Rating threshold (default is '3').

    Returns a dictionary containing codemeta IDs with a rating greater than 3
    """
    with open(query_file, "r") as file:
        rating_query = file.read()
        if rating_query is not None:
            rating_query = rating_query.replace("{JSONL}", jsonl_file)
            
    response = requests.post(RUMBLEDB, data=rating_query)
    assert (response.status_code == 200), f"Error running {rating_query} on rumbledb: {response.text}"

    return json.loads(response.text)


def save_codemeta_to_file(codemeta_lines, output_file):
    with open(output_file, "w") as output_file:
        for line in codemeta_lines:
            output_file.write(json.dumps(line) + '\n')


def process_jsonlfile(input_file_path, c3_ids, tools_requests):
    c3_lines = []
    ruc_lines = []

    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            codemeta = json.loads(line)
            if 'identifier' in codemeta:
                if codemeta['identifier'] in c3_ids['values']:
                    c3_lines.append(codemeta)
                elif codemeta['identifier'] in tools_requests:
                    c3_lines.append(codemeta)
            if 'ruc' in codemeta:
                ruc_lines.append(codemeta)

    return c3_lines, ruc_lines


def main():

    # Example list of codemeta tools that do not have a sufficient rating but are requested by the provider.
    # For now (15112023) this is a list of codemeta tools that are already uploaded to INEO and do not have a rating >= 3.
    # TODO: move this list to a separate file and find a way to let providers decide the content of this list.
    tools_requests = []
    
    # Here follows code for tools that have a RUC but do not have a sufficient rating
    # Path to the query file for a reviewRating >= 3 and the output JSONL file.
    query_file_rating = "./queries/rating.rq"
    # Path to the query file for a reviewRating < 3
    query_file_no_rating = "./queries/norating.rq"
    c3_jsonlfile = "./data/c3.jsonl"

    # Execute the query to get codemeta IDs with a reviewRating >= 3.
    c3_ids = query_rumbledb(query_file_rating, JSONL_cc)
    log.info(f"Tools with a reviewRating >= 3: {c3_ids}")
    
    # Execute the query to get codemeta IDs with a reviewRating < 3.
    no_c3 = query_rumbledb(query_file_no_rating, JSONL_cc)
    log.info(f"Tools with a reviewRating < 3: {no_c3}")

    identifiers = no_c3.get('values', [])
    RUC_tools_no_rating = []
    rich_user_contents_folder = "./data/rich_user_contents"
    for identifier in identifiers:
        filename = f"{identifier}.json"
        filepath = os.path.join(rich_user_contents_folder, filename)

        if os.path.exists(filepath):
            log.info(f"Tool {identifier} exists in the rich_user_contents folder. Add to jsonl file to be processed for INEO!")
            RUC_tools_no_rating.append(identifier)
    
    tools_requests.extend(RUC_tools_no_rating)
    log.info(f"tools that need to be manually added to INEO: {tools_requests}")
    
    # Initialize a list to store matching lines 
    c3_lines = []
    ruc_lines = []

    c3_lines, ruc_lines = process_jsonlfile(JSONL_cc_ineo, c3_ids, tools_requests)
    
    identifiers = [item['ruc']['identifier'] for item in ruc_lines]
    log.info(f"Tools that do not have a corresponding codemeta file: {identifiers}")


    # Combine both c3_lines and ruc_lines
    combined_lines = c3_lines + ruc_lines

    with open(c3_jsonlfile, 'w') as output_file:
        for line in combined_lines:
            output_file.write(json.dumps(line) + '\n')

    log.info("Matching and 'ruc' lines written to 'c3.jsonl'")


if __name__ == '__main__':
    main()
