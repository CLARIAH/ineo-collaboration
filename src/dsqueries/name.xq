(: Because the value in the datasets jsons are in a list, this query converts it to a string and ensures a single item in case of multiple matches
let $ID:="https_58__47__47_hdl.handle.net_47_10744_47_ca210971-0e15-47bb-bc3f-292afa7ff07c"
:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $name :=
    (
    for $i in js:map
    where $i/js:string[@key='id']=$ID

        return $i/js:*[@key='name']
    )[1]

return string($name)
