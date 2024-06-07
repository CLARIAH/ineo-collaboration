import os
import time
import json
import requests
import sys
import logging
from dotenv import load_dotenv
import dotenv
from harvester import get_logger, get_files

log_file_path = 'ineo_sync.log'
logger = get_logger(log_file_path, __name__)
BULK_SIZE = 1000

"""
This file loads some environment variables from a .env file
The .env file is NOT included in the repository, but is required to run this script
The .env file will be checked in into the private repo later
"""

load_dotenv()

api_token: str = dotenv.get_key('.env', 'API_TOKEN')
# TODO: old dev api, kept for time being for reference
# api_url = "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/resources/"
# New dev api
api_url: str = dotenv.get_key('.env', 'API_URL')
processed_jsonfiles = "./processed_jsonfiles_tools"
processed_jsonfiles_ds = "./processed_jsonfiles_datasets"
processed_jsonfiles_huygens = "./processed_jsonfiles_huygens"
delete_path = "./deleted_documents"

# Define the header with the Authorization token 
header = {'Authorization': f'Bearer {api_token}'}

"""
This dictionary is used to keep track of the number of times a resource has failed to be 'actioned' against INEO API.
It's possible structure is as follows:
{
    "path/to/resource1.json": 1,
    "path/to/resource2.json": 2,
    "path/to/resource3.json": 3,
    "path/to/resource4.json": 4
} 
"""
ineo_api_error = {}


def get_id_json(folder_path) -> list:
    """
    This function retrieves the ids of the processed files that need to go to INEO.  
    A document must always contain an id. This id equals the path to the resource. 
    So a document with id "alud" will be available at https://www.ineo.tools/resources/alud.
    """
    ineo_ids = []
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
                            ineo_ids.append(id_value)
                        else:
                            logger.error(f"ERROR: File {filename} does not contain an 'id' field.")
                    else:
                        logger.error(f"ERROR: File {filename} does not have the expected INEO structure.")
                except json.JSONDecodeError as e:
                    logger.error(f"Error reading processed JSON from file {filename}: {str(e)}")
    # The unique "id" values from all processed JSON files to be fed or updated into INEO
    return ineo_ids


def load_processed_document(id, folder_path):
    file_path = os.path.join(folder_path, f"{id}_processed.json")
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def save_json_data_to_file(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def check_properties(id, folder_path, vocabs) -> None:
    """"
    This function checks whether the researchDomains and researchActivities in the processed templates matches INEO.
    There are some discrepancies, e.g. https://w3id.org/nwo-research-fields#TextualAndContentAnalysis (INEO) 
    and https://w3id.org/nwo-research-fields#TextualandContentAnalysis (processed Json file of Alud). 
    """
    properties_file_path = f"./properties/{vocabs}.json"
    
    if os.path.exists(properties_file_path):
        with open(properties_file_path, "r") as json_file:
            properties = json.load(json_file)
            processed_files = load_processed_document(id, folder_path)
            try:
                research_domains = processed_files[0]['document']['properties'][f'{vocabs}']
            except KeyError as e:
                research_domains = None
            
            # Check if research_domains is not None
            if research_domains is not None:
                # Filter out None values from research_domains
                research_domains = [domain for domain in research_domains if domain]

                updated_research_domains = []
                non_matches = []

                # Print results and update research domains
                for domain in research_domains:
                    # Check if the researchdomain (template) is directly in the links (INEO property). If there is a match found (case-insensitive e.g. TextualAndContentAnalysis (INEO) == TextualandContentAnalysis (codemeta))
                        # the value of the processed.jsonfile is replaced with the property from INEO (so TextualAndContentAnalysis)
                    matches = [entry for entry in properties if entry['link'].lower() == domain.lower()]
                    if matches:
                        logger.info(f"Match found: {domain}")
                        corresponding_link = matches[0]['link']
                        updated_research_domains.append(corresponding_link)
                    else:
                        # Check if the domain is in the titles (mapping subjects datasets)
                        matches_in_titles = [entry for entry in properties if domain.lower() in entry['title'].lower()]
                        if matches_in_titles:
                            logger.info(f"Match found in title: {domain}")
                            corresponding_entry = matches_in_titles[0]
                            updated_research_domains.append(corresponding_entry['link'])
                        else:
                            logger.info(f"No match found for: {domain}")
                            non_matches.append(domain)
                            logger.info(f"no matches for: {non_matches}")

                # Update the researchDomains value in the data
                processed_files[0]['document']['properties'][f'{vocabs}'] = updated_research_domains

                # Save the updated data back to the same JSON file
                json_file_path = f"./{folder_path}/{id}_processed.json"
                save_json_data_to_file(processed_files, json_file_path)


def get_document(ids: list[str], processed_jsonfiles: list[str]) -> tuple[list, list, list]:
    """
    This code first checks if a tool with the given identifier exists in INEO by performing a GET request. 
    If a resource exists (status code 200) and does not return an empty list, it returns a list with the processed resources. 
    If the resource does not exist the API returns an empty list [] (not a status code 404). 

    - id (str): Identifier of the processed files.
    - folder_path (str): Path to the folder containing the processed files.
    - vocabs (str): Name of the property (e.g., "researchDomains" or "researchActivities").

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
                logger.info(f"{id} is present in INEO")
                logger.info(get_response.text)
                json_data = load_processed_document(id, processed_jsonfiles)
                processed_document.append(json_data)
                ids_to_update.append(id)
        else:
            logger.error("Error retrieving the resource from INEO")
            logger.info(get_response.text)
    
    return processed_document, ids_to_create, ids_to_update


def resource_exists(get_response, id, ids_to_create):
    """
    Checks if a resource exists in INEO based on the GET response and appends the ID to the ids_to_create list
    if the resource does not exist.
    """
    if get_response.text == '[]':
        logger.debug(f"{id} does not exist in INEO.")
        # Append the ID to the list of resources to create in INEO
        ids_to_create.append(id)


def handle_empty(ids, processed_jsonfiles, force_yes=False):
    """
    In case a resource does not exist in the INEO API (returns [], not a 404!), it will be created with a POST request.
    The default operation in a document is "create". 
    """
    if not force_yes:
        force_yes = input("Do you want to force 'yes' for all new tools (create)? (y/n): ").lower() == 'y'

    for id in ids:
        if not force_yes:
            confirmation = input(f"Are you sure you want to create {id}? (y/n): ")
            if confirmation.lower() != 'y':
                logger.info(f"Creation of {id} canceled.")
                continue
        
        logger.info(f"Sending {id} to INEO...")
        file_name = f"{id}_processed.json"
        file_path = os.path.join(processed_jsonfiles, file_name)
  
        with open(file_path, 'r') as new_document:
            new_document = json.load(new_document)
            create_response = requests.post(api_url, json=new_document, headers=header)
        
        if create_response.status_code == 200:
            logger.info(f"Creation of {id} is successful")
            logger.debug(create_response.text)
            # logger.info(f"New resource available here: https://ineo-git-feature-api-resource-eightmedia.vercel.app/resources/{id}")
            logger.info(f"New resource available here: https://ineo-git-development-eightmedia.vercel.app/resources/{id}")
        else:
            logger.error(f"Creation of {id} has failed")
            logger.debug(create_response.text)


def update_document(documents, ids, force_yes=False):
    """
    When the http request method is POST we can send resources to the INEO API. 
    There are three operations with POST: create, update, and delete.
    This code handles an update operation if a resource already exists in INEO.
    If a resource exists (200), it changes the default operation "create" into "update" and performs a POST request.
    If a resource does not exist, we get an empty list [].
    """
    if not force_yes:
        force_yes = input("Do you want to force 'yes' for all updates? (y/n): ").lower() == 'y'
    
    for document, id in zip(documents, ids):
        if not force_yes:
            confirmation = input(f"Are you sure you want to update {id}? (y/n): ")
            if confirmation.lower() != 'y':
                logger.info(f"Update of {id} canceled.")
                continue
        
        logger.info(f"Updating tool {id}...")
        # change default operation "create" into "update"
        document[0]["operation"] = "update"
        update_response = requests.post(api_url, json=document, headers=header)
        
        if update_response.status_code == 200:
            logger.info(f"Update of {id} is successful")
            logger.info(update_response.text)
            logger.info(f"Updated resource available here: https://ineo-git-feature-api-resource-eightmedia.vercel.app/resources/{id}")
        else:
            logger.error(f"Error updating {ids}")
            logger.info(update_response.text)


class ToolStillPresentError(Exception):
    pass


def create_delete_template():
    delete_template = [
        {
            "operation": "delete",
            "document": {
                "id": ""
            }
        }
    ]

    # Specify the file path where you want to save the template
    file_path = "./deleted_documents/delete_template.json"

    # Save the delete_template to the specified file
    with open(file_path, 'w') as json_file:
        json.dump(delete_template, json_file, indent=4)

    return delete_template 


def delete_document(delete_list, force_yes=False):
    """
    If a document contains a delete operation, with a post request we can delete resources in INEO. 
    Only the id is needed to delete a resource.
    """
    # Check if the "deleted_documents" folder exists, and create it if not
    deleted_documents_folder = "deleted_documents"
    delete_template = create_delete_template()
    file_path = os.path.join(deleted_documents_folder, "delete_template.json")   
    if not force_yes:
        force_yes = input("Do you want to force 'yes' for all deletions? (y/n): ").lower() == 'y'
    
    for id in delete_list:
        # Read the delete template and insert the id of the tool to be deleted
        with open(file_path, 'r') as delete_file:
            delete_template = json.load(delete_file)
            delete_template[0]["document"]["id"] = id

        # Save the modified template with the id of the tool to be deleted
        output_file_path = os.path.join(deleted_documents_folder, f"{id}_delete.json")
        with open(output_file_path, 'w') as file:
            json.dump(delete_template, file, indent=4) 

        if not force_yes:
            confirmation = input(f"Are you sure you want to delete {id}? (y/n): ")
            if confirmation.lower() != 'y':
                logger.info(f"Deletion of resource with id {id} canceled.")
                continue
        
        logger.info(f"Deleting resource {id}...")
        update_response = requests.post(api_url, json=delete_template, headers=header)
        
        if update_response.status_code == 200:
            get_url = f"{api_url}{id}"
            get_response = requests.get(get_url, headers=header)
            if get_response.status_code == 200 and get_response.text == '[]':
                logger.info(f"Resource with id {id} deleted successfully.")
            else:
                raise ToolStillPresentError(f"ERROR: {id} is still present in INEO")
        else:
            logger.error(f"ERROR: cannot delete {id}")
            logger.info(update_response.text)


def call_ineo_single_package(ineo_package: list[dict], api_url: str, action: str = "POST") -> None:
    """
    This function calls the INEO API to create or update resources.

    :param ineo_package: list[dict], a single ineo package, a list with a single dictionary element
    :param api_url: str
    :param action: str
    :return: None
    """
    ineo_package_json = json.dumps(ineo_package)
    ineo_action: str = ineo_package[0]["operation"]
    ineo_id: str = ineo_package[0]["document"]["id"]

    if action == "POST":
        response = requests.post(api_url, json=ineo_package_json, headers=header)
    else:
        logger.error("HTTP action not implemented yet, please use POST")
        sys.exit(1)

    if response.status_code == 200:
        logger.info(f"{ineo_id} {ineo_action} successfully.")
    else:
        logger.error(f"Action {ineo_action} on resource {ineo_package} failed....")
        logger.error(f"Response: {response.status_code} - {response.text}")


def call_ineo_single_package_from_file(ineo_package: str, api_url: str, action: str = "POST") -> None:
    """
    This function calls the INEO API to create or update resources.

    :param ineo_package: str
    :param api_url: str
    :param action: str
    :return: None
    """
    try:
        with open(ineo_package, 'r') as json_file:
            ineo_package_json = json.load(json_file)
    except Exception as e:
        logger.error(f"Error reading JSON from file {ineo_package}: {str(e)}")
        exit()
    if action == "POST":
        response = requests.post(api_url, json=ineo_package_json, headers=header)
    else:
        logger.error("HTTP action not implemented yet, please use POST")
        sys.exit(1)

    if response.status_code != 200:
        ineo_action: str = ineo_package_json[0]["operation"]
        logger.debug(f"Action {ineo_action} on resource {ineo_package} failed. Retrying ...")
        logger.debug(f"Response: {response.status_code} - {response.text}")
        if ineo_action == "create":
            ineo_package_json[0]["operation"] = "update"
            with open(ineo_package, 'w') as json_file:
                json.dump(ineo_package_json, json_file)
            with open(ineo_package, 'r') as json_file:
                ineo_package_json = json.load(json_file)
                logger.debug(f"new package: {ineo_package_json}")
        elif ineo_action == "update":
            ineo_package_json[0]["operation"] = "create"
            with open(ineo_package, 'w') as json_file:
                json.dump(ineo_package_json, json_file)
            logger.debug(f"update action as well failed, giving up.")
            return
        elif ineo_action == "delete":
            logger.error("Deletion not implemented yet")
            return
        else:
            logger.error("Unknown action")
            return

        error_counter = ineo_api_error.get(ineo_package, 0)
        if error_counter < 1:
            ineo_api_error[ineo_package] = error_counter + 1
            # TODO FIXME: recursion is not working as expected, ineo_package is a dot
            logger.debug(f"Recursion on {ineo_package} ...")
            call_ineo_single_package_from_file(ineo_package, api_url, action)
        else:
            logger.error(f"Action on resource {ineo_package} failed after {error_counter} time(s).")
            return

    else:
        id: str = ineo_package_json[0]["document"]["id"]
        print(
            f"Updated resource available here: "
            f"https://ineo-git-feature-api-resource-eightmedia.vercel.app/resources/{id}")
        logger.info(f"Action on resource {ineo_package} successful.")
    print(f"#### Response {response.status_code} - {response.text}")


def call_ineo_with_files(ineo_packages: list, api_url: str, action: str = "POST") -> None:
    """
    This function calls the INEO API to create or update resources.

    :param ineo_packages: list
    :param api_url: str
    :param action: str
    :return: None
    """
    for ineo_package in ineo_packages:
        call_ineo_single_package_from_file(ineo_package, api_url, action)


def call_ineo_bulk(ineo_package: list, api_url: str) -> None:
    """
    This function calls the INEO API to create or update resources in bulk.

    :param ineo_package: list
    :param api_url: str
    :param action: str
    :return: None
    """
    try:
        print(f"this is the api called: {api_url}")
        response = requests.post(api_url, json=ineo_package, headers=header)
    except Exception as e:
        logger.error(f"Error calling INEO API: {str(e)}")
        exit(1)

    if response.status_code != 200:
        logger.error(f"Action on resources failed.")

    print(f"#### Response {response.status_code} - {api_url} - {response.text}")


def sync_with_ineo(record_type: str = "tools", limit: int = 0, remove_first: bool = False) -> None:
    """
    This function syncs either tools or datasets with ineo depends on the parameters passed.

    :param record_type: str
    :param limit: int limit the amount of packages to sync
    :param remove_first: bool remove the packages first before syncing
    :return: None

    """
    # check tool properties and replace with INEO property if match is found
    if record_type == "tools":
        processed_files = processed_jsonfiles
    elif record_type == "datasets":
        processed_files = processed_jsonfiles_ds
    elif record_type == "huygens":
        processed_files = processed_jsonfiles_huygens
    else:
        logger.error(f"Record type {record_type} not implemented yet.")
        sys.exit(1)

    processed_document_ids = get_id_json(processed_files)
    for processed_id in processed_document_ids:
        if record_type in ["tools", "datasets"]:
            check_properties(processed_id, processed_files, vocabs="researchDomains")
        if record_type == "tools":
            check_properties(processed_id, processed_files, vocabs="researchActivities")

    # call ineo api on given record type
    if limit > 0:
        logger.debug(f"Limiting the number of {record_type} packages to sync to {limit}")
        ineo_packages: list = get_files(processed_files)[:limit]
    else:
        logger.debug(f"Syncing all {record_type} packages.")
        ineo_packages: list | None = get_files(processed_files)

    if ineo_packages is None or len(ineo_packages) == 0:
        logger.info(f"No packages found in the {record_type} processed folder.")
        exit(0)
    else:
        logger.info(f"Found {len(ineo_packages)} packages in the {record_type}. Syncing ...")
        bulk_package: list = []
        for package in ineo_packages:
            with open(package, 'r') as json_file:
                ineo_package = json.load(json_file)
                bulk_package.append(ineo_package[0])

        if remove_first:
            bulk_delete_package: list = bulk_package.copy()
            logger.info(f"{remove_first=}, deleting {len(bulk_package)} {record_type} packages.")
            print(f"{remove_first=}, deleting {len(bulk_package)} {record_type} packages.")
            for package in bulk_delete_package:
                package["operation"] = "delete"
            call_ineo_bulk(bulk_delete_package, api_url)
            logger.info(f"Deleted {len(bulk_delete_package)} {record_type} packages.")

        # Syncing the packages in bulk or batch
        logger.info(f"Syncing in total {len(bulk_package)} {record_type} packages.")
        print(f"Syncing in total {len(bulk_package)} {record_type} packages.")
        if len(bulk_package) > BULK_SIZE:
            logger.info(f"Syncing {len(bulk_package)} {record_type} packages in batches of size {BULK_SIZE}.")
            print(f"Syncing {len(bulk_package)} {record_type} packages in batches of size {BULK_SIZE}.")
            for i in range(0, len(bulk_package), BULK_SIZE):
                logger.info(f"Syncing {i} to {i + BULK_SIZE} {record_type} packages.")
                print(f"Syncing {i} to {i + BULK_SIZE} {record_type} packages.")
                call_ineo_bulk(bulk_package[i:i + BULK_SIZE], api_url)
                time.sleep(10)
        else:
            logger.info(f"Syncing {len(bulk_package)} {record_type} packages in bulk.")
            print(f"Syncing {len(bulk_package)} {record_type} packages in bulk.")
            call_ineo_bulk(bulk_package, api_url)


def main(record_type: str, limit: int = 5, remove_before_create: bool = False) -> None:
    sync_with_ineo(record_type, limit, remove_before_create)

    logger.info("Sync done, deletion skipped. returning none...")
    return None

    # TODO: implement deletion
    # Check if there are files to delete
    # imports a json file that contains the ids of the tools that needs to be deleted (outcome of harvester.py)
    if not os.path.exists(delete_path):
        logger.info(f"The folder {delete_path} does not exist, no tools to delete.")
        sys.exit(1)
    else:
        delete_file_path = f"{delete_path}/deleted_tool_ids.json"
        with open(delete_file_path, 'r') as json_file:
            delete_list = json.load(json_file)
            try:
                delete_document(delete_list)
            except ToolStillPresentError as e:
                logger.error(str(e))
                sys.exit(1) 


if __name__ == "__main__":
    # exit("Please call from main")
    main(limit=1)
    # main()
    