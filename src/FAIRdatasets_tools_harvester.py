import os
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
import hashlib
import sqlite3
from datetime import datetime
import jsonlines
import json
import shutil
import subprocess

output_path = "/data"

def get_db_cursor(db_file_name="tools_metadata.db", table_name="tools_metadata"):
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
    if file_name.endswith('.json'):
        md5_file = get_canonical(file_name)
    
    hash_md5 = hashlib.md5()
    with open(md5_file, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_json_files(
        url: str = "https://tools.clariah.nl/files/",
        save_directory: str = "tools_metadata") -> List[str]:
    """
    Download and count all individual json files

    """
    # first backup previous JSON files
    backup_directory = "tools_metadata_backup"
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
    print(list2)
    list2_copy = [x.split("/")[-1] for x in list2]
    
    # getting elements in l1 not in l2
    diff = []
    if list1 is not None and len(list1) > 0:
        list1_path = list1[0].split("/")[0]
        list1_list2 = list(set(list1_copy) - set(list2_copy))
        diff = [f"{list1_path}/{x}" for x in list1_list2]
    print(f"list1 diff is {diff}")

    # getting elements in l2 not in l1
    diff2 = []
    if list2 is not None and len(list2) > 0:
        list2_path = list2[0].split("/")[0]
        list2_list1 = list(set(list2_copy) - set(list1_copy))
        diff2 = [f"{list2_path}/{x}" for x in list2_list1]
    print(f"list2 diff is {diff2}")
    return diff + diff2

def create_db_table(conn: sqlite3.Connection, table_name: str = "tools_metadata") -> None:
    """
    create a table in the database
    """
    c = conn.cursor()
    c.execute(f"CREATE TABLE {table_name} (file_name text, md5 text, timestamp text DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()


def db_table_exists(conn: sqlite3.Connection, table_name: str = "tools_metadata") -> bool:
    """
    check if the table exists in the database
    """
    c = conn.cursor()
    c.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if c.fetchone()[0] == 1:
        return True
    return False

def process_list(diff_list, jsonlines_file, current_timestamp, previous_batch_dict=None):
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
    for file in diff_list:
        canon_file = get_canonical(file)
        md5 = get_md5(canon_file)
        previous_md5 = previous_batch_dict.get(file, None) if previous_batch_dict is not None else None

        if md5 != previous_md5:
            if previous_md5 is not None:
                print(f"File {file} has changed! Old hash was: {previous_md5}")
            add_to_jsonlines(file, jsonlines_file)
        else:
            print(f"File {file} has not changed.")
        c.execute("INSERT INTO tools_metadata (file_name, md5, timestamp) VALUES (?, ?, ?)", (file, md5, current_timestamp))


def init_check_db(db_file_name: str, table_name: str) -> Optional[sqlite3.Connection]:
    """
    check if the database exists, if not create one
    """
    conn = sqlite3.connect(db_file_name)
    
    # check if table exists
    if not db_table_exists(conn, table_name):
        print(f"Table {table_name} does not exist, creating!")
        create_db_table(conn, table_name)

    return conn

def get_previous_batch(previous_timestamp, table_name: str = "tools_metadata") -> List[str]:
    c, conn = get_db_cursor()
    c.execute(f"SELECT file_name FROM {table_name} WHERE timestamp = ?", (previous_timestamp,))
    previous_batch = c.fetchall()
    # process list of tuples to list of strings
    previous_batch = [x[0] for x in previous_batch]

    return previous_batch

def sync_ruc(github_url, github_dir):
    """
    Retrieves Rich User Content of Gihub repistory ineo-content. 
    """

    # Check if the ineo-content github repository directory exists
    if not os.path.exists(github_dir):
    # Clone the repository 
        subprocess.run(["git", "clone", github_url])
    else:
        print(f"The github directory '{github_dir}' already exists.")

    # cd ineo-content
    os.chdir(github_dir)

    # Pull the latest changes
    subprocess.run(["git", "pull"])



"""
main function
"""

if __name__ == '__main__':

    # rich user content: clone and pull changes github repository ineo-content
    github_url = "https://github.com/CLARIAH/ineo-content.git"
    github_dir = "./ineo-content"
    sync_ruc(github_url, github_dir)

    tools_folder = os.path.join(github_dir, "src", "tools")  # Separate "src" and "tools" with commas
    
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"tools folder path: {tools_folder}")
    
    if os.path.exists(tools_folder):
        files = os.listdir(tools_folder)
        for file in files:
            print(file)
    else:
        print("tools folder does not exist.")

    exit()
    c, conn = get_db_cursor()
    # if you want to keep older json files, please copy them to a different folder
    # backup_json_files(older_filder, new_folder)

    # get all the json files
    # download url and download dir are optional parameters, they have default value in the download_json_files function
    download_url = ""
    download_dir = "tools_metadata"

    # get the current timestamp to be used in the database and make sure all the files in the same batch have the same timestamp
    current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # download the json files
    jsonfiles = download_json_files()
    # jsonfiles = download_json_files("http://mylink.com/", "mydownloadedfiles/")

    # check if previous batch exists
    c.execute("SELECT * FROM tools_metadata ORDER BY timestamp DESC LIMIT 1")
    has_previous_batch = c.fetchone()
    if has_previous_batch is None:
        print("No previous batch exists in the database")
        previous_batch = None
        previous_timestamp = None
    else:
        previous_timestamp = has_previous_batch[2]
        if previous_timestamp is None:
            print("Error in getting the previous batch!")
            exit(1)
        
        previous_batch = get_previous_batch(previous_timestamp=previous_timestamp)

    # after this line we have both dir1 and dir2, dir1 is the current batch and dir2 is the previous batch
    current_batch = get_files(download_dir)
    if current_batch is None:
        print("No files found in the current batch!")
        exit(1)

    # compare the 2 lists and get the difference
    diff_list = compare_lists(current_batch, previous_batch)

    #with jsonlines.open(os.path.join(output_path, "codemeta.jsonl"), "w") as jsonlines_file:
    with jsonlines.open("codemeta.jsonl", "w") as jsonlines_file:
        process_list(diff_list, jsonlines_file, current_timestamp, None)

        if has_previous_batch is not None:
            # get previous batch from db
            c.execute("SELECT file_name, md5 FROM tools_metadata WHERE timestamp = ?", (previous_timestamp,))
            previous_batch = c.fetchall()
            # previous_batch_dict contains key value pair in the form of {file_name: md5}
            previous_batch_dict = {x[0]: x[1] for x in previous_batch}

            # loop through current batch and compare with previous batch on hash value
            process_list(current_batch, jsonlines_file, current_timestamp, previous_batch_dict)

        conn.commit()

    # RumbleDB query (rating >= 3 stars)
    print("Generating RumbleDB query...")
    rumble_query = """
        for $i in json-file("/data/codemeta.jsonl",10)
        where $i.review.reviewRating ge 3
        return $i.identifier
        """
    #with open(os.path.join(output_path, "rumbledb.rq"), "w") as file:
    with open("rumble_query.rq", "w") as file:    
        file.write(rumble_query)
    print("Done!")
