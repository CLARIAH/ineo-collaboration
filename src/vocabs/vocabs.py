import json
import shutil
from fuzzywuzzy import fuzz
import requests
from datetime import datetime

def load_json(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

def save_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_links(activity_data):
    for item in activity_data["result"]:
        old_link = item["link"]
        new_link = old_link.replace("https://vocabs.dariah.eu/tadirah2/en/page/", "https://vocabs.dariah.eu/tadirah/")
        item['link_en'] = item['link']
        item["link"] = new_link
        del item["link_en"]

# Function to find an exact match in nwo_data (e.g. "skos:prefLabel": "Modern and contemporary history") based on the "title" of research domains (e.g. "title": "Modern and contemporary history")
def find_exact_match(nwo_data, nwo_field_labels, result_entry):
    for entry in nwo_data['@graph']:
        if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == result_entry['title']:
            entry['skos:exactMatch'] = f"{result_entry['index']} {result_entry['title']}"
            return True
    return False

# Function to find a partial match in nwo_data (e.g. "skos:prefLabel": "Computers and the humanities") based on the "title" of research domains (e.g. "title": "Computers and humanities")
# The fuzzy string matching process allows to handle cases where there might be slight variations or typos in the strings between the nwo data and the researchDomains data, 
def find_partial_match(nwo_data, nwo_field_labels, result_entry):
    best_match_score = 0
    best_match_label = None
    
    # Calculating a similarity score using fuzz.ratio with the lowercase versions of the preflabels and the lowercase version of the research domains titles.
    for label in nwo_field_labels:
        match_score = fuzz.ratio(label.lower(), result_entry['title'].lower())
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_label = label
    
    # If the best match score is above 80, it a valid partial match which is then stored in the skos:partialMatch field in nwo_data.
    if best_match_score > 80:
        for entry in nwo_data['@graph']:
            if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == best_match_label:
                entry['skos:partialMatch'] = f"{result_entry['index']} {result_entry['title']}"
                return True
    return False

def create_index_to_id_map(nwo_data, field):
    index_to_id_map = {}
    for entry in nwo_data['@graph']:
        if field in entry and '@id' in entry:
            match = entry[field]
            index_to_id_map[match.split()[0]] = entry['@id'] # Extract the index (e.g., '1.2' from '1.2 Archeology of the Middle Ages')
    return index_to_id_map


def main():

    # Define the file names
    domains_data_file = 'researchDomains.json'
    activity_data_file = 'researchActivity.json'
    nwo_data_file = 'nwo-research-fields.json'
    nwo_manual_data_file = 'nwo-research-fields_template+manual.json'
    
    # Load data
    nwo_data = load_json(nwo_data_file)
    domains_data = load_json(domains_data_file)
    activity_data = load_json(activity_data_file )
    nwo_manual_data = load_json(nwo_manual_data_file)
    
    # Define the backup file names
    domains_backup_file = 'researchDomains_backup.json'
    activity_backup_file = 'researchActivity_backup.json'

    # Create copies of the original files as backups
    shutil.copy(domains_data_file, domains_backup_file)
    shutil.copy(activity_data_file, activity_backup_file)

    # Update links in activity_data
    update_links(activity_data)

    # Check and print the tadirah links to see if they work
    for item in activity_data["result"]:
        link = item["link"]
        response = requests.get(link)
        if response.status_code == 200:
            print(f"Link: {link} - Status: Working")
        else:
            print(f"Link: {link} - Status: Not Working")


    # Extract "skos:prefLabel" values from nwo_data
    nwo_field_labels = [entry['skos:prefLabel'] for entry in nwo_data['@graph'] if 'skos:prefLabel' in entry]

    # Initialize lists to store exact matches and partial matches
    exact_matches = []
    partial_matches = []

    # Iterate through "result" entries in domains_data
    for result_entry in domains_data['result']:
        exact_match_found = find_exact_match(nwo_data, nwo_field_labels, result_entry)
        
        if not exact_match_found:
            partial_match_found = find_partial_match(nwo_data, nwo_field_labels, result_entry)
            if partial_match_found:
                partial_matches.append(result_entry['title'])

    # Create index-to-id mappings for "skos:exactMatch" and "skos:partialMatch"
    exact_index_to_id_map = create_index_to_id_map(nwo_data, 'skos:exactMatch')
    partial_index_to_id_map = create_index_to_id_map(nwo_data, 'skos:partialMatch')
    manual_index_to_id_map = create_index_to_id_map(nwo_manual_data, 'skos:manualMatch')
    
    # Update "link" and "partialLink" fields in domains_data
    for result_entry in domains_data['result']:
        index = result_entry['index']
        
        # Update "link" field based on the exact matches
        if index in exact_index_to_id_map:
            result_entry['link'] = exact_index_to_id_map[index]
        
        # Update "link" field based on the partial matches
        if index in partial_index_to_id_map:
            result_entry['link'] = partial_index_to_id_map[index]

        # Update "link" field based on the manual matches
        if index in manual_index_to_id_map:
            result_entry['link'] = manual_index_to_id_map[index]

    # Save updated data
    save_json(nwo_data, 'nwo-research-fields_template.json')
    save_json(domains_data, 'researchDomains.json')
    save_json(activity_data, 'researchActivity.json')


if __name__ == "__main__":
    main()
