import re
import os
import sys
import glob
import json
import logging
from typing import Any, Dict

from plugins.bimap import BidirectionalMap
from utils.utils import get_logger
from urllib.parse import urlparse
from plugins.elasticsearch_manager import ElasticsearchSecurityManager

logger = get_logger(__name__, logging.INFO)

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    Elasticsearch = None
    helpers = None


property_path: str = "properties"
to_check = ["researchActivities", "researchDomains"]

def is_valid_url(url: str) -> bool:
    # Basic URL regex pattern
    pattern = re.compile(
        r'^(https?:\/\/)?'  # Optional HTTP or HTTPS scheme
        r'([\w\-]+\.)+'  # Subdomains and domain name
        r'[a-zA-Z]{2,}'  # Top-level domain
        r'(:\d+)?'  # Optional port
        r'(\/[^\s]*)?$'  # Optional path
    )

    if not re.match(pattern, url):
        return False

    # Additional validation using urllib.parse
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except ValueError:
        return False


def load_properties(path: str) -> dict:
    """
    Load properties from the specified path.
    create a dict per file with file name as the key and the content as the value
    The content will be a dict with the properties of the file

    :param path:
    :return: properties as dict
    """
    properties: Dict = {}
    bmap = BidirectionalMap()
    files = get_files_with_extension(path, ".json")
    for file in files:
        k = os.path.basename(file).split(".")[0]
        with open(file, 'r') as f:
            data = json.loads(f.read())
            if not isinstance(data, list):
                raise ValueError("Invalid data format. Expected list")
            for d in data:
                bmap.insert(d["title"], d["link"])
        properties[k] = bmap

    return properties



def processFile(file: str, manager: ElasticsearchSecurityManager, properties: Dict[str, BidirectionalMap], index_name: str):
    with open(file, 'r') as f:
        data = json.loads(f.read())[0].get("document")
    if data:
        for k in to_check:
            replace_values = data.get("properties").get(k)
            if replace_values:
                if isinstance(replace_values, list):
                    new_values = replace_values.copy()
                    for i in new_values:
                        if is_valid_url(i):
                            replace_values.remove(i)
                            replace_values.append(properties.get(k).get_by_value(i))
                else:
                    raise ValueError(f"Invalid data format for {k}. Expected list or string")

    # Update or create document based on document["id"]
    doc_id = data.get("id")
    if not doc_id:
        logger.warning(f"No 'id' field found in document from file {file}, skipping.")
        return

    # Search for existing document by document.id using keyword field for exact match
    query = {
        "query": {
            "term": {
                "document.id.keyword": doc_id
            }
        }
    }
    es = manager.client
    resp = es.search(index=index_name, body=query, size=1)
    hits = resp.get("hits", {}).get("hits", [])
    if hits:
        # Update existing document using internal _id
        internal_id = hits[0]["_id"]
        es.index(index=index_name, id=internal_id, document={"document": data})
        logger.info(f"Updated document with id={doc_id} (internal _id={internal_id}) in index '{index_name}'")
    else:
        # Create new document
        es.index(index=index_name, document={"document": data})
        logger.info(f"Created new document with id={doc_id} in index '{index_name}'")


def get_files_with_extension(folder, extension):
    """
    Get all files with the given extension from the specified folder.

    :param folder: The folder to search in.
    :param extension: The file extension to look for (e.g., '.json').
    :return: A list of file paths with the given extension.
    """
    search_pattern = os.path.join(folder, f"*{extension}")
    return glob.glob(search_pattern)


def processDir(data_path):
    files = get_files_with_extension(data_path, ".json")
    for file in files:
        processFile(file)

def ingest_ineo_records(name: str, config: dict[str, Any]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {json.dumps(config, indent=2)}")

    properties = load_properties(config.get("properties_path", "properties"))

    if Elasticsearch is None:
        logger.error("elasticsearch package is not installed. Please install it with 'pip install elasticsearch'.")
        return

    # Extract ES connection info
    es_scheme = config.get("elasticsearch_scheme", "http")
    es_host = config.get("elasticsearch_host", "localhost")
    es_port = config.get("elasticsearch_port", 9200)
    es_index = config.get("elasticsearch_index", "ineo")
    es_user = config.get("elasticsearch_username", None)
    es_pass = config.get("elasticsearch_password", None)
    use_auth = True if es_user and es_pass else False

    es_url = f"{es_scheme}://{es_host}:{es_port}"
    es_kwargs = {"hosts": [es_url]}
    if es_user and es_pass:
        es_kwargs["http_auth"] = (es_user, es_pass)

    try:
        manager = ElasticsearchSecurityManager(
            scheme=es_scheme,
            host=es_host,
            port=es_port,
            username=es_user,
            password=es_pass,
            verify_certs=False
        )
        # Test connection
        manager.client.search(index=es_index, size=0, body={"query": {"match_all": {}}})
        auth_status = "with authentication" if use_auth else "without authentication"
        logger.info(f"✓ Connected to Elasticsearch at {es_scheme}://{es_host}:{es_port} {auth_status}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Elasticsearch: {e}")
        logger.error(
            f"  Config: scheme={es_scheme}, host={es_host}, port={es_port}, auth={'enabled' if use_auth else 'disabled'}")
        sys.exit(1)

    datasets = config.get("datasets", {})
    if not datasets:
        logger.warning("No datasets defined in config. Nothing to ingest.")
        return

    for dataset_name, dataset_cfg in datasets.items():
        input_folder = dataset_cfg.get("input_folder")
        index_name = dataset_cfg.get("elasticsearch_index", es_index)
        if not input_folder:
            logger.warning(f"No input_folder for dataset {dataset_name}, skipping.")
            continue
        if not os.path.isdir(input_folder):
            logger.warning(f"Input folder {input_folder} does not exist for dataset {dataset_name}, skipping.")
            continue

        logger.info(f"Ingesting dataset '{dataset_name}' from {input_folder} into index '{index_name}'")
        files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
        if not files:
            logger.warning(f"No files found in {input_folder} for dataset {dataset_name}")
            continue

        logger.info(f"Ingesting {len(files)} documents into '{index_name}' from {input_folder}")
        for fname in files:
            try:
                fpath = os.path.join(input_folder, fname)
                processFile(fpath, manager, properties, es_index)
            except Exception as e:
                logger.error(f"Failed to ingest documents into '{index_name}': {e}")

    logger.info(f"### Finished {name}. ###")