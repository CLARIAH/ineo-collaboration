declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"
for $i in js:map
    where $i/js:string[@key='id']=$ID
return
xml-to-json(
<js:array>{
for $element in ($i/js:array[@key='genre'], $i/js:array[@key='modality'])
return $element/js:string
}</js:array>
)
