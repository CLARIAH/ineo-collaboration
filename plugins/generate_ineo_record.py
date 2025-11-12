import os
import re
import json
import logging
import concurrent.futures
from tqdm import tqdm
# local imports
from utils.utils import get_logger, get_redis_key, call_basex_with_query

logger = get_logger(__name__, logging.INFO)

# global cache for vocabularies
vocabs = {}


def process_vocabs(vocabs, vocab, val):
    """
    This function compares the links of the properties (e.g. mediaType, status ) from INEO with the outcome of the jsoniq query on the codemeta files.
    To make the comparisons case-insensitive, both vocab links and val are converted to lowercase (or uppercase).

    !Further processing of the research domains and research activities (checking against INEO with lowercase spellingvariations) happens in ineo-sync.py!

    It merges the index number and title of the properties in the format {index + title} "7.23 plain"
    """

    # Check if the 'properties' key of e.g. MediaType is present in the properties
    if vocab in vocabs:
        # Iterate through the 'mediaTypes' list
        for item in vocabs[vocab]:
            # Check if val is present in the 'title'
            if val.lower() == item['title'].strip().lower():
                # If there is a match, return index and title (if the index is null (e.g. by status properties) return only the title)
                if item['index'] is not None:
                    result = f"{item['index']} {item['title'].strip()}"
                else:
                    result = f"{item['title'].strip()}"

                # vocabs_list.append(result)
                return result
        else:
            logger.debug(f"There is no match for {val}")


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


def get_ruc_file(ruc_path: str, identifier: str, ruc_postfix: str = "json") -> str | dict:
    # Construct the RUC file path based on the identifier
    ruc_file_path = f"{ruc_path}/{identifier}.{ruc_postfix}"
    try:
        with open(ruc_file_path, 'r', encoding='utf-8') as fh:
            if ruc_postfix == "json":
                ruc_content = json.load(fh)
            else:
                ruc_content = fh.read()
        logger.debug(f"Loaded RUC file for identifier {identifier} from {ruc_file_path}")
        return ruc_content
    except:
        ruc_content = create_minimal_ruc(identifier)
        logger.debug(f"Loaded minimal RUC for identifier: {identifier}")
        return ruc_content


def checking_vocabs(value):
    """
    This function is used to modify and standardize the query results of the research activities and domains (activities.rq and domains.rq) in order to be mapped against nwo-research-fields.json
    research domains: Some namespaces in "applicationCategory" in the codemeta files need to be expanded with the correct URL (e.g. nwo:ComputationalLinguisticsandPhilology > https://w3id.org/nwo-research-fields#ComputationalLinguisticsandPhilology)
    research domains: Some values in "applicationCategory in the codemeta files contain the correct URL with "w3id.org"
    research activities: Checking if the URL contains vocabs.dariah.eu in order to be mapped to nwo-research-fields.json.

    !Further processing of the research domains and activities (checking against INEO with lowercase spellingvariations) happens in ineo-sync.py!
    value: type = 'str', the jsoniq query result of activities.rq or domains.rq.

    """
    if "nwo" in value:
        return re.sub(r'^nwo:', 'https://w3id.org/nwo-research-fields#', value)
    elif "w3id.org" in value:
        return value
    elif "vocabs.dariah.eu" in value:
        logger.debug("The value contains 'vocabs.dariah.eu'")
        return value
    elif ">" in value:
        logger.debug("Value contains '>' and will be ignored")
        return None
    else:
        return value


def resolve_path(ruc, path):
    """
    Function to resolve a path within a nested dictionary. It splits the path into steps, and if a step starts with "$",
    it looks for a matching key in the dictionary to access the nested values.
    """
    logger.debug(f"path[{path}]")
    steps = path.split("/")
    step = steps[0]
    logger.debug(f"step[{step}]")
    if step.startswith("$"):
        step = step.replace("$", "")
        ruc_key = step
        for key in ruc.keys():
            if key.lower() == step.lower():
                ruc_key = key
        step = ruc[ruc_key]
        logger.debug(f"$step[{step}]")
    ruc_key = None
    for key in ruc.keys():
        logger.debug(f"key[{key}]")
        if key.lower() == step.lower():
            ruc_key = key
            if len(steps) == 1:
                res = ruc[ruc_key]
                logger.debug(f"res[{res}]")
                return res
            else:
                if isinstance(ruc[ruc_key], dict):
                    res = resolve_path(ruc[ruc_key], "/".join(steps[1:]))
                    logger.debug(f"res[{res}]")
                    return res
                else:
                    logger.debug(f"path is deeper, but dict not!")
                    return None


def retrieve_info(info, ruc, template_type: str, current_id: str, basex_info: dict, properties_path: str) -> list | str | None | str:
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

    basex_protocol: str | None = basex_info.get("basex_protocol", None)
    basex_host: str | None = basex_info.get("basex_host", None)
    basex_port: str | None = basex_info.get("basex_port", None)
    basex_user: str | None = basex_info.get("basex_user", None)
    basex_password: str | None = basex_info.get("basex_password", None)
    basex_table: str | None = basex_info.get("basex_table", None)

    if (basex_protocol is None or
            basex_host is None or
            basex_port is None or
            basex_user is None or
            basex_password is None or
            basex_table is None):
        raise ValueError("Missing BaseX connection information in basex_info")

    logger.debug(f"info[{info}]")
    info_values = info.split(",")
    for info_value in info_values:
        logger.debug(f"info_value[{info_value}]")
        if info_value.startswith("ruc"):
            info_parts = info_value.split(":")
            logger.debug(f"info_parts[{info_parts}]")

            if len(info_parts) >= 2:
                """
                get the contents of the key in the RUC and assign it to info
                """
                template_key = info_parts[1].strip().lower()
                if template_key.endswith("[]"):
                    template_key = template_key[:-2]

                info = resolve_path(ruc, template_key)
                logger.debug(f"The value of '{template_key}' in the RUC: {info}")

            if info is not None and len(info_parts) > 2:
                regex_str = info_parts[2].strip()
                regex = re.compile(regex_str, flags=re.DOTALL)
                logger.debug(f"the regex string is: {regex_str}")
                if isinstance(info, list):
                    match = [
                        regex.search(item) if regex.search(item) is not None else item
                        for item in info
                    ]
                else:
                    match = regex.search(info)

                info: list | str | None = []
                if match is not None and isinstance(match, list):
                    for m in match:
                        if isinstance(m, str):
                            info.append(m)
                        else:
                            info.append(m.group(1))
                elif match is not None:
                    logger.debug(f"The regex value of '{regex_str}': {info}")
                    info = match.group(1)
                else:
                    logger.debug(f"The regex value of '{regex_str}': {info}")
                    info = None

            org_info = info
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
                    text: str = text.replace("$1", info)

                info = text
                logger.debug(f"The text value of '{info_parts[3].strip()}': {info}")

            res = info
            if res is not None:
                break  # Exit the loop once a match is found

        # With the http request method POST, the INEO api can perform three operations: create, update and delete.
        # the default option is create. This will be further processed in ineo_sync.py
        if info_value.startswith("api"):
            res = "create"

        # The default values is defined in the template after the column
        if info_value.startswith("default"):
            logger.debug(f"Starting with {info_value}")
            info_parts = info_value.split(":")
            logger.debug(f"info_parts[{info_parts}]")

            res = info_parts[1]

        # Checking if the info_value string begins with "md" (e.g. "<md:@queries/activities.rq,null")
        # First check if the JSONL file of codemeta is not empty
        if info_value.startswith("md"):
            info = None
            logger.debug(f"Starting with {info_value}")

            info_parts = info_value.split(":")
            logger.debug(f"info_parts[{info_parts}]")

            if len(info_parts) >= 2:
                path = info_parts[1]

                original_path = None
                if path.endswith("[]"):
                    original_path = path
                    path = path[:-2]  # Remove the '[]' suffix

                query = None
                file = None
                # Checking if the path starts with "@" character. If it does, it indicates that the path refers to a file path containing a query.
                if path.startswith("@"):
                    # If the path starts with "@", this line extracts the file path by removing the "@" character.
                    # For example, if path is "@queries/activities.rq", the path will be set to "queries/activities.rq".
                    file = path[1:]
                    logger.debug(f"path for the query[{file}]")
                    with open(file, "r") as file:
                        query = file.read()
                if query is not None:
                    # query = query.replace("{JSONL}", rumbledb_jsonl_path)
                    query = query.replace("{ID}", current_id)
                # This line generates a query string. It's a fallback query that is used when there is no external query file.
                else:
                    if "datasets" == template_type:
                        query = f"""
                        declare namespace js="http://www.w3.org/2005/xpath-functions";

                        for $i in js:map
                        let $ID:="{current_id}"
                         where $i/js:string[@key='id']=$ID
                         return xml-to-json($i/js:*[@key='{path}'][1])
                        """.format(current_id=current_id, path=path)
                        # query = f'for $i in json-file("{rumbledb_jsonl_path}",10) where $i.id eq "{current_id}" return $i.{path}'
                    elif "tools" == template_type:
                        query = f"""
                        declare namespace js="http://www.w3.org/2005/xpath-functions";

                        for $i in js:map
                        let $ID:="{current_id}"
                         where $i/js:string[@key='identifier']=$ID
                         return xml-to-json($i/js:*[@key='{path}'][1])
                        """.format(current_id=current_id, path=path)
                    else:
                        raise TypeError(
                            f"Invalid template type {template_type}; Valid types are 'datasets' and 'tools'")
                        # query = f'for $i in json-file("{rumbledb_jsonl_path}",10) where $i.identifier eq "{current_id}" return $i.{path}'

                logger.debug(f"basex query[{query}]")

                dbname = "datasets" if "datasets" == template_type else "tools"

                # timing the query call
                response = call_basex_with_query(query,
                                                 basex_protocol,
                                                 basex_host,
                                                 int(basex_port),
                                                 basex_user,
                                                 basex_password,
                                                 "post",
                                                 basex_table
                                                 )
                assert (
                        response.status_code == 200
                ), f"HttpError {response.status_code} Error running {query} on basex: {response.text}"

                # check whether the query run was successful
                try:
                    if response.text is not None and len(response.text) > 0:
                        resp = json.loads(response.text)
                    else:
                        resp = None
                except json.JSONDecodeError:
                    # resp = "" + response.text
                    logger.error(f"Error running {query} on basex: {response.text}")
                    raise

                if resp is not None and len(resp) > 0:
                    if isinstance(resp, str) or isinstance(resp, list):
                        info = resp
                    else:
                        raise TypeError(f"Invalid response type {type(resp)}. Allowed types are list and str.")
                else:
                    info = None

            if info is not None and len(info_parts) > 2:
                vocab = info_parts[2].strip()
                logger.debug(f"filter on vocab[{vocab}]")

                if vocab not in vocabs.keys():
                    # Load the vocabs file to be used later
                    # with open(f"/src/properties/{vocab}.json", "r") as vocabs_file:
                    with open(os.path.join(properties_path, f"{vocab}.json"), "r") as vocabs_file:
                        vocabs[vocab] = json.load(vocabs_file)

                vocabs_list = []
                result_info = []

                for val in info:
                    checked_val = checking_vocabs(val)
                    logger.debug(vocab, val)
                    try:
                        if checked_val is not None and checked_val.startswith("https://w3id.org/nwo-research-fields#"):
                            result_info.append(checked_val)
                            info = result_info
                        else:
                            # Retrieve the index number of the title of the property for mapping to INEO. E.g. for MediaTypes that is 7.23 plain
                            info = process_vocabs(vocabs, vocab, val)
                            logger.debug(f"The vocab value from '{info_parts[2].strip()}': {val}")
                            if info is not None:
                                vocabs_list.append(info)
                            if len(vocabs_list) > 0:
                                unique_list = list(set(vocabs_list))
                                info = unique_list
                            else:
                                info = None
                    except Exception as ex:
                        logger.error(f"Error processing vocabs {info_parts} - {val}: {ex}")
                        exit("error found")

            if info is not None:
                logger.debug(f"The value of '{path}' in the MD: {info}")

            res = info
            if res is not None:
                break  # Exit the loop once a match is found

        # This line checks if info_value starts with the prefix "err" ("<ruc:learn,err:there is no learn!")
        if info_value.startswith("err"):
            msg = info_value.split(":")[1].strip()  # "there is no learn!"
            # Print the error message to stderr
            logger.debug(f"error message given by template.json: [{msg}]")

        # checks if info_value starts with the prefix "null" and indicates that the result should be set to "null".
        if info_value.startswith("null"):
            logger.debug(f"Starting with 'null':{info_value}")
            # TODO FIXME: replace string "null" with None to check whether it is working
            res = None

    return res


def traverse_data(template, ruc, template_type: str, current_id: str, basex_info: dict, properties_path: str) -> list | dict | None:
    """
    This function traverses and processes the template.

    value: type = 'str', value of the template.json (e.g. "<md:@queries/plangs.rq,null")
    key: type = 'str', key of the template.json (e.g. "programmingLanguages")
    info: type = 'str', extracted information after "<" if the value starts with "<" (e.g. "<md:@queries/plangs.rq,null" > md:@queries/plangs.rq,null)
    """

    logger.debug(f"{template}, {type(template)}, {ruc=}, {template_type=}, {current_id=}")
    res = None

    # Check if the data is a dictionary
    if isinstance(template, dict):
        res = {}
        for key, value in template.items():
            # value is a string starting with <
            if isinstance(value, str) and value.startswith("<"):
                # Extract the information after the '<'
                info = value.split("<")[1]
                value = retrieve_info(info, ruc, template_type, current_id, basex_info, properties_path)
            else:
                # dealing with nested dictionaries or lists
                value = traverse_data(value, ruc, template_type, current_id, basex_info, properties_path)
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
                item = retrieve_info(info, ruc, template_type, current_id, basex_info, properties_path)
            else:
                # dealing nested dictionaries or lists
                item = traverse_data(item, ruc, template_type, current_id, basex_info, properties_path)
            if item is not None:
                if item == "null":
                    res.append(None)
                else:
                    res.append(item)
    return res


def create_output_folder(datasets: dict[str, dict[str, str]]) -> None:
    for dataset_type, dataset_info in datasets.items():
        output_folder = dataset_info.get("output_folder", None)
        if output_folder is not None:
            os.makedirs(output_folder, exist_ok=True)
            logger.info(f"Created output folder: {output_folder}")
        else:
            logger.error(f"No output folder specified for dataset type: {dataset_type}")
            raise ValueError(f"No output folder specified for dataset type: {dataset_type}")


def process_record(args):
    k, v, datasets, ruc_path, basex_protocol, basex_host, basex_port, basex_user, basex_password, properties_path = args
    identifier = k
    current_file, current_file_type = v
    current_template_path = datasets.get(current_file_type).get("template_path")
    current_output_folder = datasets.get(current_file_type).get("output_folder")
    current_basex_table = datasets.get(current_file_type).get("basex_table")

    with open(current_template_path, 'r', encoding='utf-8') as fh:
        current_template_file = json.load(fh)

    logger.debug(f"Template file: {current_template_path}")
    logger.debug(f"Output folder: {current_output_folder}")
    logger.debug(f"BaseX table: {current_basex_table}")
    logger.debug(f"Processing file for identifier: {identifier}, Type: {current_file_type}, Path: {current_file}")

    ruc_file = get_ruc_file(ruc_path, identifier)

    res = traverse_data(
        current_template_file,
        ruc_file,
        current_basex_table,
        identifier,
        {
            "basex_protocol": basex_protocol,
            "basex_host": basex_host,
            "basex_port": basex_port,
            "basex_user": basex_user,
            "basex_password": basex_password,
            "basex_table": current_basex_table
        },
        properties_path
    )

    processed_results = []
    for result in res:
        processed_results.append(result)

    filename = os.path.join(current_output_folder, f"{identifier}_processed.json")
    with open(filename, 'w') as file:
        json.dump(processed_results, file, indent=2)

# single thread version
def generate_ineo_record(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    redis_host = params.get("redis_host", None)
    redis_port = params.get("redis_port", None)
    redis_db = params.get("redis_db", None)
    redis_key = params.get("redis_key", None)
    basex_protocol = params.get("basex_protocol", None)
    basex_host = params.get("basex_host", None)
    basex_port = params.get("basex_port", None)
    basex_user = params.get("basex_user", None)
    basex_password = params.get("basex_password", None)
    ruc_path = params.get("ruc_path", None)
    properties_path = params.get("properties_path", None)
    datasets = params.get("datasets", {})

    updated_files = get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)
    logger.info(f"Fetched {len(updated_files)} updated files from Redis.")

    counters = {}
    for identifier, file_info in list(updated_files.items()):
        if len(file_info) == 2:
            file_path = file_info[0]
            file_type = file_info[1]
        else:
            logger.warning(f"Unexpected file info format for {identifier}: {file_info}")
            continue

        if file_type not in counters:
            counters[file_type] = 1
        else:
            counters[file_type] += 1

    logger.info(f"Records to update: {json.dumps(counters, indent=2)}")

    logger.info(f"Creating output folder")
    create_output_folder(datasets)

    args_list = [
        (k, v, datasets, ruc_path, basex_protocol, basex_host, basex_port, basex_user, basex_password, properties_path)
        for k, v in updated_files.items()
    ]
    for args in tqdm(args_list, total=len(args_list)):
        process_record(args)

    logger.info(f"### Finished {name}. ###")


# multi processing version
# def generate_ineo_record(name: str, params: dict[str, str]) -> None:
#     logger.info(f"### Starting {name}... ###")
#     logger.info(f"Parameters: {json.dumps(params, indent=2)}")
#
#     redis_host = params.get("redis_host", None)
#     redis_port = params.get("redis_port", None)
#     redis_db = params.get("redis_db", None)
#     redis_key = params.get("redis_key", None)
#     basex_protocol = params.get("basex_protocol", None)
#     basex_host = params.get("basex_host", None)
#     basex_port = params.get("basex_port", None)
#     basex_user = params.get("basex_user", None)
#     basex_password = params.get("basex_password", None)
#     ruc_path = params.get("ruc_path", None)
#     properties_path = params.get("properties_path", None)
#     datasets = params.get("datasets", {})
#
#     updated_files = get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)
#     logger.info(f"Fetched {len(updated_files)} updated files from Redis.")
#
#     counters = {}
#     for identifier, file_info in list(updated_files.items()):
#         if len(file_info) == 2:
#             file_path = file_info[0]
#             file_type = file_info[1]
#         else:
#             logger.warning(f"Unexpected file info format for {identifier}: {file_info}")
#             continue
#
#         if file_type not in counters:
#             counters[file_type] = 1
#         else:
#             counters[file_type] += 1
#
#     logger.info(f"Records to update: {json.dumps(counters, indent=2)}")
#
#     logger.info(f"Creating output folder")
#     create_output_folder(datasets)
#
#     with concurrent.futures.ProcessPoolExecutor() as executor:
#         args_list = [
#             (k, v, datasets, ruc_path, basex_protocol, basex_host, basex_port, basex_user, basex_password,
#              properties_path)
#             for k, v in updated_files.items()
#         ]
#         list(tqdm(executor.map(process_record, args_list), total=len(args_list)))
#
#     logger.info(f"### Finished {name}. ###")


# multi threading version
# def generate_ineo_record(name: str, params: dict[str, str]) -> None:
#     logger.info(f"### Starting {name}... ###")
#     # logger.info(f"Parameters: {params}")
#     logger.info(f"Parameters: {json.dumps(params, indent=2)}")
#
#     redis_host = params.get("redis_host", None)
#     redis_port = params.get("redis_port", None)
#     redis_db = params.get("redis_db", None)
#     redis_key = params.get("redis_key", None)
#     basex_protocol = params.get("basex_protocol", None)
#     basex_host = params.get("basex_host", None)
#     basex_port = params.get("basex_port", None)
#     basex_user = params.get("basex_user", None)
#     basex_password = params.get("basex_password", None)
#     ruc_path = params.get("ruc_path", None)
#     properties_path = params.get("properties_path", None)
#     datasets = params.get("datasets", {})
#
#     # Fetch updated files from Redis
#     updated_files = get_redis_key(redis_host, int(redis_port), int(redis_db), redis_key)
#     logger.info(f"Fetched {len(updated_files)} updated files from Redis.")
#
#     counters = {}
#     for identifier, file_info in list(updated_files.items()):
#         if len(file_info) == 2:
#             file_path = file_info[0]
#             file_type = file_info[1]
#         else:
#             logger.warning(f"Unexpected file info format for {identifier}: {file_info}")
#             continue
#
#         if file_type not in counters:
#             counters[file_type] = 1
#         else:
#             counters[file_type] += 1
#
#     logger.info(f"Records to update: {json.dumps(counters, indent=2)}")
#
#     logger.info(f"Creating output folder")
#     create_output_folder(datasets)
#
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         args_list = [
#             (k, v, datasets, ruc_path, basex_protocol, basex_host, basex_port, basex_user, basex_password,
#              properties_path)
#             for k, v in updated_files.items()
#         ]
#         list(tqdm(executor.map(process_record, args_list), total=len(args_list)))
#
#     logger.info(f"### Finished {name}. ###")
