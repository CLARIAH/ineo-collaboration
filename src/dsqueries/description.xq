(: This query extracts the "description" field (list), which will be mapped to the intro fields in INEO. The query iterates over each descriptions and filters
those descriptions that contains specific language code {code:eng}", "{code:und}" and "{code:lbe}"). The replace function then removes the langauge codes and newsline characters from each
descriptions. The descriptions are then merges and normalized, removing multiple consecutive spaces within the string.
:)

declare namespace js="http://www.w3.org/2005/xpath-functions";


let $ID:="{ID}"

let $description := (
    for $i in js:map
    where $i/js:string[@key='id']=$ID
    return $i/js:*[@key='description']
)

let $english := (
    for $item in $description
 where contains($item, "{code:eng}") or contains($item, "{code:und}")
    return replace(replace($item, "\{code:[^}]+\}", " "), "\n", " ")
)

let $mergedString := normalize-space(string-join($english, ""))

return xml-to-json(<js:string>{$mergedString}</js:string>)
