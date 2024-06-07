(: This query iterates over the urls in _landingPageRef and applies the following logic:
it first filters out those URLs that contain the substring "handle" (e.g.  "http://hdl.handle.net").
The regex then captures the part of a URL that starts with either "http://" or "https://",
followed by the domain (characters until the first "/"). The captured part includes both the protocol and domain, while ignoring the rest of the URL.
(https://archive.mpi.nl/islandora/object/lat%3A1839_00_0000_0000_0008_8C94_0#" >  "https://archive.mpi.nl"). If the host contains archive.mpi the title becomes
"Max Planck Institute for Psycholinguistics" otherwise the title is set on the url.
:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="doi_58_10.17026_47_dans-zeq-q3b7"

    for $i in js:map
    where $i/js:string[@key='id']=$ID

    return
    xml-to-json(
<js:array>
  <js:map>
    <js:string key='title'>{
      string($i/js:string[@key="dataProvider"])
    }</js:string>
    <js:null key='link' />
  </js:map>
</js:array>
)
(:
let $urls :=
    for $i in js:map
    where $i/js:string[@key='id']=$ID

return parse-json($i/js:*[@key="_landingPageRef"])

let $parsedUrls :=
  for $entry in $urls
  let $url := $entry('url')
  where not(contains($url, "handle"))
  return replace($url, "^(https?://[^/]+).*", "$1")


let $host :=
for $item in $parsedUrls
return
<js:array>
  <js:map>
    <js:string key='title'>{
      if (contains($item, "archive.mpi")) then "Max Planck Institute for Psycholinguistics" else $item
    }</js:string>
    <js:string key='link'>{$item}</js:string>
  </js:map>
</js:array>

return xml-to-json($host)
:)
