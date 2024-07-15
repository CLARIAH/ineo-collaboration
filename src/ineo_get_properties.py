import json
import requests
import os
import dotenv
from dotenv import load_dotenv
from harvester import get_logger

load_dotenv()
api_token: str = dotenv.get_key('.env', 'API_TOKEN')

log_file_path = 'get_properties.log'
log = get_logger(log_file_path, __name__)

# urls_properties = [
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/languages",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/status",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/mediaTypes",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/resourceTypes",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchActivities",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchDomains",
#     "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/informationTypes"
# ]
api_url = dotenv.get_key('.env', 'API_URL')
api_url = api_url.replace("/resources", "/properties")
urls_properties = [
    f"{api_url}languages",
    f"{api_url}status",
    f"{api_url}mediaTypes",
    f"{api_url}resourceTypes",
    f"{api_url}researchActivities",
    f"{api_url}researchDomains",
    f"{api_url}informationTypes"
]

# Define the headers with the Authorization token
headers = {
    'Authorization': f'Bearer {api_token}'
}


def main() -> None:
    """
    This function retrieves the properties from the INEO API and saves them to a JSON file.
    """
    folder_properties = 'properties/'
    if os.path.isdir(folder_properties):
        # if folder exists and json files are present, return
        if len(os.listdir(folder_properties)) > 1:
            log.info(f"Properties already downloaded {folder_properties}")
        return
    else:
        os.makedirs(folder_properties)

    for url in urls_properties:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            properties = response.json()
            filename = url.split("/")[-1]
            file_path = os.path.join(folder_properties, f'{filename}.json')
            with open(file_path, 'w') as json_file:
                json.dump(properties, json_file, indent=4)
            log.info(f"JSON data for {url} saved to {file_path}")
        else:
            log.error(f"Request for {url} failed with status code {response.status_code}")
            log.debug(response.text)


if __name__ == '__main__':
    main()
