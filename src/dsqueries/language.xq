declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $languages := (
    for $i in js:map
    where $i/js:string[@key='id']=$ID
    return $i/js:*[@key="_languageName"]
)

let $filteredLanguages := (
    for $language in distinct-values($languages)
    where $language ne "Unspecified" and $language ne "Unknown"
    return <js:string>{$language}</js:string>
)

return xml-to-json(
<js:array>{$filteredLanguages}</js:array>
)
