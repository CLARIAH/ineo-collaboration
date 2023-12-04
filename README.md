# ineo-collaboration
This project serves as a tool to gather, process, and synchronize Codemeta and Rich User Content (RUC) files with an external API called [INEO](https://www.ineo.tools/). 


## Overview

This repository comprises six scripts responsible for different functionalities:

### Scripts Overview
- main.py: The main script orchestrating the program's workflow.
- harvester.py: Handles harvesting of data from codemeta and rich user contents (RUC)
- rating.py: Filters codemeta reviewRatings using a RumbleDB database. 
- template.py: Designed to process JSON data from codemeta and RUC using a template and retrieves information based on a set of rules defined in that template. Creates a json file to be fed into INEO.
- ineo_get_properties.py: Fetches properties data from the INEO API and saves the JSON response to local files. 
- ineo_sync.py: Responsible for synchronization tasks related to INEO, such as creating new resources, updating existing resources and deleting inactive resources. 

#### harvester.py
The harvester.py script serves as a tool to gather, process, and synchronize Codemeta and Rich User Content (RUC) files. It's designed to streamline data collection, manage databases, and generate JSONlines files for efficient integration with the INEO platform. It performs the following tasks:

Data Harvesting: Downloads Codemeta (software metadata from all of the [sources](https://github.com/CLARIAH/clariah-plus/blob/main/requirements/software-metadata-requirements.md) within CLARIAH, which is harvested automatically, and periodically, by [a harvesting
tool](https://github.com/proycon/codemeta-harvester)) and RUC files from a [Github repository](https://github.com/CLARIAH/ineo-content).

Database Management: Maintains a SQLite database to track timestamps and changes with MD5 hashes. Only the files that have changed end up in a JSONlines file (codemeta.jsonl)
File Comparison: Compares current and previous batches to identify file changes.
JSONlines Generation: Converts gathered codemeta data into a JSONlines format (codemeta.jsonl) for further processing with a RumbleDB database. If the JSONL file is empty, there might be no updates to feed into INEO.
Inactive Tool Tracking: Identifies inactive tools based on absence counts over 3 runs in a database. 

#### rating.py
This script (rating.py) encompasses functions for querying RumbleDB, filtering codemeta IDs based on reviewratings (in our case resources with a reviewRating > 3 will be fed into INEO), and managing the processing of a JSONlines file (c3.jsonl). The c3.jsonl file consists of (changed) codemeta (consisting of tools with a reviewRating of > 3) and rich user contents files. 

#### ineo_get_properties.py
This script interacts with an API to fetch various properties data and store the JSON responses. The properties include tadirah vocabularies (https://vocabs.dariah.eu/tadirah/analyzing) and NWO research fields (https://w3id.org/nwo-research-fields#ComputersAndTheHumanities) to map against the researchdomains and researchactivites retrieved from the codemeta files. 

#### template.py
This script, template.py, is a crucial component of the program that plays a pivotal role in merging data from Rich User Contents (RUC) and codemeta files (MD) based on a provided template file (template.json). The template follows a Domain-Specific Language (DSL) to define how the information should be processed and retrieved. The DSL can define queries to a RumbleDB database 
that retrieves values from the codemeta. Ultimately, the script merges the retrieved values from the RUC and codemeta into an INEO JSON file (processed_jsonfiles) to be used with the INEO API. 

#### ineo_sync.py
This script syncs data with an external [INEO API](https://github.com/CLARIAH/ineo-collaboration/tree/main/doc). It operates on the processed jsonfiles, determining actions for each document (create, update, delete) based on their existence and properties. It also checks whether the researchDomains and researchActivities in the processed templates matches the ones in INEO.

## Setup
This project utilizes Docker for containerization and includes two services: ineo-sync and rumbledb. You can start docker (assuming you use docker and are in the src directory of the source code) using:

``
docker compose up -d
``

To access the ineo-sync container and interact with it, run:

``
docker exec -it ineo-sync /bin/bash
``

Execute main.py to initiate the workflow. 

``
python main.py
``

