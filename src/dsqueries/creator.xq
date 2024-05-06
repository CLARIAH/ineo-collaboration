declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $creators :=
    for $i in js:*
    where $i/js:string[@key='id']=$ID
    return $i/js:*[@key='creator']

let $creator :=
    if (exists($creators))
    then
        for $c in $creators
        return
  <js:array>
    <js:map>
      <js:string key="title">{string($c)}</js:string>
      <js:string key="link">null</js:string>
    </js:map>
  </js:array>

    else ()

return xml-to-json($creator)
