declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"
let $ID:="https_58__47__47_hdl.handle.net_47_10744_47_ca210971-0e15-47bb-bc3f-292afa7ff07c"

let $languages := (
    for $i in js:map
    where $i/js:string[@key='id']=$ID
    return $i/js:*[@key="_languageName"]
)

let $filteredLanguages := (
    for $language in distinct-values($languages)
    where $language ne "Unspecified" and $language ne "Unknown"
    return $language
)

return [$filteredLanguages]
