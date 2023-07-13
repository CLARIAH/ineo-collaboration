import re

def extract_ruc(ruc_content):
    dictionary = {}
    
    # Extracting identifier
    identifier = re.search(r'identifier:\s*(.+)', ruc_content)
    if identifier:
        dictionary['identifier'] = identifier.group(1)
    
    # Extracting title
    title_match = re.search(r'title:\s*(.+)', ruc_content)
    if title_match:
        dictionary['title'] = title_match.group(1)
    
    grlc = re.search(r'grlc\n\n(.+)', ruc_content)
    if grlc:
        dictionary['grlc'] = grlc.group(1).strip()
    
    overview_match = re.search(r'##\s*Overview\s*\n+(.*?)(?=##)', ruc_content, re.DOTALL)
    if overview_match:
        dictionary['overview'] = overview_match.group(1).strip()
    
    instruction = re.search(r'###\s*Instruction webpages\s*\n+(.+?)\n+##', ruc_content)
    if instruction:
        dictionary['Instruction webpages'] = instruction.group(1).strip()
    
    articles = re.search(r'### Articles.*?\n\n(.*?)\n', ruc_content)
    if articles:
        dictionary['Articles'] = articles.group(1)
    
    return dictionary

# Read the content from the Rich User Content file
with open('ineo-content/src/tools/grlc.md', 'r') as file:
    grlc_mdfile = file.read()

# Extract the information and create the dictionary
ruc_contents = extract_ruc(grlc_mdfile)

print("grlc Rich User Contents: ", ruc_contents)

exit()

with open('ineo-content/src/tools/mediasuite.md', 'r') as file:
    mediasuite_mdfile = file.read()

# Extract the information and create the dictionary for "mediasuite.md"
mediasuite_contents = extract_ruc(mediasuite_mdfile)

# Print the resulting dictionary for "mediasuite.md"
print(f"mediasuite Rich User Contents: ", mediasuite_contents)
