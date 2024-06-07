import json
import os
from utils import get_logger, get_files, get_id_from_file_name

logger = get_logger(__name__, "reduce_id.log")

current_path = os.path.dirname(os.path.abspath(__file__))
input_path: str = f"{os.path.join(current_path, 'data', 'parsed_datasets')}"
id_limit: int = 128


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
            json_data["id"] = new_current_id
            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
            # Change the file name
            os.rename(filename, new_filename)
    if counter > 0:
        print(f"### {counter} files have id length > {id_limit}")
        logger.info(f"### {counter} files have id length > {id_limit}")


if __name__ == "__main__":
    reduce_id("processed_jsonfiles_datasets", 138)

