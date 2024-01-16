import sys
import json
import requests
import re
import pretty_errors
import jsonlines
import os

"""
This script is designed to process JSON data using a template and retrieve information based on a set of rules defined in the template. 
https://github.com/CLARIAH/clariah-plus/blob/main/requirements/software-metadata-requirements.md
"""

RUMBLEDB = "http://rumbledb:8001/jsoniq"
#RUMBLEDB = "http://localhost:8001/jsoniq"

# location of the JSONL file within container ineo-sync
JSONL_ineo = "./data/c3.jsonl"
JSONL_datasets_ineo = "/data/datasets.jsonl"

# location of the (same) JSONL file within container rumbledb
JSONL = "/data/c3.jsonl"
JSONL_datasets = "/data/datasets.jsonl"

PROCESSED_FILES = "./processed_jsonfiles"
TOOLS_TEMPLATE = "./template_tools.json"

# ID and TEMPLATE can be overridden by command-line arguments. Default value is "grlc"
ID = "grlc"
if len(sys.argv) > 1:
    ID = sys.argv[1]

if len(sys.argv) > 2:
    TOOLS_TEMPLATE = sys.argv[2]

# Debug and error handling functions
def debug(func, msg):
    print(f"?DBG:{func}:{msg}", file=sys.stderr)
    return None

def error(func, msg):
    if func is None:
        print(f"!ERR:{msg}", file=sys.stderr)
    else:
        print(f"!ERR:{func}:{msg}", file=sys.stderr)

def resolve_path(ruc, path):
    """
    Function to resolve a path within a nested dictionary. It splits the path into steps, and if a step starts with "$", 
    it looks for a matching key in the dictionary to access the nested values.
    """
    debug("resolve_path", f"path[{path}]")
    steps = path.split("/")
    step = steps[0]
    debug("resolve_path", f"step[{step}]")
    if step.startswith("$"):
        step = step.replace("$", "")
        ruc_key = step
        for key in ruc.keys():
            if key.lower() == step.lower():
                ruc_key = key
        step = ruc[ruc_key]
        debug("resolve_path", f"$step[{step}]")
    ruc_key = None
    for key in ruc.keys():
        debug("resolve_path", f"key[{key}]")
        if key.lower() == step.lower():
            ruc_key = key
            if len(steps) == 1:
                res = ruc[ruc_key]
                debug("resolve_path", f"res[{res}]")
                return res
            else:
                if isinstance(ruc[ruc_key], dict):
                    res = resolve_path(ruc[ruc_key], "/".join(steps[1:]))
                    debug("resolve_path", f"res[{res}]")
                    return res
                else:
                    debug("resolve_path", f"path is deeper, but dict not!")
                    return None


def traverse_data(template, ruc, rumbledb_jsonl_path):
    """
    This function traverses and processes the template. 
    
    value: type = 'str', value of the template.json (e.g. "<md:@queries/plangs.rq,null")
    key: type = 'str', key of the template.json (e.g. "programmingLanguages")
    info: type = 'str', extracted information after "<" if the value starts with "<" (e.g. "<md:@queries/plangs.rq,null" > md:@queries/plangs.rq,null) 
    """
    
    res = None

    # Check if the data is a dictionary
    if isinstance(template, dict):
        res = {}
        for key, value in template.items():
            # value is a string starting with <
            if isinstance(value, str) and value.startswith("<"):
                # Extract the information after the '<'
                info = value.split("<")[1]
                value = retrieve_info(info, ruc, rumbledb_jsonl_path)
            else:
                # dealing with nested dictionaries or lists
                value = traverse_data(value, ruc, rumbledb_jsonl_path)
            if value is not None:
                if value == "null":
                    res[key] = None
                else:
                    res[key] = value

    # If the data is a list
    elif isinstance(template, list):
        res = []
        for item in template:
            if isinstance(item, str) and item.startswith("<"):
                # Extract the information after the '<'
                info = item.split("<")[1]
                item = retrieve_info(info, ruc, rumbledb_jsonl_path)
            else:
                # dealing nested dictionaries or lists
                item = traverse_data(item, ruc, rumbledb_jsonl_path)
            if item is not None:
                if item == "null":
                    res.append(None)
                else:
                    res.append(item)
    return res
    
def checking_vocabs(value): 
    """
    This function is used to modify and standardize the query results of the research activities and domains (activities.rq and domains.rq) in order to be mapped against nwo-research-fields.json
    research domains: Some namespaces in "applicationCategory" in the codemeta files need to be expanded with the correct URL (e.g. nwo:ComputationalLinguisticsandPhilology > https://w3id.org/nwo-research-fields#ComputationalLinguisticsandPhilology)
    research domains: Some values in "applicationCategory in the codemeta files contain the correct URL with "w3id.org"
    research activities: Checking if the URL contains vocabs.dariah.eu in order to be mapped to nwo-research-fields.json. 

    value: type = 'str', the jsoniq query result of activities.rq or domains.rq. 
    
    """
    if "nwo" in value:
        return re.sub(r'^nwo:', 'https://w3id.org/nwo-research-fields#', value)
    elif "w3id.org" in value:
        return value
    elif "vocabs.dariah.eu" in value:
        debug("info", "The value contains 'vocabs.dariah.eu'")
        return value
    elif ">" in value:
        debug("info", "Value contains '>' and will be ignored")
        return None 
    else:
        return value

def process_vocabs(vocabs, vocab, val):
    """
    This function compares the links of the properties (e.g. mediaType) from INEO with the outcome of the jsoniq query on the codemeta files.
    To make the comparisons case-insensitive, both vocab links and val are converted to lowercase (or uppercase). 


    It merges the index number and title of the properties in the format {index + title} "7.23 plain"
    """
    
    # Check if the 'properties' key of e.g. MediaType is present in the properties
    if vocab in vocabs:
        # Iterate through the 'mediaTypes' list
        for item in vocabs[vocab]:
            # Check if val is present in the 'title'
            if val == item['title'].strip():
                # If there is a match, return index and title
                result = f"{item['index']} {val.strip()}"
                #vocabs_list.append(result)
                return result
                
            else:
                debug("process_vocabs", f"There is no match for {val}")

    
# global cache for vocabularies
vocabs = {}

def retrieve_info(info, ruc, rumbledb_jsonl_path) -> list | str | None:
    """
    
    This scripts parses and processes a set of input instructions from template.json (info, e.g. md:@queries/domains.rq:researchDomains,null) 
    The function returns the result of processing these instructions (res), which could be a list, a string, or None.
    
    The input instruction is further split using commas as delimiters (info_values), and different components of the instruction are processed. 
    This means that the order of the instruction is important: the loop is exited if a result is found. 
        
    The instructions in the template include:
        ruc: if an instruction starts with "ruc", it indicates that the function should extract information from the Rich User Contents
            - if it starts with "ruc", the instruction is further split using colons as delimiters (info_parts), and different components of the instruction are processed.
            - such a component can include a regular expression (e.g. "<ruc:overview:^.*(### Data.*) > "^.*(### Data.*)") which further transforms the extracted data.
        md: if an instruction starts with "md", it indicates that the function should retrieve information from the codemeta.json files, potentially using a jsoniq query. 
            the codemeta.json files are converted to a jsonl file that is stored in RumbleDB (done by script FAIRdatasets_tools_harvester.py)
            - if an instruction starts with "md" the info is further split into components. If a component start with "@" it indicates that there is a path to a file path containing a jsoniq query ("@queries/author.rq" > "queries/author.rq").
            - if is does not start with "@" (e.g. md:description > description) a query string is created. 
            - if a query is found, the function sends a POST request to RUMBLEDB with the query and processes and filters the response.
            - component "researchactivity" or "researchdomain" ("<md:@queries/activities.rq:researchActivity > researchActivity). Extra filter to further process the response of the jsoniq query (see functions "process_vocabs" and "checking_vocabs")
        api: if an instruction starts with "api", it sets the res variable to the string "create".
        err: if an instruction starts with "err", it indicates that an error message should be printed to the standard error stream (err:there is no learn!" > there is no learn!)
        null: if an instruction starts with "null", it sets the res variable to the string "null".

    info: type  = 'str', input instruction from template.json (information after "<" in def traverse_data, e.g. md:@queries/domains.rq:researchDomains)
    ruc: type = 'dict', Rich User Contents (from Github Repository ineo-content). The ruc is processed and created in script FAIRdatasets_tools_harvester.py.
    res: type = 'str' | 'list' | None, the function returns the value stored in the res variable, which represents the result of processing the instructions in the template.
    
    """
    # res is the final return value of the function
    res = None

    global vocabs

    debug("retrieve_info", f"info[{info}]")
    info_values = info.split(",") 
    for info_value in info_values:
        debug("retrieve_info", f"info_value[{info_value}]")
        if info_value.startswith("ruc"):
            info_parts = info_value.split(":")
            debug("retrieve_info", f"info_parts[{info_parts}]")

            if len(info_parts) >= 2:
                """
                get the contents of the key in the RUC and assign it to info
                """
                template_key = info_parts[1].strip().lower()
                if template_key.endswith("[]"):
                    template_key = template_key[:-2]

                info = resolve_path(ruc, template_key)
                debug(
                    "retrieve_info", f"The value of '{template_key}' in the RUC: {info}"
                )

            if info is not None and len(info_parts) > 2:
                regex_str = info_parts[2].strip()
                regex = re.compile(regex_str, flags=re.DOTALL)
                debug("retrieve_info", f"the regex string is: {regex_str}")
                if isinstance(info, list):
                    match = [
                        regex.search(item) if regex.search(item) is not None else item
                        for item in info
                    ]
                else:
                    match = regex.search(info)

                info: list | None = []
                if match is not None and isinstance(match, list):
                    for m in match:
                        if isinstance(m, str):
                            info.append(m)
                        else:
                            info.append(m.group(1))
                elif match is not None:
                    info.append(match.group(1))
                    debug("retrieve_info", f"The regex value of '{regex_str}': {info}")
                else:
                    info = None
                    debug("retrieve_info", f"The regex value of '{regex_str}': {info}")

            if info is not None and len(info_parts) > 3:
                template_key = info_parts[1].strip().lower()
                if template_key.endswith("[]"):
                    # in case of carousel
                    text: str = ":".join(info_parts[3:])
                    text: list = [
                        text.replace("$1", i)
                        if not (i.startswith("https://") or i.startswith("http://"))
                        else i
                        for i in info
                    ]
                else:
                    # in case of string
                    text: str = info_parts[3].strip()
                    # text is changing type here to list
                    text: str = text.replace("$1", info[0])

                info = text
                debug(
                    "retrieve_info",
                    f"The text value of '{info_parts[3].strip()}': {info}",
                )

            res = info
            if res is not None:
                break  # Exit the loop once a match is found
    
        # With the http request method POST, the INEO api can perform three operations: create, update and delete.
        # the default option is create. This will be further processed in ineo_sync.py
        if info_value.startswith("api"):
            res = "create"
        
        # Checking if the info_value string begins with "md" (e.g. "<md:@queries/activities.rq,null")
        # First check if the JSONL file of codemeta is not empty   
        if info_value.startswith("md"):
            info = None
            debug("retrieve_info", f"Starting with {info_value}")

            info_parts = info_value.split(":")
            debug("retrieve_info", f"info_parts[{info_parts}]")
            
            if len(info_parts) >= 2:
                path = info_parts[1]

                original_path = None
                if path.endswith("[]"):
                    original_path = path
                    path = path[:-2]  # Remove the '[]' suffix

                query = None
                # Checking if the path starts with "@" character. If it does, it indicates that the path refers to a file path containing a query.
                if path.startswith("@"):
                    # If the path starts with "@", this line extracts the file path by removing the "@" character. 
                    # For example, if path is "@queries/activities.rq", the path will be set to "queries/activities.rq". 
                    file = path[1:]
                    debug("path", f"path for the query[{file}]")
                    with open(file, "r") as file:
                        query = file.read()
                if query is not None:
                    query = query.replace("{JSONL}", rumbledb_jsonl_path)
                    query = query.replace("{ID}", ruc["identifier"])
                # This line generates a query string. It's a fallback query that is used when there is no external query file.
                else:
                    if "datasets" in rumbledb_jsonl_path:
                        query = f'for $i in json-file("{rumbledb_jsonl_path}",10) where $i.id eq "{ruc["identifier"]}" return $i.{path}'
                    else:
                        query = f'for $i in json-file("{rumbledb_jsonl_path}",10) where $i.identifier eq "{ruc["identifier"].lower()}" return $i.{path}'

                debug("retrieve_info", f"rumbledb query[{query}]")
                response = requests.post(RUMBLEDB, data=query)
                assert (
                    response.status_code == 200
                ), f"Error running {query} on rumbledb: {response.text}"

                # check whether the query run was successful
                resp = json.loads(response.text)
                if ("error-code" in resp) or ("error-message" in resp):
                    error(
                        "retrieve_info",
                        f"Error running {query} on rumbledb: {response.text}",
                    )
                    exit()

                if len(resp["values"]) > 0:
                    if original_path:
                        info = resp["values"]
                    else:
                        info = resp["values"][0]
                else:
                    info = None

            if info is not None and len(info_parts) > 2:
                vocab = info_parts[2].strip()
                debug("retrieve_info", f"filter on vocab[{vocab}]")
                
                if vocab not in vocabs.keys():
                    # Load the vocabs file to be used later
                    with open(f"/src/properties/{vocab}.json", "r") as vocabs_file:
                        vocabs[vocab] = json.load(vocabs_file)
                
                vocabs_list = []
                result_info = []
                
                for val in info:
                    checked_val = checking_vocabs(val)
                    debug(vocab, val) 
                    if checked_val is not None and checked_val.startswith("https://w3id.org/nwo-research-fields#"):
                        result_info.append(checked_val)
                        info = result_info 
                    else:
                        # Retrieve the index number of the title of the property for mapping to INEO. E.g. for MediaTypes that is 7.23 plain
                        info = process_vocabs(vocabs, vocab, val)
                        debug(
                            "retrieve_info",
                            f"The vocab value from '{info_parts[2].strip()}': {val}",
                            )
                        if info is not None:
                            vocabs_list.append(info)
                        if len(vocabs_list) > 0:
                            unique_list = list(set(vocabs_list))
                            info = unique_list
                        else:
                            info = None


            if info is not None:
                debug("retrieve_info", f"The value of '{path}' in the MD: {info}")

            res = info
            if res is not None:
                break  # Exit the loop once a match is found
    
        # This line checks if info_value starts with the prefix "err" ("<ruc:learn,err:there is no learn!")
        if info_value.startswith("err"):
            msg = info_value.split(":")[1].strip() # "there is no learn!"
            # Print the error message to stderr
            error(None, f"{msg}")

        # checks if info_value starts with the prefix "null" and indicates that the result should be set to "null".
        if info_value.startswith("null"):
            debug("retrieve_info", f"Starting with 'null':{info_value}")
            res = "null"

    return res


def create_minimal_ruc(current_id: str) -> dict:
    """
    Create a minimal RUC (Rich User Contents) object with default values.
    Used when there are no RUC files. 
    The title of the minimal RUC will be overwritten by the template.json (leading codemeta.jsonl)
    Current_id (str): The identifier of the c3 codemeta.jsonl
    """
    ruc = {
        "identifier": current_id,
        "title": current_id,
    }
    return ruc


def main(current_id: str = ID, template_path: str = TOOLS_TEMPLATE, rumbledb_jsonl_path: str = TOOLS_TEMPLATE):
    """
    Main function
    
    This script processes JSON data using a template (template.json) and retrieving information from it based on a set of instructions defined in template.py. 
    This function starts the process of traversing the template and retrieving the information from the Rich User Contents (RUC) and codemeta files (MD)
    then merge them into an INEO json file to ultimately feed into the INEO API. 

    template: type = 'dict', the template file loaded as json, by default it is always a list of dictionaries as INEO supports multiple records
    ruc: type = 'dict', the rich user contents file loaded as json, by default it is always a dictionary as it contains only one record
    res: type = 'list', the result of combining the RUC and the MD based on the instructions set out in template.py. 
    
    """
    
    # DSL template
    global template
    with open(template_path, "r") as file:
        template = json.load(file)

    # Rich User Contents
    ruc = None
    
    # Load RUC dictionary or create a minimal RUC object if not existent
    ruc_file_path = f"./data/rich_user_contents/{current_id}.json"
    if os.path.exists(ruc_file_path):
        with open(ruc_file_path, "r") as json_file:
            ruc = json.load(json_file)
        debug("main", f"RUC contents: {ruc}")
    else:
        ruc = create_minimal_ruc(current_id)

    # Combine codemeta/datasets and RUC using the template
    res = traverse_data(template, ruc, rumbledb_jsonl_path)
    
    # Create folders if they don't exist
    tools_folder = 'processed_jsonfiles_tools'
    datasets_folder = 'processed_jsonfiles_datasets'

    if not os.path.exists(tools_folder):
        os.makedirs(tools_folder)

    if not os.path.exists(datasets_folder):
        os.makedirs(datasets_folder)
    
    # Iterate through the results and save JSON files accordingly
    for result in res:
        resource_types = res[0].get('document', {}).get('properties', {}).get('resourceTypes', [])

        if "Tools" in resource_types:
            folder_name = tools_folder
        else:
            folder_name = datasets_folder

        filename = os.path.join(folder_name, f"{current_id}_processed.json")
        with open(filename, 'w') as file:
            json.dump(result, file, indent=2)

    print("JSON files saved successfully.")

if __name__ == "__main__":
    main()




    
   
    
   
