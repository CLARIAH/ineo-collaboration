import json
import requests
import os
import dotenv
from dotenv import load_dotenv
from harvester import configure_logger

load_dotenv()
api_token: str = dotenv.get_key('.env', 'API_TOKEN')
log_file_path = 'get_properties.log'
log = configure_logger(log_file_path)

urls_properties = [
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/languages",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/status",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/mediaTypes",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/resourceTypes",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchActivities",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchDomains",
    "https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/informationTypes"
]

# Define the headers with the Authorization token
headers = {
    'Authorization': f'Bearer {api_token}'
}

def main():
    folder_properties = 'properties/'
    if not os.path.exists(folder_properties):
        os.makedirs(folder_properties)

    for url in urls_properties:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            properties = response.json()
            filename = url.split("/")[-1]
            file_path = os.path.join(folder_properties, f'{filename}.json')
            with open(file_path, 'w') as json_file:
                json.dump(properties, json_file, indent=4)
            print(f"JSON data for {url} saved to {file_path}")
        else:
            print(f"Request for {url} failed with status code {response.status_code}")
            print(response.text)


if __name__ == '__main__':
    main()