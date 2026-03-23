import json
import logging
import os
from typing import Any, Dict

from utils.utils import get_logger

logger = get_logger(__name__, logging.INFO)

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    Elasticsearch = None
    helpers = None

def ingest_ineo_records(name: str, config: dict[str, Any]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {json.dumps(config, indent=2)}")

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

    es_url = f"{es_scheme}://{es_host}:{es_port}"
    es_kwargs = {"hosts": [es_url]}
    if es_user and es_pass:
        es_kwargs["http_auth"] = (es_user, es_pass)

    try:
        es = Elasticsearch(**es_kwargs)
        if not es.ping():
            logger.error(f"Could not connect to Elasticsearch at {es_url}")
            return
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return

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

        actions = []
        for fname in files:
            fpath = os.path.join(input_folder, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                # If the file contains a list of records with 'operation' and 'document', use document['id'] as _id
                if isinstance(doc, list):
                    for d in doc:
                        if (
                            isinstance(d, dict)
                            and d.get("operation")
                            and isinstance(d.get("document"), dict)
                            and d["document"].get("id")
                        ):
                            actions.append({
                                "_index": index_name,
                                "_id": d["document"]["id"],
                                "_source": d["document"]
                            })
                        else:
                            # fallback: index as is
                            actions.append({"_index": index_name, "_source": d})
                elif (
                    isinstance(doc, dict)
                    and doc.get("operation")
                    and isinstance(doc.get("document"), dict)
                    and doc["document"].get("id")
                ):
                    actions.append({
                        "_index": index_name,
                        "_id": doc["document"]["id"],
                        "_source": doc["document"]
                    })
                else:
                    actions.append({"_index": index_name, "_source": doc})
            except Exception as e:
                logger.error(f"Failed to read or parse {fpath}: {e}")

        if actions:
            try:
                helpers.bulk(es, actions)
                logger.info(f"Ingested {len(actions)} documents into '{index_name}' from {input_folder}")
            except Exception as e:
                logger.error(f"Failed to ingest documents into '{index_name}': {e}")
        else:
            logger.warning(f"No valid documents to ingest for dataset {dataset_name}")

    logger.info(f"### Finished {name}. ###")