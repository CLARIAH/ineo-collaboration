import sys
import json
import requests
import re 

#RUMBLEDB = "http://rumbledb:8001/jsoniq"
RUMBLEDB = "http://localhost:8001/jsoniq"
JSONL = "/data/codemeta.jsonl"

ID="grlc"
if len(sys.argv) > 1:
    ID = sys.argv[1]


def debug(func,msg):
    print(f"?DBG:{func}:{msg}", file=sys.stderr)
    return None

def error(func,msg):
    if func is None:
        print(f"!ERR:{msg}", file=sys.stderr)
    else:
        print(f"!ERR:{func}:{msg}", file=sys.stderr)

def resolve_path(ruc, path):
    debug("resolve_path",f"path[{path}]")
    steps = path.split("/")
    step = steps[0]
    ruc_key = None 
    for key in ruc.keys():
        debug("resolve_path",f"key[{key}]")
        if key.lower() == step:
            ruc_key = key
            if len(steps) == 1:
                return ruc[ruc_key]
            else:
                if isinstance(ruc[ruc_key],dict):
                    return resolve_path(ruc[ruc_key],'/'.join(steps[1:]))
                else:
                    debug("resolve_path",f"path is deeper, but dict not!")
                    return None


def traverse_data(data, ruc):

    res = None
    
    # Check if the data is a dictionary
    if isinstance(data, dict):
        res = {}
        for key, value in data.items():
            # value is a string starting with <
            if isinstance(value, str) and value.startswith('<'):
                # Extract the information after the '<'
                info = value.split('<')[1]  
                value = retrieve_info(info, ruc)
            else:
              # dealing with nested dictionaries or lists
              value = traverse_data(value, ruc)
            if value is not None:
                if value == "null":
                    res[key] = None
                else:
                    res[key] = value
    
    # If the data is a list
    elif isinstance(data, list):
        res = []
        for item in data:
            if isinstance(item, str) and item.startswith('<'):
                # Extract the information after the '<'
                info = item.split('<')[1]  
                item = retrieve_info(info,ruc)
            else:
              # dealing nested dictionaries or lists
              item = traverse_data(item, ruc)
            if item is not None:
                if item == "null":
                    res.append(None)
                else:
                    res.append(item)
    return res

#TODO: "### Overview\n* from the API
def retrieve_info(info, ruc):
    res = None
    debug("retrieve_info",f"info[{info}]")
    info_values = info.split(",")
    for info_value in info_values:
        debug("retrieve_info",f"info_value[{info_value}]")
        if info_value.startswith("ruc"):
            info_parts = info_value.split(":")
            debug("retrieve_info",f"info_parts[{info_parts}]")
        
            if len(info_parts) >= 2:
                template_key = info_parts[1].strip().lower()
                info = resolve_path(ruc, template_key)
                debug("retrieve_info", f"The value of '{template_key}' in the RUC: {info}")    

            if info is not None and len(info_parts) > 2:
                regex_str = info_parts[2].strip()
                regex = re.compile(regex_str, flags=re.DOTALL)
                debug("retrieve_info",f"the regex string is: {regex_str}")
                match = regex.search(info)
                
                if match is not None:
                    info = match.group(1)
                    debug("retrieve_info", f"The regex value of '{regex_str}': {info}")
                else:
                    info = None
                    debug("retrieve_info", f"The regex value of '{regex_str}': {info}")

            if info is not None and len(info_parts) > 3:
                text = info_parts[3].strip()
                text = text.replace("$1",info)  
                info = text
                debug("retrieve_info", f"The text value of '{info_parts[3].strip()}': {info}")
                
            res = info
            if res is not None:
                break  # Exit the loop once a match is found

        if info_value.startswith("md"):
            info is None
            debug("retrieve_info",f"Starting with 'md':{info_value}")
            path = info_value.split(":")[1].strip()
            query = f"for $i in json-file(\"{JSONL}\",10) where $i.identifier eq \"{ruc['identifier']}\" return $i.{path}"
            debug("retrieve_info",f"rumbledb query[{query}]")
            response = requests.post(RUMBLEDB, data = query)
            debug("retrieve_info",f"rumbledb result[{response.text}]")
            resp = json.loads(response.text)
            if len(resp['values']) > 0 :
                info = resp['values'][0]
            if info is not None:
                debug("retrieve_info",f"The value of '{path}' in the MD: {info}")
                res = info
                break  # Exit the loop once a match is found

        if info_value.startswith("err"):
            msg = info_value.split(":")[1].strip()
            # Print the error message to stderr
            error(None,f"{msg}")
 
        if info_value.startswith("null"): 
            debug("retrieve_info",f"Starting with 'null':{info_value}")
            res = "null" 
    
    return res

# DSL
with open("./template.json", 'r') as file:
    template = json.load(file)

# Rich User Contents
ruc = None
with open(f"./data/{ID}.json", "r") as json_file:
    ruc = json.load(json_file)

debug("main",f"RUC contents of grlc: {ruc}")

res = traverse_data(template, ruc)

json.dump(res, sys.stdout, indent=2)


