import sys
import json
import requests
import re
import pretty_errors
import jsonlines

RUMBLEDB = "http://rumbledb:8001/jsoniq"
# RUMBLEDB = "http://localhost:8001/jsoniq"
JSONL = "/data/data/codemeta.jsonl"

ID = "grlc"
if len(sys.argv) > 1:
    ID = sys.argv[1]

TEMPLATE = "./template.json"
if len(sys.argv) > 2:
    TEMPLATE = sys.argv[2]


def debug(func, msg):
    print(f"?DBG:{func}:{msg}", file=sys.stderr)
    return None


def error(func, msg):
    if func is None:
        print(f"!ERR:{msg}", file=sys.stderr)
    else:
        print(f"!ERR:{func}:{msg}", file=sys.stderr)


def resolve_path(ruc, path):
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


def traverse_data(data, ruc):
    res = None

    # Check if the data is a dictionary
    if isinstance(data, dict):
        res = {}
        for key, value in data.items():
            # value is a string starting with <
            if isinstance(value, str) and value.startswith("<"):
                # Extract the information after the '<'
                info = value.split("<")[1]
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
            if isinstance(item, str) and item.startswith("<"):
                # Extract the information after the '<'
                info = item.split("<")[1]
                item = retrieve_info(info, ruc)
            else:
                # dealing nested dictionaries or lists
                item = traverse_data(item, ruc)
            if item is not None:
                if item == "null":
                    res.append(None)
                else:
                    res.append(item)
    return res


def check_links(links):
    if isinstance(links, str):
        # If 'links' is a single URL in vocabs
        if "vocabs.dariah.eu" in links:
            debug("info", "The link contains 'vocabs.dariah.eu'")
            return True
        else:
            debug("info", "The link does not contain 'vocabs.dariah.eu'")
            return False
    elif isinstance(links, list):
        # If 'links' is a list of strings
        matching_links = [link for link in links if "vocabs.dariah.eu" in link]
        if matching_links:
            debug("info", "Multiple links contain 'vocabs.dariah.eu'")
            return True
        else:
            debug("info", "None of the links in the API contain 'vocabs.dariah.eu'")
            return False
    else:
        debug(
            "info",
            "Invalid input. 'links' should be either a string or a list of strings",
        )
        return False


def retrieve_info(info, ruc) -> list | str | None:
    """
    TODO: put some documentation here **with** examples preferably

    docstring
    info: [type], [description]
    ruc: [type], [description]

    return: [type], [description]
    """
    # res is the final return value of the function
    res = None

    # Load the vocabs file to be used later for research activity
    with open(f"./vocabs/researchActivity.json", "r") as vocabs_file:
        vocabs = json.load(vocabs_file)

    debug("retrieve_info", f"info[{info}]")
    info_values = info.split(",")
    for info_value in info_values:
        debug("retrieve_info", f"info_value[{info_value}]")
        if info_value.startswith("ruc"):
            info_parts = info_value.split(":")
            debug("retrieve_info", f"info_parts[{info_parts}]")

            if len(info_parts) >= 2:
                """
                get the content of the key in the RUC and assign it to info
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

        if info_value.startswith("md"):
            info = None
            debug("retrieve_info", f"Starting with {info_value}")
            path = info_value.split(":")[1].strip()

            original_path = None
            if path.endswith("[]"):
                original_path = path
                path = path[:-2]  # Remove the '[]' suffix

            query = None
            if path.startswith("@"):
                file = path[1:]
                debug("path", f"path for the query[{file}]")
                with open(file, "r") as file:
                    query = file.read()
            if query is not None:
                query = query.replace("{JSONL}", JSONL)
                query = query.replace("{ID}", ruc["identifier"].lower())
            else:
                query = f'for $i in json-file("{JSONL}",10) where $i.identifier eq "{ruc["identifier"].lower()}" return $i.{path}'

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

            if info is not None:
                debug("retrieve_info", f"The value of '{path}' in the MD: {info}")

                # Check if info contains "vocabs.dariah.eu"
                vocabs_list = []
                for item in info:
                    if check_links(item):
                        debug("research activity", item)
                        # Iterate through the items in the "result" array of the vocabs
                        for vocabs_item in vocabs.get("result", []):
                            if vocabs_item.get("link") == item:
                                title = vocabs_item.get("title")
                                index = vocabs_item.get("index")
                                result = f"{index} {title}"
                                vocabs_list.append(result)
                                debug("vocabs", f"vocabs index and title':{result}")

                """
                TODO: fix this tricky code below
                It is now checking whether vocabs_list is empty or not to determine 
                whether it is the generic use case or use case of Research Activity
                Better solution would be getting the key value from the template, i.e, if keyvalue == "researchActivity": ...
                """
                if len(vocabs_list) > 0:
                    info = vocabs_list

            debug("final result", info)

            res = info
            break  # Exit the loop once a match is found

        if info_value.startswith("err"):
            msg = info_value.split(":")[1].strip()
            # Print the error message to stderr
            error(None, f"{msg}")

        if info_value.startswith("null"):
            debug("retrieve_info", f"Starting with 'null':{info_value}")
            res = "null"

    return res


def main():
    """
    Main function
    This function starts the process of traversing the template and retrieving the information from the RUC and MD
    then merge then info an INEO json file for feeding into INEO API

    TEMPLATE: the template file loaded as json, by default it is always a list of dictionaries as INEO supports multiple records
    RUC: the rich user contents file loaded as json, by default it is always a dictionary as it contains only one record

    return: None
    """
    # DSL
    with open(TEMPLATE, "r") as file:
        template = json.load(file)

    # Rich User Contents
    ruc = None
    with open(f"./data/{ID}.json", "r") as json_file:
        ruc = json.load(json_file)

    debug("main", f"RUC contents of grlc: {ruc}")

    res = traverse_data(template, ruc)

    json.dump(res, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
