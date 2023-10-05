import harvester
import template
import ineo_sync
import logging
import json


jsonl_file: str = "/data/codemeta.jsonl"


def call_harvester():
    # TODO: call harvester
    harvester.main()
    logging.info("Harvester called")


def get_ids_from_jsonl(jsonl_file: str = jsonl_file) -> list[str]:
    all_ids: list[str] = []
    with open(jsonl_file, "r") as f:
        for line in f:
            json_line = json.loads(line)
            assert "identifier" in json_line, f"identifier not found in {json_line}"
            all_ids.append(json_line["identifier"])
    return all_ids


def call_template():
    # TODO: call template
    for current_id in get_ids_from_jsonl():
        template.main(current_id)


# TODO: call ineo_sync
def call_ineo_sync():
    ineo_sync.main()


if "__main__" == __name__:
    # TODO: call_harvester() needs more work to handle new RUC without codemeta as well as how to get new RUC only
    call_harvester()
    call_template()
    # TODO: test ineo_sync, code should be in ineoPost.py???
    call_ineo_sync()
    logging.info("All done")