import harvester
import template
import ineo_sync
import logging
import json
import os


jsonl_file: str = "./data/codemeta.jsonl"

def call_harvester():
    harvester.main()
    logging.info("Harvester called")


def get_ids_from_jsonl(jsonl_file: str = jsonl_file) -> list[str]:
    all_ids: list[str] = []
    line_count = 0
    with open(jsonl_file, "r") as f:
        for line in f:
            line_count += 1
            json_line = json.loads(line)
            assert "identifier" in json_line, f"identifier not found in {json_line}"
            all_ids.append(json_line["identifier"])
    print("Number of codemeta tools in the jsonl file:", line_count)
    return all_ids

def call_template():
    missing_ruc = 0 
    for current_id in get_ids_from_jsonl():
        path = "./data" 
        file_name = f"{current_id}.json"
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            print(f"Combining both RUC and CM of {file_name} for the INEO api...")
            template.main(current_id)
        else:
            #print(f"The RUC of {file_name} does not exist in the directory.")
            missing_ruc += 1
    print(f"Number of missing RUCs: {missing_ruc}")


# TODO: call ineo_sync
def call_ineo_sync():
    ineo_sync.main()


if "__main__" == __name__:
    # TODO: call_harvester() needs more work to handle new RUC without codemeta as well as how to get new RUC only
    call_harvester()
    call_template()
    #call_ineo_sync()
    logging.info("All done")