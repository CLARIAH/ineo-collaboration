(: This query focuses on the "format" key of the datasets, which will be mapped to the Mediatype field in INEO. Descriptions returns a list of format (e.g. "video/x-mpeg1").
These values are then split by the "/" delimiter, ensuring uniqueness in the format names (e.g. video, x-mpeg1"). :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $descriptions := (
    for $i in js:map
    where $i/js:string[@key='id']=$ID
    return $i/js:array[@key='format']/js:string
)

let $distinct-results := distinct-values($descriptions)
let $filtered-results := $distinct-results[. != "unknown type"]
return
if (empty($filtered-results)) then ""
else
xml-to-json(
  <js:array>{
    for $item in $filtered-results
    return
    <js:string>{$item}</js:string>
  }</js:array>
)