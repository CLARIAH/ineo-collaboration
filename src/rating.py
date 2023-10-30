import requests
import json
import logging
from harvester import configure_logger


RUMBLEDB = "http://rumbledb:8001/jsoniq"
JSONL_cc = "/data/codemeta.jsonl"
JSONL_cc_ineo = "./data/codemeta.jsonl"
log_file_path = 'rating.log'
log = configure_logger(log_file_path)

# list of codemeta tools that do not have a sufficient rating but are requested by the provider. Added manually.
tools_requests = ['mediasuite', 'lenticularlens']
log.info(f"tools that need to be manually added to INEO: {tools_requests}")

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


def filter_codemeta(jsonl_file: str, c3_ids: dict, tools_requests: list) -> tuple:
    """
    Filters codemeta JSONL data based on codemeta IDs and manually requested tools.
    jsonl_file (str): Path to the JSONL file containing codemeta data (codemeta.jsonl)
    c3_ids (dict): Dictionary of codemeta IDs with a reviewRating > 3.
    tools_requests (list): List of manually requested tools that need to go to INEO despite an insufficient rating

    Returns a tuple containing two lists:
    1. filtered codemeta lines with a rating >= 3.
    2. codemeta tools that have an insufficient rating < 3
    """
    c3_jsonl_lines = []
    no_c3_identifiers = [] 
    with open(jsonl_file, "r") as codemeta_jsonl:
        for line in codemeta_jsonl:
            codemeta_tool = json.loads(line)
            codemeta_identifier = codemeta_tool.get('identifier')
            if codemeta_identifier in c3_ids['values']:
                c3_jsonl_lines.append(codemeta_tool)
            elif codemeta_identifier in tools_requests:
                c3_jsonl_lines.append(codemeta_tool)
            else:
                no_c3_identifiers.append(codemeta_tool['identifier'])
    return c3_jsonl_lines, no_c3_identifiers


def save_codemeta_to_file(codemeta_lines, output_file):
    with open(output_file, "w") as output_file:
        for line in codemeta_lines:
            output_file.write(json.dumps(line) + '\n')


def main():
    # Paths to the query file and the output JSONL file.
    query_file = "./queries/rating.rq"
    c3_jsonlfile = "./data/c3_codemeta.jsonl"

    # Execute the query to get codemeta IDs with a rating > 3.
    c3_ids = query_rumbledb(query_file, JSONL_cc)

    # Filter codemeta data and get identifiers of tools with a rating < 3.
    c3_jsonl_lines, no_c3_identifiers = filter_codemeta(JSONL_cc_ineo, c3_ids, tools_requests)

    # Save the filtered codemeta data to a JSONL file.
    save_codemeta_to_file(c3_jsonl_lines, c3_jsonlfile)
    
    log.info(f"Tools with a rating < 3: {no_c3_identifiers}")
    log.info(f"All codemeta JSONL files with a 3-stars rating have been saved to: {c3_jsonlfile}")


if __name__ == '__main__':
    main()