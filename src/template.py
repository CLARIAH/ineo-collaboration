import sys
import json


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

def retrieve_info(info, ruc):
    res = None
    debug("retrieve_info",f"info[{info}]")
    info_values = info.split(",")
    for info_value in info_values:
        debug("retrieve_info",f"info_value[{info_value}]")
        if info_value.startswith("ruc"):
            debug("retrieve_info",f"Starting with 'ruc':{info_value}")
            template_key = info_value.split(":")[1].strip().lower()
            debug("retrieve_info",f"template_key[{template_key}]")
            info = resolve_path(ruc,template_key)
            if info is not None:
                debug("retrieve_info",f"The value of '{template_key}' in the RUC: {info}")
                res = info
                break  # Exit the loop once a match is found
     
        if info_value.startswith("md"):
            debug("retrieve_info",f"Starting with 'md':{info_value}")

        if info_value.startswith("err"):
            msg = info_value.split(":")[1].strip()
            
            # Print the error message to stderr
            error(None,f"{msg}")
 
        if info_value.startswith("null"): 
            debug("retrieve_info",f"Starting with 'null':{info_value}")
            res = "null" #there is no Null in python, None becomes null in json
    return res


# DSL template
template = [
    {
        "tabs": {
            "overview": {
                "body":"<ruc:tabs/overview/body/foo,md:query,err:there is no overview!,null"           
            }
        }
    }
]

# Rich User Contents
ruc = None
with open("./data/grlc.json", "r") as json_file:
    ruc = json.load(json_file)

debug("main",f"RUC contents of grlc: {ruc}")

res = traverse_data(template, ruc)

json.dump(res, sys.stdout, indent=2)


"""
# DSL
with open("./template.json", 'r') as file:
    template = json.load(file)
result = traverse_data(template)
"""
