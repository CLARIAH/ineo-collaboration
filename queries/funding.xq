(: This query evaluates the structure of the funder and funding fields to create objects with "title" and "link" for fill funding in the template.
If there's a funder field, it constructs an object with "title" as the name under funder and "link" as the url under funder.
If funding is an object (dictionary in jsoniq), it constructs an object with "title" as the name under funding or funding.funder and "link" as the url under funding or funding.funder.
If funding is an array, it constructs an array of objects by iterating through each item in the funding array. 
The [[1]] syntax is applied to these arrays, attempting to access the second value within each array.
If none of the conditions above are met, it returns the string "null". :)

(: This query evaluates the structure of the funder and funding fields to create objects with "title" and "link" for fill funding in the template.
If there's a funder field, it constructs an object with "title" as the name under funder and "link" as the url under funder.
If funding is an object (
  dictionary in jsoniq
), it constructs an object with "title" as the name under funding or funding.funder and "link" as the url under funding or funding.funder.
If funding is an array, it constructs an array of objects by iterating through each item in the funding array.
The [[1]] syntax is applied to these arrays, attempting to access the second value within each array.
If none of the conditions above are met, it returns the string "null". :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="{ID}"
where $i/js:string[@key='identifier']=$ID
return

if (exists($i/js:*[@key='funder'])) then
xml-to-json(
  <js:array>
    <js:map>
      <js:string key="title">{string($i/js:*[@key='funder']/js:*[@key='name'])}</js:string>
      <js:string key="link">{string($i/js:*[@key='funder']/js:*[@key='url'])}</js:string>
    </js:map>
  </js:array>
)
else if ($i/js:*[@key='funding']/self::js:map) then
xml-to-json(
  <js:array>
    <js:map>
      <js:string key="title">{string($i/js:*[@key='funding']/js:*[@key='name']),string($i/js:*[@key='funding']/js:*[@key='funder']/js:*[@key='name'])}</js:string>
      <js:string key="link">{string($i/js:*[@key='funding']/js:*[@key='url']),string($i/js:*[@key='funding']/js:*[@key='funder']/js:*[@key='url'])}</js:string>
    </js:map>
  </js:array>
)
else if ($i/js:*[@key='funding']/self::js:array) then
xml-to-json(
  <js:array>
    <js:map>
      <js:string key="title">{string($i/js:*[@key='name'])}</js:string>
      <js:string key="link">{string($i/js:*[@key='url'])}</js:string>
    </js:map>
  </js:array>
)
else "null"
