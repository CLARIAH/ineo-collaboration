import FAIRdatasets_tools_harvester as harvester

do_download: bool = False
do_compare: bool = True

# init db and check if the table exists
conn = harvester.init_check_db(db_file_name="tools_metadata.db", table_name="tools_metadata")
if conn is None:
    print("Error in creating the database connection!")
    exit(1)
c = conn.cursor()

# doing tests
save_directory: str = "test_dir"
if do_download:
    harvester.download_json_files(save_directory)

files = harvester.get_files(save_directory)

previous_timestamp = c.execute("SELECT * FROM tools_metadata ORDER BY timestamp DESC LIMIT 1").fetchone()[2]
has_previous_batch = True if previous_timestamp else False
print(f"has_previous_batch: {has_previous_batch}")
print(f"previous_timestamp: {previous_timestamp}")

if do_compare:
    previous_batch = harvester.get_previous_batch(previous_timestamp=previous_timestamp)
    print(f"previous_batch: {previous_batch}, there are {len(previous_batch)} entries")

    
