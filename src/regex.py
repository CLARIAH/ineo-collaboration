import re
import yaml
import sys

ID="grlc"
if len(sys.argv) > 1:
    ID = sys.argv[1]

re_fields = re.compile(r'^---(.*)---', flags=re.DOTALL)
re_descriptions = re.compile(r'---\n+#(.*?)\n\n(.*?)\n\n##', flags=re.DOTALL)
re_sections = re.compile(r'(?m)^(##\s+.*?)$(.*?)(?=^##\s|\Z)', flags=re.DOTALL | re.MULTILINE)
re_name = re.compile(r'[^a-zA-Z]', flags=re.DOTALL)

def extract_ruc(ruc_content):
    dictionary = {}
    fields = re_fields.search(ruc_content).group(1)
    dictionary = yaml.load(fields, Loader=yaml.SafeLoader)

    descriptions = re.findall(re_descriptions, ruc_content)
    
    for description in descriptions:
        section_name = description[0].strip()
        section_content = description[1].strip()
        dictionary[section_name] = section_content
    
    sections = re.finditer(re_sections, ruc_content)
    
    for section in sections:
        section_name = section.group(1)
        section_name = re_name.sub("", section_name)
        section_content = section.group(2)
        dictionary[section_name] = section_content.strip()
    
    return dictionary

"""
# Read the content from the Rich User Content file
with open(f"./ineo-content/src/tools/{ID}.md", 'r') as file:
    mdfile = file.read()

# Extract the information and create the dictionary
ruc_contents = extract_ruc(mdfile)

print(f"{ID} Rich User Contents: ", ruc_contents)
"""