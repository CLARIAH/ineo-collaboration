(: This query retrieves the version from the codemeta files. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
  <js:array>
    <js:map>
      <js:string key='title'>{string($i/js:*[@key='version'])}</js:string>
      <js:string key='url'></js:string>
    </js:map>
  </js:array>
)