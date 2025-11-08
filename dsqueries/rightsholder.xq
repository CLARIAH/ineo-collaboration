declare namespace js="http://www.w3.org/2005/xpath-functions";


let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='id']=$ID

return xml-to-json(
<js:array>{

for $j in $i/js:*[@key='rightsHolder']
return <js:map>
    <js:string key="title">{string($j)}</js:string>
    <js:string key="link">null</js:string>
</js:map>
}
</js:array>
)
