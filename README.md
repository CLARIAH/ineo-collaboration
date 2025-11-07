# ineo-collaboration
This project serves as a tool to gather, process, and synchronize metadata from different sources (tools codemeta, 
VLO datasets, SD Editor and so on) and Rich User Content (RUC) files.

The steps:
1. Harvesting datasets from different sources
2. Filter and process them based on review ratings and other criteria
3. Merging the data based on a template file
4. Synchronizing the processed data with the INEO platform via its API.

File structure:
- `utils/`: Utility functions for data processing and API interactions.
- `plugins/`: Contains source-specific harvesting and processing plugins.
- `config.yml`: Configuration file for the project.
- `main.py`: Main script to run the data processing and synchronization.
- `registry.py`: Registry for managing plugins.
- `step*_*.py`: Individual processing steps as modular scripts.
- `properties/`: Directory for property definitions and mappings. The contents should be fetched from NWO. It's a TODO. 
- `templates/`: Directory for template files used in data merging.

