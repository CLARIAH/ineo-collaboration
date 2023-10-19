import os
import json
import requests
import sys
from dotenv import load_dotenv
import dotenv
import template



"""
This file loads some environment variables from a .env file
The .env file is NOT included in the repository, but is required to run this script
The .env file will be checked in into the private repo later
"""

load_dotenv()
api_token: str = dotenv.get_key('.env', 'API_TOKEN')
api_url = "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/resources/"
folder_path = "./processed_jsonfiles"
delete_path = "./deleted_documents"
# Define the header with the Authorization token 
header = {'Authorization': f'Bearer {api_token}'}

def get_id() -> list:
    """
    This function retrieves the ids of the processed files that need to go to INEO.  
    A document must always contain an id. This id equals the path to the resource. 
    So a document with id "alud" will be available at https://www.ineo.tools/resources/alud.
    """
    ids = []
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
                            ids.append(id_value)
                        else:
                            print(f"File {filename} does not contain an 'id' field.")
                    else:
                        print(f"File {filename} does not have the expected INEO structure.")
                except json.JSONDecodeError as e:
                    print(f"Error reading processed JSON from file {filename}: {str(e)}")
    # The unique "id" values from all JSON files to be fed or updated into INEO
    return ids

def load_processed_document(id, folder_path):
    file_path = os.path.join(folder_path, f"{id}_processed.json")
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def get_document(ids) -> list:
    """
    This code first checks if a tool with the given identifier exists in INEO by performing a GET request. 
    If a resource exists (status code 200) and does not return an empty list, it returns a list with the processed resources. 
    If the resource does not exist the API returns an empty list [] (not a status code 404). 

    """
    processed_document = []
    ids_to_update = []
    ids_to_create = []  
    for id in ids:
        get_url = f"{api_url}{id}"
        get_response = requests.get(get_url, headers=header)
        if get_response.status_code == 200:
            if get_response.text == '[]':
                resource_exists(get_response, id, ids_to_create)
            else:
                print(f"{id} is present in INEO")
                print(get_response.text)
                json_data = load_processed_document(id, folder_path)
                processed_document.append(json_data)
                ids_to_update.append(id)
        else:
            print("Error retrieving the resource from INEO")
            print(get_response.text)
    
    return processed_document, ids_to_create, ids_to_update


def resource_exists(get_response, id, ids_to_create):
    """
    Checks if a resource exists in INEO based on the GET response and appends the ID to the ids_to_create list
    if the resource does not exist.
    """
    if get_response.text == '[]':
        print(f"{id} does not exist in INEO.")
        # Append the ID to the list of resources to create in INEO
        ids_to_create.append(id)

def handle_empty(ids):
    """
    In case a resource does not exists in the INEO API (returns [], not a 404!), it will be created with a POST request.
    The default operation in a document is "create". 
    """
    # id of the document that is not present in INEO
    for id in ids:
        confirmation = input(f"Are you sure you want to create {id}? (y/n): ")
        if confirmation.lower() == 'y':
            print(f"Sending {id} to INEO...")
            file_name = f"{id}_processed.json"
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as new_document:
                new_document = json.load(new_document)
                create_response = requests.post(api_url, json=new_document, headers=header)
            if create_response.status_code == 200:
                print(f"Creation of {id} is successful")
                print(create_response.text)
            else:
                print(f"Creation of {id} has failed")
                print(create_response.text)
        else:
            print(f"Creation of {id} canceled.")


def update_document(documents, ids):
    """
    When the http request method is POST we can send resources to the INEO API. 
    There are three operations with POST: create, update and delete.
    This code handles an update operation if a resource already exists in INEO.
    If a resource exists (200), it changes the default operation "create" into "update" and performs a POST request.
    If a resource does not esixt we get an empty list []. 
    """
    for document, id in zip(documents, ids):
        confirmation = input(f"Are you sure you want to update {id}? (y/n): ")
        if confirmation.lower() == 'y':
            print(f"Updating tool {id}...")
        # change default operation "create" into "update"
            document[0]["operation"] = "update"
            update_response = requests.post(api_url, json=document, headers=header)
            if update_response.status_code == 200:
                print(f"Update of {id} is successful")
                print(update_response.text)
            else:
                print(f"Error updating {ids}")
                print(update_response.text)
        else:
            print(f"Update of {id} canceled.")

class ToolStillPresentError(Exception):
    pass


def delete_document(delete_list):
    """
    #TODO: boolean check whether it is deleted in INEO with a GET!
    If a document contains a delete operation, with a post request we can delete resources in INEO. 
    Only the id is needed to delete a resource.
    """
    # Check if the "deleted_documents" folder exists, and create it if not
    deleted_documents_folder = "deleted_documents"
    if not os.path.exists(deleted_documents_folder):
        os.makedirs(deleted_documents_folder)
    delete_template = "template_delete.json"
    file_path = os.path.join(deleted_documents_folder, delete_template)   
    
    for id in delete_list:
        # Read the delete template and insert the id of the tool to be deleted
        with open(file_path, 'r') as delete_file:
            delete_template = json.load(delete_file)
        delete_template[0]["document"]["id"] = id

        # Save the modified template with the id of the tool to be deleted
        output_file_path = os.path.join(deleted_documents_folder, f"{id}_delete.json")
        with open(output_file_path, 'w') as file:
            json.dump(delete_template, file, indent=4) 

        confirmation = input(f"Are you sure you want to delete {id}? (y/n): ")
        if confirmation.lower() == 'y':
            print(f"Deleting tool {id}...")
            update_response = requests.post(api_url, json=delete_template, headers=header)
            if update_response.status_code == 200:
                get_url = f"{api_url}{id}"
                get_response = requests.get(get_url, headers=header)
                if get_response.status_code == 200 and get_response.text == '[]':
                    print(f"Tool with id {id} deleted successfully.")
                else:
                    raise ToolStillPresentError(f"ERROR: {id} is still present in INEO")
            else:
                print(f"ERROR: cannot delete {id}")
                print(update_response.text)
        else:
            print(f"Deletion of tool with id {id} canceled.")


def main():
    processed_document_ids = get_id()
    processed_documents, ids_to_create, ids_to_update,  = get_document(processed_document_ids)  
    
    update_document(processed_documents, ids_to_update)
    handle_empty(ids_to_create)
    
    delete_list = ["test3"]
    try:
        delete_document(delete_list)
    except ToolStillPresentError as e:
        print(str(e))
        sys.exit(1) 

if __name__ == "__main__":
    main()
    