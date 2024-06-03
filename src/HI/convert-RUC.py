import os
import sys
import re
import yaml
import json
import logging
from typing import AnyStr

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from utils import get_logger, get_files

log_file_path = 'convert-RUC.log'
logger = get_logger(log_file_path, __name__, level=logging.ERROR)

data_folder = f"{os.path.join(parent_dir, 'ineo-content', 'src', 'data')}"  # '/Users/menzowi/Documents/Projects/CLARIAH/INEO/ineo-content/src/data'
print(f"data_folder: {data_folder}")


def extract_ruc(ruc_content: AnyStr) -> dict:
    """"
    Extracts Rich User Content (RUC) data from a markdown file. 

    This function parses the input content string to extract metadata fields, descriptions, and sections,
    organizing them into a dictionary.

    Args:
        ruc_content (AnyStr): The content string containing RUC data in markdown from Github
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
    re_fields = re.compile(r'^---(.*)---', flags=re.DOTALL)
    re_descriptions = re.compile(r'---\n+#(.*?)\n(.*?)\n\n##', flags=re.DOTALL)
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


if __name__ == '__main__':
    all_files: list = get_files(folder_name=data_folder, file_postfix='md')
    for full_path in all_files:
        print(f"### Processing {full_path}")
        file_path = os.path.dirname(full_path)
        file_name = os.path.basename(full_path).split('.')[0]
        logger.info(f"{file_path=}, {file_name=}")
        with open(full_path, 'r') as file:
            contents = file.read()
            ruc_contents: dict = extract_ruc(contents)
            with open(f"{file_path}/{file_name}.json", 'w') as json_file:
                json.dump(ruc_contents, json_file, indent=2)
