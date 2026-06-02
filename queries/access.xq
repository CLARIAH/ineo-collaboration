(: This query operates on a JSONL file, limiting results to 10 items and filtering based on a specified identifier defined by template.py.
It retrieves the codemeta value from codeRepository, returning the link and setting the title to "Open Access" if that link contains "github".
If the condition is not met, it returns an empty result.:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
  if (contains($i/js:*[@key='codeRepository'], "github"))
  then
  <js:array>
    <js:map>
      <js:string key="title">Open Access</js:string>
      <js:string key="link">{string($i/js:*[@key='codeRepository'])}</js:string>
    </js:map>
  </js:array>
  else ()

)