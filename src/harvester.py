import concurrent.futures
import os
import re
import requests
import hashlib
import sqlite3
import jsonlines
import json
import shutil
import subprocess
import yaml
import dotenv
import logging
from typing import List, Optional, AnyStr, Union, Dict, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
from utils import get_logger, get_files, remove_html_tags, shorten_list_or_string, get_id_from_file_name

log_file_path = 'harvester.log'
logger = get_logger(log_file_path, __name__, level=logging.ERROR)

try:
    from base_query import base_query
    logger.info(f"base_query.py found! {base_query}")
except ImportError:
    base_query = "koninklijke bibliotheek"
    logger.info(f"base_query.py not found! Using default base query: {base_query}")

output_path_data = "./data"
output_path_queries = "./queries"
delete_path = "./deleted_documents"

# Solr API
dotenv.load_dotenv()
solr_url = dotenv.get_key(".env", "SOLR_URL")
username = dotenv.get_key(".env", "USERNAME")
password = dotenv.get_key(".env", "PASSWORD")

# title should be 67 characters with 3 dots, and description should be 297 characters with 3 dots
title_limit: int = 67
description_limit: int = 297
more_characters: str = "..."
# ID length limit
id_limit: int = 128


def create_folder(folder_name: str):
    """
    Create a folder if it doesn't exist.
    """
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def extract_ruc(ruc_content: AnyStr) -> dict:
    """"
    Extracts Rich User Content (RUC) data from a markdown file. 

    This function parses the input content string to extract metadata fields, descriptions, and sections,
    organizing them into a dictionary.

    Args:
        ruc_content (AnyStr): The content string containing RUC data in markdown from Github
    Returns:
        dict: A dictionary containing the extracted RUC data organized as metadata fields, descriptions,
              and sections.

    The function uses regular expressions to identify and extract different components of the RUC data, removing the markdown.
    including metadata fields enclosed between '---' lines, e.g.:
    ---
    identifier: Frog
    carousel:
        - /media/frog-logo.svg
        - /media/frog-output.png
        - /media/frog.gif
    group: Frog
    title: Frog
    ---
    descriptions with titles, e.g.:
    ---
    # Frog

    and content and headings under '##' headings, e.g.:
    ## Overview

    """
    re_fields = re.compile(r'^---(.*)---', flags=re.DOTALL)
    re_descriptions = re.compile(r'---\n+#(.*?)\n\n(.*?)\n\n##', flags=re.DOTALL)
    re_sections = re.compile(r'(?m)^(##\s+.*?)$(.*?)(?=^##\s|\Z)', flags=re.DOTALL | re.MULTILINE)
    re_name = re.compile(r'[^a-zA-Z]', flags=re.DOTALL)

    # Extract metadata fields enclosed between '---' lines.

    fields = re_fields.search(ruc_content).group(1)
    dictionary: dict = yaml.load(fields, Loader=yaml.SafeLoader)

    # Extract descriptions (e.g. ##Overview) from '##' headings
    descriptions = re.findall(re_descriptions, ruc_content)

    for description in descriptions:
        section_name = description[0].strip()
        section_content = description[1].strip()
        dictionary[section_name] = section_content

    # Extract sections (e.g., ##Mentions) from '##' sections
    sections = re.finditer(re_sections, ruc_content)

    for section in sections:
        section_name = section.group(1)
        section_name = re_name.sub("", section_name)
        section_content = section.group(2)
        dictionary[section_name] = section_content.strip()

    return dictionary


def get_db_cursor(db_file_name=os.path.join(output_path_data, "ineo.db"), table_name="tools_metadata"):
    """
    Get a cursor to the database SQLite3 file which is used to track the changes in the harvested files.
    """
    # init db and check if the table exists
    conn = init_check_db(db_file_name, table_name)
    if conn is None:
        logger.error("Error in creating the database connection!")
        exit(1)
    # create a cursor
    c = conn.cursor()
    return c, conn


def get_canonical(file_name):
    """
    Create a canonical version of the json file. 
    For ignoring fields that do not contain necessary changes for the MD5 to change.
    """
    logger.debug(f"making canon file for {file_name}")
    print(f"making canon file for {file_name}")
    canon_file = f"{file_name}.canon"
    with open(file_name, 'r') as json_file:
        data = json.load(json_file)
        if 'review' in data:
            data['review']['@id'] = '__canon_purge__'
            data['review']['datePublished'] = '__canon_purge__'
        else:
            logger.debug("no review!")
    with open(canon_file, 'w') as json_file:
        json.dump(data, json_file, indent=2)
    return canon_file


def get_md5(file_name):
    """
    Getting MD5 of each individual json file
    """
    md5_file = file_name
    if file_name.endswith('codemeta.json'):
        md5_file = get_canonical(file_name)
    hasher = hashlib.md5()
    with open(md5_file, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_json_files(
        url: str = "https://tools.clariah.nl/files/",
        save_directory: str = os.path.join(output_path_data, "tools_metadata")) -> List[str]:
    """
    Download and count all individual json files using beautifulsoup to harvest contents from the given URL. 

    """
    # first backup previous JSON files
    backup_directory = os.path.join(output_path_data, "tools_metadata_backup")
    backup_json_files(save_directory, backup_directory)

    files_list = []

    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    count = 0

    for link in links:
        href = link.get('href')
        if href.endswith('.codemeta.json'):
            file_url = url + href
            logger.debug(f"Downloading {file_url}")
            response = requests.get(file_url)
            file_name = os.path.join(save_directory, href)
            files_list.append(file_name)
            # loads binary response content as string and dump it to json file
            with open(file_name, 'w') as file:
                content = response.content.decode('utf-8')
                content_json = json.loads(content)
                # shorten name and description
                content_json["name"] = shorten_list_or_string(content_json.get("name", ""), title_limit, more_characters)
                content_json["description"] = shorten_list_or_string(content_json.get("description", ""), description_limit, more_characters)
                json.dump(content_json, file, indent=2)
            count += 1

    logger.info(f"Downloaded all the tools metadata! Total JSON files: {count}")
    return files_list


def backup_json_files(source_directory: str, backup_directory: str) -> None:
    """
    Make a backup copy of the previously downloaded JSON files.
    """
    if not os.path.exists(source_directory):
        os.makedirs(source_directory)

    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)

    for file_name in os.listdir(source_directory):
        source_file = os.path.join(source_directory, file_name)
        backup_file = os.path.join(backup_directory, file_name)
        shutil.copyfile(source_file, backup_file)

    logger.info("Backup of previous JSON files created.")


def make_jsonline(jsonfile):
    """
    Write the contents of multiple JSON files to a single JSONlines file.
    RumbleDB processes JSONL files. 
    """
    data = json.load(jsonfile)
    return data


def add_to_jsonlines(read_from_file, write_to_file):
    """
    Add a single JSON file (e.g. codemeta.json) to a JSONlines file.
    """
    with open(read_from_file, 'r') as json_file:
        data = make_jsonline(json_file)
        logger.debug(f"writing {data} to {write_to_file}")
        with jsonlines.open(write_to_file, 'a') as jsonlines_file:
            jsonlines_file.write(data)


def compare_lists(list1: Optional[List[str]], list2: Optional[List[str]]) -> List[str]:
    """
    compare 2 lists and return the difference
    """
    if list1 is None:
        list1 = []
    if list2 is None:
        list2 = []

    # list1 - list2 but with path stripped

    list1_copy = [x.split("/")[-1] for x in list1]
    list2_copy = [x.split("/")[-1] for x in list2]

    # getting elements in l1 not in l2
    diff = []
    if list1 is not None and len(list1) > 0:
        # list1_path = list1[0].split("/")[:-1]
        list1_list2 = list(set(list1_copy) - set(list2_copy))
        # diff = [f"{list1_path}/{x}" for x in list1_list2]
        diff = [x for x in list1_list2]
    logger.debug(f"list1 diff is {diff}")

    # getting elements in l2 not in l1
    diff2 = []
    if list2 is not None and len(list2) > 0:
        # list2_path = list2[0].split("/")[:-1]
        list2_list1 = list(set(list2_copy) - set(list1_copy))
        # diff2 = [f"{list2_path}/{x}" for x in list2_list1]
        diff2 = [x for x in list2_list1]
    logger.debug(f"list2 diff is {diff2}")
    return diff + diff2


def create_db_table(conn: sqlite3.Connection, table_name: str) -> None:
    """
    Create a table in the database
    """
    c = conn.cursor()
    if table_name == "rich_user_contents":
        c.execute(f"CREATE TABLE {table_name} (file_name text, md5 text, timestamp text DEFAULT CURRENT_TIMESTAMP)")
    else:
        c.execute(f"CREATE TABLE {table_name} (file_name text, md5 text, timestamp text DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()


def db_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """
    check if the table exists in the data
    """
    c = conn.cursor()
    c.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if c.fetchone()[0] == 1:
        return True
    return False


def get_id_from_ruc_file_name(file_name: str) -> str:
    full_file_name = file_name.split("/")[-1]
    id_part = full_file_name.split(".")[0]
    return id_part


def get_id_from_field(file_name: str) -> str:
    with open(file_name, 'r') as json_file:
        data = json.load(json_file)
        result: str = data.get('identifier', data.get('id', None))
        if result is None:
            raise Exception(f"Could not find identifier or id in {file_name}")
        return result


def process_list(ids: list, folder_name, db_file_name, table_name, diff_list, current_timestamp,
                 previous_batch_dict=None):
    """
    This function tracks changes in json files, get a canon file form it, and records those changes in a JSON Lines file, and maintains a record of the changes in a database.
    The function compares MD5 hashes between the current batch and the previous batch.

    diff_list: list of files to process
    current_timestamp: timestamp of the current batch
    previous_batch_dict: Optional dictionary of previous batch

    if previous batch dict is none, then it will always add the file to the jsonlines file
    if previous batch dict is not none, then it will compare the md5 of the current file with the md5 of the previous batch
    """
    c, conn = get_db_cursor(db_file_name, table_name)

    for file in diff_list:
        file = os.path.normpath(os.path.join(folder_name, file))
        logger.info(f"### Processing {file}")
        md5 = get_md5(file)
        previous_md5 = previous_batch_dict.get(file, None) if previous_batch_dict is not None else None

        if md5 != previous_md5:
            if previous_md5 is not None:
                logger.debug(f"File {file} has changed! Old hash was: {previous_md5}")
            ids.append(get_id_from_field(file))
            logger.debug(f"### Adding {ids[-1]}")
        else:
            logger.debug(f"File {file} has not changed.")
        c.execute(f"INSERT INTO {table_name} (file_name, md5, timestamp) VALUES (?, ?, ?)",
                  (file, md5, current_timestamp))
        conn.commit()


def init_check_db(db_file_name: str, table_name: str) -> Optional[sqlite3.Connection]:
    """
    check if the database exists, if not create one
    Creates tables in the database.
    """
    conn = sqlite3.connect(db_file_name)

    # check if table exists
    if not db_table_exists(conn, table_name):
        logger.info(f"Table {table_name} does not exist, creating!")
        create_db_table(conn, table_name)

    return conn


def get_previous_batch(db_file_name, table_name, previous_timestamp) -> List[str]:
    c, conn = get_db_cursor(db_file_name, table_name)
    c.execute(f"SELECT file_name FROM {table_name} WHERE timestamp = ?", (previous_timestamp,))
    previous_batch = c.fetchall()
    # process list of tuples to list of strings
    previous_batch = [x[0] for x in previous_batch]

    return previous_batch


def sync_ruc(github_url, github_dir):
    """
    Retrieves Rich User Content of Gihub repository "ineo-content".
    """
    # store the current working directory
    current_dir = os.getcwd()

    # Check if the ineo-content github repository directory exists
    if not os.path.exists(github_dir):
        logger.info(f"The github directory '{github_dir}' does not exist. Cloning...")
        # Clone the repository
        subprocess.run(["git", "clone", github_url])
    else:
        logger.info(f"The github directory '{github_dir}' already exists. Pulling...")

        # cd ineo-content
        os.chdir(github_dir)

        # Run git pull and capture the output
        result = subprocess.run(["git", "stash"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = subprocess.run(["git", "stash", "clear"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = subprocess.run(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the "Already up to date" message is in the output
        if "Already up to date." in result.stdout:
            logger.info("Repository is already up to date. The RUC have not changed")
        else:
            logger.info("Repository is not up to date.")

        # Change back to the previous working directory
        os.chdir(current_dir)


def get_ruc_contents() -> dict:
    """
    This script synchronizes with the GitHub repository of ineo-content, extracts Rich User Content (RUC)
    and returns the RUC data in a dictionary.

    The 'extract_ruc' function is used to parse the RUC data from a given content string using regex.
    It extracts metadata fields, descriptions, and sections, returning them as a dictionary.
    """
    github_url = "https://github.com/CLARIAH/ineo-content.git"
    github_dir = "./ineo-content"
    sync_ruc(github_url, github_dir)

    folder_path = "./ineo-content/src/tools"
    all_ruc_contents = {}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as file:
            contents: AnyStr = file.read()
            ruc_contents: dict = extract_ruc(contents)
            logger.debug(f"Rich User Contents of {file_path} is:\n{ruc_contents}\n")
            all_ruc_contents[filename] = ruc_contents

    # Check if the RUC filename is identical to the identifier and replace if not
    modified_contents = {}
    for filename, ruc_data in all_ruc_contents.items():
        identifier = ruc_data.get('identifier', '').lower()  # Get the lowercase identifier from the RUC dictionary
        filename_ruc = os.path.splitext(filename)[0].lower()
        if filename_ruc != identifier:
            logger.debug(f"Filename '{filename_ruc}' is not identical to the identifier '{identifier}'")
            logger.debug("Replacing the filename with the identifier...")
            modified_contents[identifier] = ruc_data
        else:
            modified_contents[filename] = ruc_data

    all_ruc_contents = modified_contents

    return all_ruc_contents


def serialize_ruc_to_json(ruc_contents_dict, output_dir="./data") -> Union[dict, list]:
    """
    Serialize the RUC dictionary into JSON files.

    Args:
        ruc_contents_dict (dict): A dictionary containing RUC data
        output_dir (str): The directory where the RUC JSON files will be saved. Defaults to "./data".
    """
    ruc_subfolder = "rich_user_contents"
    for filename, ruc_contents in ruc_contents_dict.items():
        subfolder_path = os.path.join(output_dir, ruc_subfolder)
        os.makedirs(subfolder_path, exist_ok=True)
        json_file_path = os.path.join(subfolder_path, os.path.splitext(filename)[0] + ".json")
        org_title = ruc_contents.get("title", "")
        # shorten title and description
        ruc_contents["title"] = shorten_list_or_string(org_title, title_limit, more_characters)
        org_description = ruc_contents.get(org_title, None)
        if org_description is not None:
            if org_title == ruc_contents["title"]:
                # if the title is not shortened, use it as key to retrieve the description
                ruc_contents[org_title] = shorten_list_or_string(org_description, description_limit, more_characters)
            else:
                ruc_contents[ruc_contents["title"]] = shorten_list_or_string(org_description, description_limit, more_characters)
                _ = ruc_contents.pop(org_title)

        with open(json_file_path, "w") as json_file:
            json.dump(ruc_contents, json_file)


# Initialize a dictionary to store the absence count for each file_name
absence_count = {}


def get_matching_timesamps(db_file_name, table_name, threshold):
    """
    This function determines whether each file_name is present or absent based on the timestamp in the records. 
    It Iterates through the distinct filenames and retrieves the most recent record for each file_name. It then 
    checks if the timestamp matches the current date. If it does, the file_name is considered present in the latest download.
    If the timestamp does not match the current date, it calculate the time elapsed in days since the last run of the file_name and
    updates the absence count for the file_name in the absence_count dictionary.

    Returns a list of records, where each record includes information about the file_name, whether it matches the current date, and the time elapsed (if not present).
    """

    c, conn = get_db_cursor(db_file_name, table_name)

    # Get a list of distinct filenames
    c.execute("SELECT DISTINCT file_name FROM tools_metadata")
    distinct_filenames = [row[0] for row in c.fetchall()]

    results = []
    limit = threshold + 1

    # Iterate through distinct filenames and retrieve the top 3 records for each
    for file_name in distinct_filenames:
        c.execute(f"SELECT * FROM tools_metadata WHERE file_name = ? ORDER BY timestamp DESC LIMIT {limit}",
                  (file_name,))
        records = c.fetchall()

        if records:
            current_date = datetime.now().strftime('%Y%m%d')

            # Check if the date part of the latest timestamp matches the current date
            for record in records:
                record_list = list(record)
                timestamp = record_list[2]  # the timestamp is in the third column of the table
                matches_date = current_date == timestamp[:8]  # compare %Y%m%d
                record_list.append(matches_date)

                if not matches_date:
                    # Calculate the time elapsed between the current date and the timestamp
                    timestamp_date = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
                    current_date_date = datetime.strptime(current_date, '%Y%m%d')
                    time_elapsed = current_date_date - timestamp_date
                    record_list.append(time_elapsed)

                    # Update the absence count for this file_name
                    tool_name = record_list[0]
                    absence_count[tool_name] = absence_count.get(tool_name, 0) + 1

                results.append(record_list)

    # Close the cursor and connection
    c.close()
    conn.close()

    return results


def process_records_timestamps(records):
    for record in records:
        if record[-2]:  # Check if the record matches the current date
            logger.info(f"Record {record} matches the current date")
        else:
            time_elapsed = record[-1]
            time_elapsed_in_days = time_elapsed.days
            logger.info(f"Record {record} does not match the current date. Time elapsed (days): {time_elapsed_in_days}")


def create_minimal_ruc(ruc_file, ruc_contents_dict):
    """
    Create a minimal RUC (Rich User Contents) object with default values and save it to a JSON file.
    Used when there is no corresponding codemeta file for a RUC. 
    """

    ruc_id = get_id_from_ruc_file_name(ruc_file)
    identifier_value = ruc_contents_dict[f'{ruc_id}.md']['identifier']

    ruc_template = {
        "ruc": {"identifier": identifier_value}
    }

    # Write the JSON data to the file
    with open(ruc_file, 'w') as json_file:
        json.dump(ruc_template, json_file, indent=4)


def _fetch_solr_records(query: str, solr_url: str, username, password, start=0, rows=10000) -> Dict:
    """
    Retrieve Solr records in parallel with a given query.
    """
    params = {
        "q": query,
        "wt": "json",
        "start": start,
        "rows": rows,
    }
    response = requests.get(f"{solr_url}/select", params=params, auth=(username, password))
    response.raise_for_status()  # Raise exception if the request failed
    data = response.json()
    return data["response"]


def fetch_solr_records(query: str, solr_url: str, username: str, password: str, start=0, rows=10000) -> List[Dict]:
    """
    Retrieve Solr records in parallel with a given query.
    """
    # Retrieve the total number of records
    response = _fetch_solr_records(query, solr_url, username, password, start=start, rows=0)
    total_records = response["numFound"]
    logger.info(f"Total records in Solr: {total_records}")

    # Retrieve the records in parallel
    records = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for start in range(0, total_records, rows):
            futures.append(
                executor.submit(
                    _fetch_solr_records, query, solr_url, username, password, start=start, rows=rows
                )
            )
        for future in concurrent.futures.as_completed(futures):
            records.extend(future.result()["docs"])
    return records


def store_solr_response(base_query: str, solr_url: str, username, password, parsed_datasets_directory: str):
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
        os.makedirs(parsed_datasets_directory)

    # Get datasets
    logger.info(f"Getting and parsing datasets ...")
    docs: List[Dict] = fetch_solr_records(base_query, solr_url, username, password)

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
            print(doc)
            exit()


def get_id_from_change_list(diff_list_ruc: list) -> list[str]:
    return [x.split(".")[0] for x in diff_list_ruc if x.endswith('.json')]


def reduce_id(input_path: str, id_limit: int = id_limit):
    """
    This function reduces the id length of the files in the input path and change its file name accordingly

    input_path (str): The path of the files to be checked
    id_limit (int): The limit of the id length

    return: None
    """
    logger.debug(f"{input_path=}")
    files = get_files(input_path)
    logger.debug(f"### checking length of {len(files)} files in {input_path} ###")
    counter: int = 0
    for filename in files:
        logger.debug(f"### checking {filename} ###")
        current_id: str = get_id_from_file_name(filename)
        if len(current_id) > id_limit:
            counter += 1
            print(f"\n\n### {filename} has id length {len(current_id)} > {id_limit}")
            logger.info(f"\n\n### {filename} has id length {len(current_id)} > {id_limit}")
            dir_name = os.path.dirname(filename)
            # new id is the last 128 characters of the current id
            new_current_id = current_id[-id_limit:]
            new_filename = os.path.join(dir_name, f"{new_current_id}.json")
            logger.debug(f"{new_current_id}")
            logger.debug(f"{new_filename=}")
            # get content and replace id with new id
            with open(filename, "r") as f:
                json_data = json.loads(f.read())
            json_data["id"] = new_current_id
            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
            # Change the file name
            os.rename(filename, new_filename)
    if counter > 0:
        print(f"### {counter} files have id length > {id_limit}")
        logger.info(f"### {counter} files have id length > {id_limit}")


def _harvest_datasets():
    """
    This function downloads the latest datasets from the Solr API and saves them as individual JSON files.
    """
    # Get INEO records from Solr and save them as individual JSON files
    # current_path = os.path.dirname(os.path.abspath(__file__))
    parsed_datasets_directory = './data/parsed_datasets'
    store_solr_response(base_query, solr_url, username, password, parsed_datasets_directory)
    logger.info("reducing id length according to the INEO standard")
    reduce_id(parsed_datasets_directory, id_limit)
    logger.debug(f"Datasets are saved in {parsed_datasets_directory}")


def _harvest_ruc():
    """
    This function downloads the latest Rich User Content (RUC) from the Github repository "ineo-content".
    """
    ruc_contents_dict = get_ruc_contents()
    serialize_ruc_to_json(ruc_contents_dict)


def _harvest_tools_codemeta():
    # download the codemeta files
    _ = download_json_files()


def get_changed_ids(db_file_name, db_table_name, current_timestamp, download_dir_part, diff_ids):
    (c, conn) = get_db_cursor(db_file_name=db_file_name, table_name=db_table_name)
    download_dir = os.path.join(output_path_data, download_dir_part)

    # check if previous batch exists in the "tools_metadata" table
    c.execute(f"SELECT * FROM {db_table_name} ORDER BY timestamp DESC LIMIT 1")
    has_previous_batch = c.fetchone()
    if has_previous_batch is None:
        logger.debug(f"No {db_table_name} previous batch exists in the database")
        previous_batch = None
        previous_timestamp = None
    else:
        previous_timestamp = has_previous_batch[2]
        if previous_timestamp is None:
            logger.error("Error in getting the previous batch!")
            exit(1)

        previous_batch = get_previous_batch(db_file_name, db_table_name, previous_timestamp=previous_timestamp)

    current_batch = get_files(download_dir)
    if current_batch is None:
        logger.error("No codemeta files found in the current batch!")
        exit(1)

    # compare the 2 lists and get the difference
    diff_list = compare_lists(current_batch, previous_batch)

    if has_previous_batch is not None:
        # get previous batch from db
        c.execute(f"SELECT file_name, md5 FROM {db_table_name} WHERE timestamp = ?", (previous_timestamp,))
        previous_batch = c.fetchall()

        # previous_batch_dict contains key value pair in the form of {file_name: md5}
        previous_batch_dict = {x[0]: x[1] for x in previous_batch}

        batch = [x.split("/")[-1] for x in current_batch]

        # loop through current batch and compare with previous batch using hash values
        process_list(diff_ids, download_dir, db_file_name, db_table_name, batch, current_timestamp, previous_batch_dict)
    else:
        process_list(diff_ids, download_dir, db_file_name, db_table_name, diff_list, current_timestamp, None)

    conn.commit()
    conn.close()


def harvest(threshold: int = 3, debug: bool = False) -> Tuple:
    """
    This script downloads the latest Codemeta JSON files and Rich User Content (RUC) from Github,
    threshold: int : The number of iterations after which a file is considered absent.
    TODO: The threshold is implemented, but need test
    """
    if debug:
        if os.path.exists("tools.json") and os.path.exists("datasets.json"):
            logger.info("tools.json and datasets.json exist! Reading the ids from the files.")
            with open("tools.json", "r") as f:
                codemeta_ids = json.load(f)
            with open("datasets.json", "r") as f:
                datasets_ids = json.load(f)
            return codemeta_ids, datasets_ids

    logger.info("tools.json and datasets.json do not exist! Fetching the ids from harvest.")

    """
    Prepare the database and the tables before actual harvesting
    """
    # Create the "data" folder if it doesn't exist
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    # make sure the db exists for storing versioning info
    db_file_name = os.path.join(output_path_data, "ineo.db")
    # get the current timestamp to be used in the database and make sure all the files in the same batch have the same timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    """
    Harvesting
    """
    # harvest datasets
    logger.info("Harvesting datasets ...")
    _harvest_datasets()
    # harvest tools_codemeta
    logger.info("Harvesting tools codemeta ...")
    _harvest_tools_codemeta()
    # harvest ruc
    logger.info("Harvesting rich user content ...")
    _harvest_ruc()

    """
    Getting the changed ids after harvesting
    """
    codemeta_ids: list = []
    datasets_ids: list = []

    get_changed_ids(db_file_name, "tools_metadata", current_timestamp, "tools_metadata", codemeta_ids)
    get_changed_ids(db_file_name, "rich_user_contents", current_timestamp, "rich_user_contents", codemeta_ids)
    get_changed_ids(db_file_name, "datasets", current_timestamp, "parsed_datasets", datasets_ids)

    """
    Make sure the ids are unique and save them to the files for debugging
    """
    codemeta_ids = list(set(codemeta_ids))
    datasets_ids = list(set(datasets_ids))
    if debug:
        with open("tools.json", "w") as f:
            json.dump(codemeta_ids, f)
        with open("datasets.json", "w") as f:
            json.dump(datasets_ids, f)
    return codemeta_ids, datasets_ids

    # TODO <<<DELETION SCENERIO >>>
    # Search for inactive tools to delete in INEO (inactive after a tool is absent for three runs in the database)
    codemeta_records = get_matching_timesamps(db_file_name, table_name_tools, threshold)
    # Iterate through the absent records and compare the timestamps in the db with the current date 
    process_records_timestamps(codemeta_records)

    ids_to_delete = []
    for file_name, count in absence_count.items():
        if count > threshold:
            # Extract the ID from the file_name
            tool_id = get_id_from_file_name(file_name)
            if tool_id:
                ids_to_delete.append(tool_id)

    if ids_to_delete:
        logger.debug(f"IDs of the tools to be deleted: {', '.join(ids_to_delete)}")

        # Write the IDs to a JSON file in the "delete_tools" folder
        deleted_documents_folder = delete_path
        if not os.path.exists(deleted_documents_folder):
            os.makedirs(deleted_documents_folder)

        file_path = os.path.join(delete_path, 'deleted_tool_ids.json')
        with open(file_path, 'w') as json_file:
            json.dump(ids_to_delete, json_file)
            logger.debug(f"JSON containing tools to be deleted saved to {file_path}")


if __name__ == '__main__':
    harvest(threshold=3, debug=True)
