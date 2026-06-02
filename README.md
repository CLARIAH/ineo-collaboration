# ineo-collaboration

This project serves as a tool to gather, process, and synchronize metadata from different sources (tools codemeta,
VLO datasets, SD Editor and so on) and Rich User Content (RUC) files.

### Current version

`0.8` is the current version of the scripts and Docker image.
For example, the docker image is labeled as `registry.diginfra.net/tsd/ineo-sync:0.8`.

### File structure:

- `utils/`: Utility functions for data processing and API interactions.
- `plugins/`: Contains source-specific harvesting and processing plugins.
- `config.yml`: Configuration file for the project.
- `main.py`: Main script to run the data processing and synchronization.
- `registry.py`: Registry for managing plugins.
- `step*_*.py`: Individual processing steps as modular scripts.
- `properties/`: Directory for property definitions and mappings. The contents should be fetched from [url place](url). It's a TODO.
- `templates/`: Directory for template files used in data merging.
- `dsqueries/`: Directory containing basex queries for generating INEO record from datasets.
- `queries/`: Directory containing basex queries for generating INEO record from tools_metadata files.

### Prerequisites

- `docker compose up -d` to start the required services (e.g., basex, redis)

### How to build and run

1. `docker build -t ineo-sync .` to build the Docker image for current architecture.
2. `docker buildx build --platform linux/amd64,linux/arm64 -t ineo-sync:latest --push .` to build and push
   multi-architecture image.
3. `docker exec -it ineo-sync uv run main.py` to run the container with the configuration file.

### Configuration examples

```yaml
pipeline:
  - name: "Harvest VLO Data"
    description: "Harvest data from VLO"
    plugin: harvest_vlo
    config:
      base_query: "*:*"
      solr_url: "http://vlo-solr:8983/solr/vlo-index"
      solr_username: ""
      solr_password: ""
      output_folder: "./data/parsed_datasets"
      backup_directory: "./data/parsed_datasets_backup"
      proxies:
        http: "socks5://localhost:9999"
  - name: "Harvest codemeta"
    description: "Harvest codemeta"
    plugin: harvest_codemeta
    config:
      url: "https://tools.clariah.nl/files/"
      output_path_data: "./data/tools_metadata"
      backup_directory: "./data/tools_metadata_backup"
  - name: "Harvest RUC"
    description: "Harvest RUC"
    plugin: harvest_ruc
    config:
      github_url: "https://github.com/CLARIAH/ineo-content.git"
      github_dir: "./data/github-ineo-content"
      ineo_ruc_path: "./data/rich_user_contents"
      backup_directory: "./data/rich_user_contents_backup"
      skip_files:
        - "./data/github-ineo-content/src/index.md"
  - name: "Init basex server"
    description: "init basex server"
    plugin: init_basex
    config:
      basex_protocol: "http"
      basex_host: "localhost"
      basex_port: 8082
      basex_user: "admin"
      basex_password: "pass"
      tables:
        - name: tools
          folder: "/data/tools_metadata"
        - name: datasets
          folder: "/data/parsed_datasets"
  - name: "Fetch property"
    description: "Dummy placeholder for fetch property plugin, properties are existing files, should be fetched in the future"
    plugin: fetch_property
    config: { }
  - name: "Get updated files"
    description: "Get and store IDs and file paths of updated files in Redis"
    plugin: get_updated_files
    config:
      redis_host: "localhost"
      redis_port: 6379
      redis_db: 0
      data_types:
        - name: tools_metadata
          new_files_path: "./data/tools_metadata"
          previous_files_path: "./data/tools_metadata_backup"
          redis_key: "updated_datasets"
          remove_key_before_update: true
        - name: parsed_datasets
          new_files_path: "./data/parsed_datasets"
          previous_files_path: "./data/parsed_datasets_backup"
          redis_key: "updated_datasets"
          remove_key_before_update: false
        - name: rich_user_contents
          new_files_path: "./data/rich_user_contents"
          previous_files_path: "./data/rich_user_contents_backup"
          redis_key: "updated_rich_user_contents"
          merge_with: "updated_datasets"
          remove_key_before_update: true
  - name: "Get updated RUC"
    description: "Merge updated RUC info into updated datasets in Redis"
    plugin: get_updated_ruc
    config:
      redis_host: "localhost"
      redis_port: 6379
      redis_db: 0
      to_merge:
        redis_key: "updated_rich_user_contents"
        merge_with: "updated_datasets"
      files_path: # path -> type mapping
        "./data/tools_metadata": tools_metadata
        "./data/parsed_datasets": parsed_datasets
  - name: "Generate INEO record"
    description: "Generate INEO record based on updated files"
    plugin: generate_ineo_record
    config:
      redis_host: "localhost"
      redis_port: 6379
      redis_db: 0
      redis_key: "updated_datasets"
      basex_protocol: "http"
      basex_host: "localhost"
      basex_port: 8082
      basex_user: "admin"
      basex_password: "pass"
      ruc_path: "./data/rich_user_contents"
      properties_path: "./properties"
      datasets:
        tools_metadata:
          basex_table: "tools"
          template_path: "./templates/template_tools.json"
          output_folder: "./data/processed_tools_metadata"
        parsed_datasets:
          basex_table: "datasets"
          template_path: "./templates/template_datasets.json"
          output_folder: "./data/processed_parsed_datasets"
  - name: "Cleanup Redis"
    description: "Cleanup Redis keys used during the pipeline"
    plugin: cleanup_redis
    config:
      redis_host: "localhost"
      redis_port: 6379
      redis_db: 0
      keys_to_delete:
        - "updated_datasets"
        - "updated_rich_user_contents"

```
