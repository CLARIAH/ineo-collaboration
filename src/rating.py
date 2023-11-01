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


def main():
    # Paths to the query file and the output JSONL file.
    query_file = "./queries/rating.rq"
    c3_jsonlfile = "./data/c3_codemeta.jsonl"

    # Execute the query to get codemeta IDs with a rating >= 3.
    c3_ids = query_rumbledb(query_file, JSONL_cc)

    # Initialize a list to store matching lines
    matching_lines = []

    # Open the input JSONL file
    with open(JSONL_cc_ineo, 'r') as input_file:
        for line in input_file:
            data = json.loads(line)
            if 'identifier' in data:
                if data['identifier'] in c3_ids['values']:
                    # If the 'identifier' matches a c3_id, add it to the list of matching lines
                    matching_lines.append(data)
                elif data['identifier'] in tools_requests:
                    # If the 'identifier' matches a tools_request, add it to the list
                    matching_lines.append(data)

    # Write the matching lines to the output JSONL file
    with open('c3.jsonl', 'w') as output_file:
        for data in matching_lines:
            output_file.write(json.dumps(data) + '\n')

    print("Matching lines written to 'c3.jsonl'")


if __name__ == '__main__':
    main()