import sys
import httpx
import logging
# local imports
from utils.utils import get_logger, call_basex, test_basex_connection

logger = get_logger(__name__, logging.INFO)


def prepare_basex_tables(
        protocol: str,
        table_name: str,
                         folder: str,
                         host: str = "basex",
                         port: int = 8080,
                         user: str = "admin",
                         password: str = "pass",
                         action: str = "post") -> None:
    """
    This function prepares the basex tables for the tools and datasets

    table_name (str): The name of the table to be created
    folder (str): The folder containing the json files to be inserted into the basex table

    return (None)
    """
    content_type: str = "application/xml"

    content = """
    <query>
        <text><![CDATA[
    import module namespace db = "http://basex.org/modules/db";

    db:create(
      "{table_name}",
      "{folder}",
      (),
      map {{
        "createfilter": "*.json",
        "parser": "json",
        "jsonparser": "format=basic,liberal=yes,encoding=UTF-8"
      }}
    )
    ]]></text>
    </query>
    """.format(table_name=table_name, folder=folder)

    # Create the basex table
    response = call_basex(protocol, content, host, port, user, password, action, content_type=content_type)
    if 199 < response.status_code < 300:
        logger.info(f"Basex table {table_name} created with folder {folder} ...")
    else:
        logger.error(f"Failed to create the basex table {table_name} with folder {folder} ...")
        logger.error(f"Response: {response.text}")
        raise Exception(f"Failed to create the basex table {table_name} with folder {folder} ...")


def init_basex(name: str, params: dict[str, str]) -> None:
    logger.info(f"### Starting {name}... ###")
    logger.info(f"Parameters: {params}")

    basex_protocol: str = params.get("basex_protocol", "http")
    basex_host: str = params.get("basex_host", "basex")
    basex_port: int = int(params.get("basex_port", 8080))
    basex_user: str = params.get("basex_user", None)
    basex_password: str = params.get("basex_password", None)
    tables = params.get("tables", None)

    connection_test = test_basex_connection(basex_protocol, basex_host, basex_port, basex_user, basex_password)
    if not connection_test:
        logger.error(f"Failed to connect to BaseX server. ")
        sys.exit(1)
    else:
        logger.info(f"Successfully connected to BaseX server at {basex_host}:{basex_port}.")

    logger.info(f"Working on {len(tables)} tables.")
    logger.debug(f"Working on {len(tables)} tables: {tables}")
    for table in tables:
        table_name = table.get("name", None)
        table_folder = table.get("folder", None)
        logger.info(f"Preparing table {table_name} with folder {table_folder} ...")
        prepare_basex_tables(basex_protocol, table_name, table_folder, basex_host, basex_port, basex_user, basex_password)

    logger.info(f"### Finished {name}. ###")