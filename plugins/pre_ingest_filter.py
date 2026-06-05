import json
import shutil
import logging
import sys
import os
from typing import Any

# Add parent directory to path to allow imports when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# local imports
from utils.utils import (get_logger, get_files_with_postfix, get_identifier)

logger = get_logger(__name__, logging.INFO)


def get_file_list(paths: dict) -> dict:
    """

    """
    all_files = {
        # identifier: [file_path, type]
    }
    for file_path in paths.keys():
        new_files = get_files_with_postfix(file_path, ".json")
        # Check each new file against its previous version
        for file in new_files:
            identifier = get_identifier(file, ["id", "identifier"])
            dataset_type = paths[file_path]
            all_files[identifier] = (file, dataset_type)
    return all_files



def pre_ingest_filter(name: str, params: dict[str, Any]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    datasets = params.get("datasets", None)
    for dataset_type, dataset_config in datasets.items():
        input_dir = dataset_config.get("input_folder", None)
        output_dir = dataset_config.get("output_folder", None)
        if input_dir is None or output_dir is None:
            logger.warning(f"Dataset {dataset_type} is missing input_folder or output_folder.")
            continue
        # Ensure the output directory exists
        shutil.os.makedirs(output_dir, exist_ok=True)

        # Get all files in the input directory
        all_files = get_files_with_postfix(input_dir, ".json")
        logger.info(f"Found {len(all_files)} files in {input_dir} for dataset {dataset_type}.")
        # Here you can add any filtering logic you want to apply to the files before moving them to the output directory. For example, you could filter by file size, modification date
        # For now, we'll move the files without link field, or link is empty, to the output directory
        for file in all_files:
            # Check if the file has a link field and if it's empty
            data = None
            with open(file, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {file}: {e}")
                    continue
            if data:
                document = data[0].get("document", {})
            else:
                logger.warning(f"No data found in {file}. Skipping.")
                continue
            link = document.get("properties", {}).get("link", None)
            if link is None or link == "":
                # Move the file to the output directory
                shutil.move(file, output_dir)
                logger.info(f"Moved {file} to {output_dir}.")

        logger.info(f"Finished pre ingest filtering for {dataset_type}.")
    logger.info(f"### Finished {name}. ###")

if __name__ == "__main__":
    # Example usage from config.yml
    params = {
        "datasets": {
            "tools_metadata": {
                "input_folder": "./data/processed_tools_metadata",
                "output_folder": "./data/processed_filtered_out_tools_metadata"
            },
            "parsed_datasets": {
                "input_folder": "./data/processed_parsed_datasets",
                "output_folder": "./data/processed_filtered_out_parsed_datasets"
            }
        }
    }
    pre_ingest_filter("pre_ingest_filter", params)