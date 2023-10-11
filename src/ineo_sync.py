import os
import json
import requests
from dotenv import load_dotenv
import dotenv


"""
This file loads some environment variables from a .env file
The .env file is NOT included in the repository, but is required to run this script
The .env file will be checked in into the private repo later
"""

load_dotenv()
api_token: str = dotenv.get_key('.env', 'API_TOKEN')
api_url = "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/resources/"
folder_path = "./processed_jsonfiles"

# Define the header with the Authorization token 
header = {'Authorization': f'Bearer {api_token}'}

def get_id() -> set:
    """
    A document must always contain an id. This id equals the path to the resource. 
    So a document with id "alud" will be available at https://www.ineo.tools/resources/alud.
    """
    unique_ids = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as json_file:
                try:
                    document = json.load(json_file)
                    # a document is a list with a single dictionary element
                    if isinstance(document, list) and len(document) == 1:
                        # a document must always contain an id
                        id_value = document[0].get("document", {}).get("id")
                        if id_value is not None:
                            unique_ids.add(id_value)
                        else:
                            print(f"File {filename} does not contain an 'id' field.")
                    else:
                        print(f"File {filename} does not have the expected INEO structure.")
                except json.JSONDecodeError as e:
                    print(f"Error reading JSON from file {filename}: {str(e)}")
    # The unique "id" values from all JSON files to be fed or updated into INEO
    return unique_ids

def get_document(ids) -> list:
    """
    This code first checks if a tool with the given identifier exists by performing a GET request. 
    If it exists (status code 200), it returns a list with the processed resources. 
    
    """
    document_list = []
    for id in ids:
        get_url = f"{api_url}{id}"
        get_response = requests.get(get_url, headers=header)
        if get_response.status_code == 200:
            file_path = os.path.join(folder_path, f"{id}_processed.json")
            with open(file_path, 'r') as json_file:
                json_data = json.load(json_file)
                document_list.append(json_data)
    return document_list

def handle_empty(id, header):
    """
    In case a resources does not exists in API (404), it will be created with a POST request.
    The default operation in a document is "create". 
    """
    with open(f"{id}_processed.json", 'r') as json_file:
        json_data = json.load(json_file)
        # the resource does not exist, so create it
        create_response = requests.post(api_url, json=json_data, headers=header)
    if create_response.status_code == 200:
        print(f"Creation of tool {id} is successful")
        print(create_response.text)
    else:
        print(f"Creation of tool {id} has failed")
        print(create_response.text)

def update_api(documents, ids):
    """
    When the http request method is POST we can send resources to the INEO API. 
    There are three operations with POST: create, update and delete.
    This code handles an update operation if a resource already exists in INEO.
    If a resource exists (200), it changes the default operation "create" into "update"
    and performs a POST request.
    If a resource does not esixt we get a 404 
    """
    for id, document in zip(ids, documents):
        # change default operation "create" into "update"
        document[0]["operation"] = "update"
        update_response = requests.post(api_url, json=document, headers=header)
        if update_response.status_code == 200:
            print(f"Update of {id} is successful")
            print(update_response.text)
        elif update_response.status_code == 404:
            # The resource does not exist
            handle_empty(id, header)
        else:
            print('Error checking the tool')
            print(update_response.text)

def main():
    unique_ids = get_id()
    documents = get_document(unique_ids)
    update_api(documents, unique_ids)

if __name__ == "__main__":
    main()