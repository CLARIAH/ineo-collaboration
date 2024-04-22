(: For each matching item, this query constructs an array containing objects with two fields:

"title": It extracts a substring from the codeRepository field by taking the content between "://" and the first "/" after that. This effectively isolates the domain or service name from the URL.
For instance: https://github.com/knaw-huc/huc-cmdi-app - > github.com
"link": It directly assigns the codeRepository field as the link.:)


declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
  <js:array>
  <js:map>
  <js:string key="title">{substring-before(substring-after(string($i/js:*[@key='codeRepository']), "://"), "/")}</js:string>
  <js:string key="link">{string($i/js:*[@key='codeRepository'])}</js:string>
  </js:map>
  </js:array>

)
