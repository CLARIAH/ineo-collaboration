import json
from fuzzywuzzy import fuzz

# Load the data from the nwo research fields 
with open('nwo-research-fields.json', 'r') as research_fields_file:
    nwo_data = json.load(research_fields_file)

# Load the data from the research domains
with open('researchDomain.json', 'r') as domains_file:
    domains_data = json.load(domains_file)

# Extract the "skos:prefLabel" values from the nwo data
nwo_field_labels = [entry['skos:prefLabel'] for entry in nwo_data['@graph'] if 'skos:prefLabel' in entry]

# Initialize lists to store exact matches and partial matches
exact_matches = []
partial_matches = []

# Iterate through the "result" entries in domains_data
for result_entry in domains_data['result']:
    exact_match_found = False
    
    # Check if the "title" exists in the nwo
    if result_entry['title'] in nwo_field_labels:
        # If there is an exact match, find the corresponding entry in the nwo data
        for entry in nwo_data['@graph']:
            if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == result_entry['title']:
                # Update the entry with the "skos:exactMatch" field in the desired format (e.g. "11.3 Cultural history")
                entry['skos:exactMatch'] = f"{result_entry['index']} {result_entry['title']}"
                exact_match_found = True
                exact_matches.append(result_entry['title'])
                break
    
    if not exact_match_found:
        best_match_score = 0
        best_match_label = None
        
        # If there's no exact match, find the best fuzzy match
        for label in nwo_field_labels:
            match_score = fuzz.ratio(label.lower(), result_entry['title'].lower())
            if match_score > best_match_score:
                best_match_score = match_score
                best_match_label = label
        
        # Check for the best match score (set on > 80)
        if best_match_score > 80:
            partial_matches.append(result_entry['title'])
            print(f'nwo data pref_label: {best_match_label}')
            print(f'variations in the titles of domains_data: {result_entry["title"]}')
            print()

            # Update the entry with the "skos:partialMatch" field (format: "skos:partialMatch": "13.7 Software, algorithms, operating systems")
            for entry in nwo_data['@graph']:
                if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == best_match_label:
                    entry['skos:partialMatch'] = f"{result_entry['index']} {result_entry['title']}"
                    break
        
# Save the updated research_fields_data back to the "now-research-fields.json" file
with open('nwo-research-fields_template.json', 'w') as research_fields_file:
    json.dump(nwo_data, research_fields_file, indent=4)
