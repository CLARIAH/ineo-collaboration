import os
import re
import sys
import yaml
import json
import shutil
import logging
import subprocess
# local imports
from utils.utils import (get_logger, shorten_list_or_string,
                         title_limit, description_limit, more_characters,
                         get_files_with_postfix)

logger = get_logger(__name__, logging.INFO)


def extract_ruc(ruc_content) -> dict:
    """"
    Extracts Rich User Content (RUC) data from a markdown file.

    This function parses the input content string to extract metadata fields, descriptions, and sections,
    organizing them into a dictionary.

    Args:
        ruc_content: The content string containing RUC data in markdown from Github
    Returns:
        dict: A dictionary containing the extracted RUC data organized as metadata fields, descriptions,
              and sections.

    The function uses regular expressions to identify and extract different components of the RUC data, removing the markdown.
    including metadata fields enclosed between '---' lines, e.g.:
    ---
    identifier: Frog
    carousel:
        - /media/frog-logo.svg
        - /media/frog-output.png
        - /media/frog.gif
    group: Frog
    title: Frog
    ---
    descriptions with titles, e.g.:
    ---
    # Frog

    and content and headings under '##' headings, e.g.:
    ## Overview

    """
    logger.debug(f"Extracting Rich User Content from markdown content...\n{ruc_content}\n")
    re_fields = re.compile(r'^---(.*)---', flags=re.DOTALL)
    re_descriptions = re.compile(r'---\n+#(.*?)\n\n(.*?)\n\n##', flags=re.DOTALL)
    re_sections = re.compile(r'(?m)^(##\s+.*?)$(.*?)(?=^##\s|\Z)', flags=re.DOTALL | re.MULTILINE)
    re_name = re.compile(r'[^a-zA-Z]', flags=re.DOTALL)

    # Extract metadata fields enclosed between '---' lines.

    fields = re_fields.search(ruc_content).group(1)
    dictionary: dict = yaml.load(fields, Loader=yaml.SafeLoader)

    # Extract descriptions (e.g. ##Overview) from '##' headings
    descriptions = re.findall(re_descriptions, ruc_content)

    for description in descriptions:
        section_name = description[0].strip()
        section_content = description[1].strip()
        dictionary[section_name] = section_content

    # Extract sections (e.g., ##Mentions) from '##' sections
    sections = re.finditer(re_sections, ruc_content)

    for section in sections:
        section_name = section.group(1)
        section_name = re_name.sub("", section_name)
        section_content = section.group(2)
        dictionary[section_name] = section_content.strip()

    return dictionary


def sync_ruc(github_url, github_dir) -> None:
    """
    Retrieves Rich User Content of GiHub repository.
    """
    # store the current working directory
    if os.path.exists(github_dir):
        try:
            shutil.rmtree(github_dir)
        except Exception as e:
            logger.error(f"Error removing directory '{github_dir}': {e}")
            sys.exit(1)
    # Clone the repository
    subprocess.run(["git", "clone", github_url, github_dir])


def get_ruc_contents(github_url: str, github_dir: str, skip_files: list | None) -> dict:
    """
    This script synchronizes with the GitHub repository of ineo-content, extracts Rich User Content (RUC)
    and returns the RUC data in a dictionary.

    params:
        github_url (str): The URL of the GitHub repository to clone.
        github_dir (str): The local directory where the GitHub repository will be cloned.
        skip_files (list | None): A list of file paths to skip during processing.

    returns:
        dict: A dictionary containing the RUC data extracted from the markdown files.

    The 'extract_ruc' function is used to parse the RUC data from a given content string using regex.
    It extracts metadata fields, descriptions, and sections, returning them as a dictionary.
    """
    # Clone the GitHub repository
    sync_ruc(github_url, github_dir)

    fullpath_md = os.path.join(github_dir, "src")
    logger.info(f"Extracting Rich User Content from markdown files in '{fullpath_md}'...")
    all_ruc_contents = {}

    for filename in get_files_with_postfix(fullpath_md, postfix=".md", skip_files=skip_files):
        logger.info(f"Processing file: {filename}")
        with open(filename, 'r') as file:
            contents = file.read()
            ruc_contents: dict = extract_ruc(contents)
            logger.debug(f"Rich User Contents of {filename} is:\n{ruc_contents}\n")
            all_ruc_contents[filename] = ruc_contents

    # Check if the RUC filename is identical to the identifier and replace if not
    modified_contents = {}
    for filename, ruc_data in all_ruc_contents.items():
        identifier = ruc_data.get('identifier', '').lower()  # Get the lowercase identifier from the RUC dictionary
        filename_ruc = os.path.splitext(filename)[0].lower()
        if filename_ruc != identifier:
            logger.debug(f"Filename '{filename_ruc}' is not identical to the identifier '{identifier}'")
            logger.debug("Replacing the filename with the identifier...")
            modified_contents[identifier] = ruc_data
        else:
            modified_contents[filename] = ruc_data

    all_ruc_contents = modified_contents

    return all_ruc_contents


def serialize_ruc_to_json(ruc_contents_dict: dict, output_dir: str) -> None:
    """
    Serialize the RUC dictionary into JSON files.

    Args:
        ruc_contents_dict (dict): A dictionary containing RUC data
        output_dir (str): The directory where the RUC JSON files will be saved. Defaults to "./data".
    """
    if not os.path.exists(output_dir):
        logger.info(f"The output directory '{output_dir}' does not exist. Creating...")
        os.makedirs(output_dir)

    for filename, ruc_contents in ruc_contents_dict.items():
        json_file_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".json")
        org_title = ruc_contents.get("title", "")
        # shorten title and description
        ruc_contents["title"] = shorten_list_or_string(org_title, title_limit, more_characters)
        org_description = ruc_contents.get(org_title, None)
        if org_description is not None:
            if org_title == ruc_contents["title"]:
                # if the title is not shortened, use it as key to retrieve the description
                ruc_contents[org_title] = shorten_list_or_string(org_description, description_limit, more_characters)
            else:
                ruc_contents[ruc_contents["title"]] = shorten_list_or_string(org_description, description_limit,
                                                                             more_characters)
                _ = ruc_contents.pop(org_title)

        with open(json_file_path, "w") as json_file:
            json.dump(ruc_contents, json_file)


def harvest_ruc(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    github_url = params.get("github_url", None)
    github_dir = params.get("github_dir", None)
    ineo_ruc_path = params.get("ineo_ruc_path", None)
    skip_files = params.get("skip_files", None)

    ruc_data = get_ruc_contents(github_url, github_dir, skip_files)
    serialize_ruc_to_json(ruc_data, ineo_ruc_path)

    logger.info(f"### Finished {name}. ###")
