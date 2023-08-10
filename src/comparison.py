import os
import json

API_DIRECTORY = "./api"
#CODEMETA_DIRECTORY = "./data/tools_metadata"

# Load the json files of the INEO API, transforming them in a dictionary
def load_json_files(directory):
    count = 0
    json_files = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            count += 1
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                data = json.load(file)
                json_files[filename] = data
    return count, json_files

count, dictionaries = load_json_files(API_DIRECTORY)
#count, dictionaries = load_json_files(CODEMETA_DIRECTORY)

# Collect all unique keys found in the properties sections
merged_properties_keys = set()

# Collect values for each properties" key from all INEO dictionaries
values_by_key = {}

# Access each INEO dictionary 
for filename, data in dictionaries.items():
    if isinstance(data, list):
        for id, dictionary in enumerate(data):
            if "properties" in dictionary:
                properties_data = dictionary["properties"]
                properties_data_count = len(properties_data)
                #print(f"\nProperties data for {filename}:\n{json.dumps(properties_data, indent=4)}\n")
                print(f"There are {properties_data_count} properties keys for {filename}: \n{list(properties_data.keys())}\n")
                merged_properties_keys.update(properties_data.keys()) 
    
                # Iterate through each dictionary and its properties
                for key, value in properties_data.items():
                    if key not in values_by_key:
                        values_by_key[key] = []
                    values_by_key[key].append((filename, value))
    else:
        merged_properties_keys.update(data.keys())
    
# Print the unique properties keys
unique_properties_count = len(merged_properties_keys)
print(f"There are {unique_properties_count} unique properties keys in {count} dictionaries:")
print(list(merged_properties_keys))

# Print all the values for each properties key
for key, values in values_by_key.items():
    print(f"\n{key}:")
    for filename, value in values:
        # Get the type of the properties value
        value_type = type(value).__name__
        
        print(f" - {filename.replace('.json', '')}: {json.dumps(value, indent=4)} (Type: {value_type})")

