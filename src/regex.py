import re

def extract_ruc(ruc_content):
    dictionary = {}
    
    regex = r'^---(.*)---'
    fields = re.search(regex, ruc_content, flags=re.DOTALL).group(1)
    
    key = ""
    val = ""
    for f in fields.splitlines():
        regex = r'^(.*):(\s(.*)$|$)'
        kv = re.search(regex, f)
        if kv:       
            key = kv.group(1)
            val = kv.group(2)
        else:
            val += '\n' + f
        if not key == "":
            dictionary[key] = val.strip()

    regex = r'---\n#(.*?)\n\n(.*?)\n\n##'
    descriptions = re.findall(regex, ruc_content, flags=re.DOTALL)

    for description in descriptions:
        section_name = description[0].strip()
        section_content = description[1].strip()
        dictionary[section_name] = section_content
    
    regex = r'(?m)^##\s+(.*?)$(.*?)(?=^##\s|\Z)'
    sections = re.finditer(regex, ruc_content, flags=re.DOTALL | re.MULTILINE)
    
    for section in sections:
        section_name = section.group(1)
        
        section_content = section.group(2)
        dictionary[section_name] = section_content.strip()
    
    return dictionary
 