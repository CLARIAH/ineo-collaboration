(: This query extracts and organizes maintainers' names and associated links (emails or reference links),
ensuring uniqueness in the title-link pairs while handling various formats of email addresses.
It first iterates through the codemeta file and checks the structure of the "maintainer" field.
Depending on whether the "maintainer" is an object, an array, or contains specific properties like "email" or "sameAs,"
it constructs objects containing "title" (a combination of given and family names) and "link" (an email address or a reference link).
It processes various scenarios for email addresses within the "maintainer" field, ensuring that links are formatted correctly as mailto: email. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $results :=
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID
  return
  let $maintainers := $i/js:*[@key='maintainer']
  for $maintainer in ($maintainers/self::js:array/*)
  return
      <js:map>
        <js:string key="title">{string($maintainer/js:string[@key='givenName'])}&#x00A0;{string($maintainer/js:string[@key='familyName'])}</js:string>
        <js:string key="link">{
          (
            $maintainer/js:*[@key='email'][starts-with((self::js:string, self::js:array/js:string[1])[1], 'mailto:')],
            concat("mailto:", ($maintainer/js:*[@key='email']/self::js:string, $maintainer/js:*[@key='email']/self::js:array/js:string[1])[1]),
            $maintainer/js:string[@key='sameAs'],
            $maintainer/js:string[@key='@id'],
            ""
          )[1]

        }
        </js:string>
      </js:map>

return xml-to-json(
  <js:array>{
    for $person in distinct-values($results/string(js:string[@key='title']))
    return $results[js:string[@key='title'][.=$person]][1]
  }</js:array>
)