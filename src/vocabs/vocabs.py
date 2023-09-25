import json
import copy
from fuzzywuzzy import fuzz

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
        item["nl_link"] = new_link

def find_exact_match(nwo_data, nwo_field_labels, result_entry):
    for entry in nwo_data['@graph']:
        if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == result_entry['title']:
            entry['skos:exactMatch'] = f"{result_entry['index']} {result_entry['title']}"
            return True
    return False

def find_partial_match(nwo_data, nwo_field_labels, result_entry):
    best_match_score = 0
    best_match_label = None
    
    for label in nwo_field_labels:
        match_score = fuzz.ratio(label.lower(), result_entry['title'].lower())
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_label = label
    
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
            index_to_id_map[match.split()[0]] = entry['@id']
    return index_to_id_map


def main():

    # Load data
    nwo_data = load_json('nwo-research-fields.json')
    domains_data = load_json('researchDomains.json')
    activity_data = load_json('researchActivity.json')
    
    # Update links in activity_data
    update_links(activity_data)

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

    # Update "link" and "partialLink" fields in domains_data
    for result_entry in domains_data['result']:
        index = result_entry['index']
        
        # Update "link" field
        if index in exact_index_to_id_map:
            result_entry['link'] = exact_index_to_id_map[index]
        
        # Update "partialLink" field
        if index in partial_index_to_id_map:
            result_entry['link'] = partial_index_to_id_map[index]

    # Save updated data
    save_json(nwo_data, 'nwo-research-fields_template.json')
    save_json(domains_data, 'researchDomains_template.json')
    save_json(activity_data, 'researchActivity_template.json')


if __name__ == "__main__":
    main()
