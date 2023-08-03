import re
import yaml

re_fields = re.compile(r'^---(.*)---', flags=re.DOTALL)
# re_split = re.compile(r'^(.*):(\s(.*)$|$)')
re_descriptions = re.compile(r'---\n#(.*?)\n\n(.*?)\n\n##', flags=re.DOTALL)
re_sections = re.compile(r'(?m)^(##\s+.*?)$(.*?)(?=^##\s|\Z)', flags=re.DOTALL | re.MULTILINE)
re_name = re.compile(r'[^a-zA-Z]', flags=re.DOTALL)

def extract_ruc(ruc_content):
    dictionary = {}
    fields = re_fields.search(ruc_content).group(1)
    dictionary = yaml.load(fields, Loader=yaml.SafeLoader)

    """
    key = ""
    val = ""
    for f in fields.splitlines():  
        kv = re.search(re_split, f)
        if kv:       
            key = kv.group(1)
            val = kv.group(2)
        else:
            val += '\n' + f
        if not key == "":
            dictionary[key] = val.strip()
    """
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

# Read the content from the Rich User Content file
with open('./ineo-content/src/tools/grlc.md', 'r') as file:
    grlc_mdfile = file.read()

# Extract the information and create the dictionary
ruc_contents = extract_ruc(grlc_mdfile)

print("grlc Rich User Contents: ", ruc_contents)

with open('./ineo-content/src/tools/mediasuite.md', 'r') as file:
    mediasuite_mdfile = file.read()

# Extract the information and create the dictionary for "mediasuite.md"
mediasuite_contents = extract_ruc(mediasuite_mdfile)

# Print the resulting dictionary for "mediasuite.md"
print(f"mediasuite Rich User Contents: ", mediasuite_contents)