import os
import re
import logging
import requests
import hashlib
import sqlite3
import jsonlines
import json
import shutil
import subprocess
import yaml
from typing import List, Optional, AnyStr, Union
from bs4 import BeautifulSoup
from datetime import datetime

output_path_data = "./data"
output_path_queries = "./queries"


def extract_ruc(ruc_content: AnyStr) -> dict:
    """"
    Extracts Rich User Content (RUC) data from a given content string.

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
    Get a cursor to the database
    """
    # init db and check if the table exists
    conn = init_check_db(db_file_name, table_name)
    if conn is None:
        print("Error in creating the database connection!")
        exit(1)
    # create a cursor
    c = conn.cursor()
    return (c, conn)


def get_canonical(file_name):
    
    """
    Create a canonical version of the json file
    """
    print(f"making canon file for {file_name}")
    canon_file = f"{file_name}.canon"
    with open(file_name, 'r') as json_file:
        data = json.load(json_file)
        if 'review' in data:
            data['review']['@id'] = '__canon_purge__'
            data['review']['datePublished'] = '__canon_purge__'
        else:
            print("no review!")
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
    hash_md5 = hashlib.md5()
    with open(md5_file, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_json_files(
        url: str = "https://tools.clariah.nl/files/",
        save_directory: str = os.path.join(output_path_data, "tools_metadata")) -> List[str]:
    """
    Download and count all individual json files

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
            print(f"Downloading {file_url}")
            response = requests.get(file_url)
            file_name = os.path.join(save_directory, href)
            files_list.append(file_name)
            with open(file_name, 'wb') as file:
                file.write(response.content)
            count += 1

    print(f"Downloaded all the tools metadata! Total JSON files: {count}")
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

    print("Backup of previous JSON files created.")

def get_files(folder_name: str) -> Optional[List[str]]:
    """
    get all the files in the folder
    """
    if not os.path.exists(folder_name):
        return None
    files_list = os.listdir(folder_name)
    results: List[str] = []
    for f in files_list:
        if f.endswith('.json'):
            results.append(f"{folder_name}/{f}")
    return results

def make_jsonline(jsonfile):
    """
    Write the contents of multiple JSON files to a single JSONlines file.
    """
    data = json.load(jsonfile)
    return data


def add_to_jsonlines(file, file_handle):
    """
    Add a single JSON file to a JSONlines file.
    file: path to JSON file
    file_handle: handle to JSONlines file
    returns: None
    """
    with open(file, 'r') as json_file:
        data = make_jsonline(json_file)
        file_handle.write(data)


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
    #print(list2)
    list2_copy = [x.split("/")[-1] for x in list2]
    
    # getting elements in l1 not in l2
    diff = []
    if list1 is not None and len(list1) > 0:
        # list1_path = list1[0].split("/")[:-1]
        list1_list2 = list(set(list1_copy) - set(list2_copy))
        # diff = [f"{list1_path}/{x}" for x in list1_list2]
        diff = [x for x in list1_list2]
    print(f"list1 diff is {diff}")

    # getting elements in l2 not in l1
    diff2 = []
    if list2 is not None and len(list2) > 0:
        # list2_path = list2[0].split("/")[:-1]
        list2_list1 = list(set(list2_copy) - set(list1_copy))
        # diff2 = [f"{list2_path}/{x}" for x in list2_list1]
        diff2 = [x for x in list2_list1]
    print(f"list2 diff is {diff2}")
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

def process_list(folder_name, db_file_name, table_name, diff_list, jsonlines_file, current_timestamp, previous_batch_dict=None):
    """
    process the list of files and add to jsonlines file
    diff_list: list of files to process
    jsonlines_file: jsonlines file to write to
    current_timestamp: timestamp of the current batch
    previous_batch_dict: Optional dictionary of previous batch

    This function takes a list of files, get a canon file from it, get the md5 of the canon file, and compare it with the previous batch md5
    if previous batch dict is none, then it will always add the file to the jsonlines file
    if previous batch dict is not none, then it will compare the md5 of the current file with the md5 of the previous batch
    """
    c, conn = get_db_cursor(db_file_name, table_name)
    folder_name = folder_name
    toolmeta_dir = os.path.join(output_path_data, folder_name)
    for file in diff_list:
        file = os.path.normpath(os.path.join(toolmeta_dir, file))
        md5 = get_md5(file)
        previous_md5 = previous_batch_dict.get(file, None) if previous_batch_dict is not None else None

        if md5 != previous_md5:
            if previous_md5 is not None:
                print(f"File {file} has changed! Old hash was: {previous_md5}")
            add_to_jsonlines(file, jsonlines_file)
        else:
            print(f"File {file} has not changed.")
        c.execute(f"INSERT INTO {table_name} (file_name, md5, timestamp) VALUES (?, ?, ?)", (file, md5, current_timestamp))
        conn.commit()

def init_check_db(db_file_name: str, table_name: str) -> Optional[sqlite3.Connection]:
    """
    check if the database exists, if not create one
    Creates tables in the database. 
    """
    conn = sqlite3.connect(db_file_name)
    
    # check if table exists
    if not db_table_exists(conn, table_name):
        print(f"Table {table_name} does not exist, creating!")
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
    #store the current working directory
    current_dir = os.getcwd()
    
    # Check if the ineo-content github repository directory exists
    if not os.path.exists(github_dir):
        print(f"The github directory '{github_dir}' does not exist. Cloning...")
    # Clone the repository 
        subprocess.run(["git", "clone", github_url])
    else:
        print(f"The github directory '{github_dir}' already exists. Pulling...")

        # cd ineo-content
        os.chdir(github_dir)

         # Run git pull and capture the output
        result = subprocess.run(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the "Already up to date" message is in the output
        if "Already up to date." in result.stdout:
            print("Repository is already up to date. The RUC have not changed")
        else:
            print("Repository is not up to date.")

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
            print(f"Rich User Contents of {file_path} is:\n{ruc_contents}\n")
            all_ruc_contents[filename] = ruc_contents
            
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
        with open(json_file_path, "w") as json_file:
            json.dump(ruc_contents, json_file)

"""
main function
"""


def main():
    # Create the "data" folder if it doesn't exist
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # Serialize the RUC dictionary into JSON
    ruc_contents_dict = get_ruc_contents()
    serialize_ruc_to_json(ruc_contents_dict)

    table_name_ruc = "rich_user_contents"
    db_file_name = os.path.join(output_path_data, "ineo.db")
    (c_ruc, conn_ruc) = get_db_cursor(db_file_name=db_file_name, table_name=table_name_ruc)
    
    # Initialize the database connection and create the table if it doesn't exist
    table_name_tools = "tools_metadata"
    (c, conn) = get_db_cursor(db_file_name=db_file_name, table_name=table_name_tools)
    
    # download url and download dir are optional parameters, they have default value in the download_json_files function
    download_url = ""
    codemeta_download_dir = os.path.join(output_path_data, "tools_metadata")
    ruc_download_dir = os.path.join(output_path_data, "rich_user_contents")
    # get the current timestamp to be used in the database and make sure all the files in the same batch have the same timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # download the codemeta files
    jsonfiles = download_json_files()
    
    # check if previous batch exists in the "tools_metadata" table
    c.execute("SELECT * FROM tools_metadata ORDER BY timestamp DESC LIMIT 1")
    has_previous_batch = c.fetchone()
    if has_previous_batch is None:
        print("No codemeta previous batch exists in the database")
        previous_batch = None
        previous_timestamp = None
    else:
        previous_timestamp = has_previous_batch[2]
        if previous_timestamp is None:
            print("Error in getting the previous batch!")
            exit(1)
        
        previous_batch = get_previous_batch(db_file_name, table_name_tools, previous_timestamp=previous_timestamp)

    # Check for a previous batch in the "rich_user_contents" table
    c_ruc.execute("SELECT * FROM rich_user_contents ORDER BY timestamp DESC LIMIT 1")
    ruc_has_previous_batch = c_ruc.fetchone()
    if ruc_has_previous_batch is None:
        print("No rich_user_contents previous batch exists in the database")
        ruc_previous_batch = None
        previous_timestamp = None
    else:
        previous_timestamp = ruc_has_previous_batch[2]
        if previous_timestamp is None:
            print("Error in getting the previous rich_user_contents batch!")
            exit(1)

        ruc_previous_batch = get_previous_batch(db_file_name, table_name_ruc, previous_timestamp=previous_timestamp)   

    # after this line we have both dir1 and dir2, dir1 is the current batch and dir2 is the previous batch
    codemeta_current_batch = get_files(codemeta_download_dir)
    ruc_current_batch = get_files(ruc_download_dir)
    if codemeta_current_batch is None:
        print("No codemeta files found in the current batch!")
        exit(1)
    if ruc_current_batch is None:
        print("No RUC files found in the current batch!")
        exit(1)

    # compare the 2 lists and get the difference
    diff_list = compare_lists(codemeta_current_batch, previous_batch)
    diff_list_ruc = compare_lists(ruc_current_batch, ruc_previous_batch)

    # Process the Codemeta json files
    codemeta_folder_name = "tools_metadata"
    codemeta_output = "codemeta.jsonl"
    
    with jsonlines.open(os.path.join(output_path_data, codemeta_output), "w") as jsonlines_file:
        process_list(codemeta_folder_name, db_file_name, table_name_tools, diff_list, jsonlines_file, current_timestamp, None)

        if has_previous_batch is not None:
            # get previous batch from db
            c.execute("SELECT file_name, md5 FROM tools_metadata WHERE timestamp = ?", (previous_timestamp,))
            previous_batch = c.fetchall()
        
            # previous_batch_dict contains key value pair in the form of {file_name: md5}
            previous_batch_dict = {x[0]: x[1] for x in previous_batch}

            batch = [x.split("/")[-1]  for x in codemeta_current_batch]    
        
            # loop through current batch and compare with previous batch using hash values
            process_list(codemeta_folder_name, db_file_name, table_name_tools, batch, jsonlines_file, current_timestamp, previous_batch_dict)

        conn.commit()
    
    # Process the Rich User Contents.
    ruc_output = "ruc.jsonl"
    ruc_folder_name = "rich_user_contents"
    with jsonlines.open(os.path.join(output_path_data, ruc_output), "w") as ruc_jsonlines_file:
        process_list(ruc_folder_name, db_file_name, table_name_ruc, diff_list_ruc, ruc_jsonlines_file, current_timestamp, None)

        if ruc_has_previous_batch is not None:
            # get previous RUC batch from db
            c.execute("SELECT file_name, md5 FROM rich_user_contents WHERE timestamp = ?", (previous_timestamp,))
            ruc_previous_batch = c.fetchall()
        
            # previous_batch_dict contains key value pair in the form of {file_name: md5}
            ruc_previous_batch_dict = {x[0]: x[1] for x in ruc_previous_batch}

            ruc_batch = [x.split("/")[-1]  for x in ruc_current_batch]    
        
            # loop through current batch and compare with previous batch on hash value
            process_list(ruc_folder_name, db_file_name, table_name_ruc, ruc_batch, ruc_jsonlines_file, current_timestamp, ruc_previous_batch_dict)


        conn.commit()

if __name__ == '__main__':
    main()
