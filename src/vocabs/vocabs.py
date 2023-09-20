import json

# Load the data from the nwo research fields
with open('nwo-research-fields.json', 'r') as research_fields_file:
  nwo_data = json.load(research_fields_file)

# Load the data from the research domains
with open('researchDomain.json', 'r') as domains_file:
    domains_data = json.load(domains_file)

# Extract the "skos:prefLabel" values from the nwo data
nwo_field_labels = [entry['skos:prefLabel'] for entry in nwo_data['@graph'] if 'skos:prefLabel' in entry]

# Iterate through the "result" entries in domains_data
for result_entry in domains_data['result']:
    # Check if the "title" in the result entry exists in nwo_field_labels
    if result_entry['title'] in nwo_field_labels:
        # If there is an exact match, find the corresponding entry in nwo_data
        for entry in nwo_data['@graph']:
            if 'skos:prefLabel' in entry and entry['skos:prefLabel'] == result_entry['title']:
                
                # Update the entry with the "skos:exactMatch" field
                entry['skos:exactMatch'] = f"{result_entry['index']} {result_entry['title']}"

# Save the updated fields into a template file
with open('now-research-fields_template.json', 'w') as research_fields_file:
    json.dump(nwo_data, research_fields_file, indent=4)
