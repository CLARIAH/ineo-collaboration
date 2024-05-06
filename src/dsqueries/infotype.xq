(: This query iterates over the urls in _landingPageRef and applies the following logic:
it first filters out those URLs that contain the substring "handle" (e.g.  "http://hdl.handle.net").
The regex then captures the part of a URL that starts with either "http://" or "https://",
followed by the domain (characters until the first "/"). The captured part includes both the protocol and domain, while ignoring the rest of the URL.
(https://archive.mpi.nl/islandora/object/lat%3A1839_00_0000_0000_0008_8C94_0#" >  "https://archive.mpi.nl"). If the host contains archive.mpi the title becomes
"Max Planck Institute for Psycholinguistics" otherwise the title is set on the url.
:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

    for $i in js:map
    where $i/js:string[@key='id']=$ID
return

[$i/js:*[@key='genre'], $i/js:*[@key='modality']]

(:
xml-to-json(
  <js:array>
  <js:map>
    <js:string key='title'>{}</js:string>
    <js:string key='link'>{$i}</js:string>
  </js:map>
</js:array>
)
  [($i.genre[], $i.modality[])]
:)