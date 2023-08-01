import sys
import json
import FAIRdatasets_tools_harvester as harvester

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
with open("./ineo-content/grlc.json", "r") as json_file:
    ruc = json.load(json_file)[0]

debug("main",f"RUC contents of grlc: {ruc}")

res = traverse_data(template, ruc)

json.dump(res, sys.stdout, indent=2)

"""
# Rich User Contents
ruc = {
  "identifier": "grlc",
  "title": "grlc",
  "grlc": "grlc makes all your Linked Data accessible to the Web by automatically converting your SPARQL queries into RESTful APIs.",
  "Overview": "* grlc is a lightweight server that takes SPARQL queries (stored in a GitHub repository, in your local filesystem, or listed in a URL), and translates them to Linked Data Web APIs. This enables universal access to Linked Data. Users are not required to know SPARQL to query their data, but instead can access a web API.\n* grlc assumes that you have a collection of SPARQL queries as .rq files. grlc will create one API operation for each SPARQL query/.rq file in the collection.\n* Your queries can add API parameters to each operation by using the parameter mapping syntax. This allows your query to define query variables which will be mapped to API parameters for your API operation (see here for an example).\n* Your queries can include special decorators to add extra functionality to your API.",
  "Learn": "### Instruction webpages\n\n* The Quick Tutorial is a quick walkthrough for deploying your own Linked Data API using grlc.",
  "Mentions": "### Articles (incl. conference papers, presentations and demo\u2019s)\n\n* Albert Mero\u00f1o-Pe\u00f1uela, Rinke Hoekstra. \u201cgrlc Makes GitHub Taste Like Linked Data APIs\u201d. The Semantic Web \u2013 ESWC 2016 Satellite Events, Heraklion, Crete, Greece, May 29 \u2013 June 2, 2016, Revised Selected Papers. LNCS 9989, pp. 342-353 (2016). (PDF)\n* Albert Mero\u00f1o-Pe\u00f1uela, Rinke Hoekstra. \u201cSPARQL2Git: Transparent SPARQL and Linked Data API Curation via Git\u201d. In: Proceedings of the 14th Extended Semantic Web Conference (ESWC 2017), Poster and Demo Track. Portoroz, Slovenia, May 28th \u2013 June 1st, 2017 (2017). (PDF)\n* Albert Mero\u00f1o-Pe\u00f1uela, Rinke Hoekstra. \u201cAutomatic Query-centric API for Routine Access to Linked Data\u201d. In: The Semantic Web \u2013 ISWC 2017, 16th International Semantic Web Conference. Lecture Notes in Computer Science, vol 10587, pp. 334-339 (2017). (PDF)\n* Pasquale Lisena, Albert Mero\u00f1o-Pe\u00f1uela, Tobias Kuhn, Rapha\u00ebl Troncy. \u201cEasy Web API Development with SPARQL Transformer\u201d. In: The Semantic Web \u2013 ISWC 2019, 18th International Semantic Web Conference. Lecture Notes in Computer Science, vol 11779, pp. 454-470 (2019). (PDF)\n\n### Projects\n\n### Teaching and Instruction"
}

"""
"""

# DSL
with open("./template.json", 'r') as file:
    template = json.load(file)
result = traverse_data(template)
"""
