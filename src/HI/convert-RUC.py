import yaml
import re
import os
from typing import List, Optional, AnyStr, Union, Dict
import logging
from utils import get_logger, get_files
import json

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

log_file_path = 'convert-RUC.log'
logger = get_logger(log_file_path, __name__, level=logging.ERROR)

folder_path = '/Users/menzowi/Documents/Projects/CLARIAH/INEO/ineo-content/src/data'

if __name__ == '__main__':
    for filename in os.listdir(folder_path):
            print(f"record[{filename}]")
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                contents: AnyStr = file.read()
                ruc_contents: dict = extract_ruc(contents)
                print(f"Rich User Contents of {file_path} is:\n{json.dumps(ruc_contents)}\n")