(: This query gets the YYYY-MM-DD of a given record :)
declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="{ID}"
where $i/js:string[@key='identifier']=$ID

return xml-to-json(<js:string>{substring($i/js:string[@key='dateCreated'], 1, 10)}</js:string>)