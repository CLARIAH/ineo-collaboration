import json
import os
from utils import get_logger, get_files, get_id_from_file_name

logger = get_logger(__name__, "reduce_id.log")

current_path = os.path.dirname(os.path.abspath(__file__))
input_path: str = f"{os.path.join(current_path, 'data', 'parsed_datasets')}"
id_limit: int = 128

id_field_path: dict = {
    "parsed_datasets": "id",
    "processed_jsonfiles_datasets": [0, "document", "id"],
    0: "test"
}


def get_id_field(id_obj: list | dict, path: list | str) -> dict:
    """
    This function gets the id field from the id_obj using the path

    id_obj (list | dict): The object to get the id field from
    path (list | str): The path to the id field
    return: The id field object
    """
    # when id_obj is a list, the path[0] should be an integer
    if not (isinstance(id_obj, list) and isinstance(path, list) and isinstance(path[0], int)):
        raise Exception(f"Invalid id_obj: {id_obj} or path: {path}")
    if isinstance(path, str):
        return id_obj[path]
    if isinstance(path, list):
        if len(path) == 1:
            return id_obj[path[0]]
        return get_id_field(id_obj[path[0]], path[1:])
    raise Exception(f"Invalid path: {path} or invalid id_obj: {id_obj}")


def reduce_id(input_path: str = input_path, id_limit: int = id_limit):
    """
    This function reduces the id length of the files in the input path and change its file name accordingly

    input_path (str): The path of the files to be checked
    id_limit (int): The limit of the id length

    return: None
    """
    files = get_files(input_path)
    print(f"### checking length of {len(files)} files in {input_path} ###")
    logger.info(f"### checking length of {len(files)} files in {input_path} ###")
    counter: int = 0
    for filename in files:
        # print(f"### checking {filename} ###")
        current_id: str = get_id_from_file_name(filename)
        if len(current_id) > id_limit:
            counter += 1
            print(f"\n\n### {filename} has id length {len(current_id)} > {id_limit}")
            logger.info(f"\n\n### {filename} has id length {len(current_id)} > {id_limit}")
            dir_name = os.path.dirname(filename)
            # new id is the last 128 characters of the current id
            new_current_id = current_id[-id_limit:]
            new_filename = os.path.join(dir_name, f"{new_current_id}.json")
            logger.debug(f"{new_current_id}")
            logger.debug(f"{new_filename=}")
            # get content and replace id with new id
            with open(filename, "r") as f:
                json_data = json.loads(f.read())
            if "parsed_datasets" in input_path:
                json_data["id"] = new_current_id
            elif "processed_jsonfiles_datasets" in input_path:
                json_data[0]["document"]["id"] = new_current_id
            else:
                raise ValueError("Invalid input path")

            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
            # Change the file name
            os.rename(filename, new_filename)
    if counter > 0:
        print(f"### {counter} files have id length > {id_limit}")
        logger.info(f"### {counter} files have id length > {id_limit}")


if __name__ == "__main__":
    reduce_id("processed_jsonfiles_datasets")
    # test = get_id_field([{"document": {"id": "1234"}}], [0, "document", "id"])
    # print(f"{test=}")
