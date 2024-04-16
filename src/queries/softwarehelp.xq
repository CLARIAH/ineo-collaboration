(: This query extracts information from the "softwareHelp" field, ensuring proper handling for both object (dicionary) and array structures within it. 
If the field is an object, it extracts the name and URL. 
If it's an array, it extracts multiple sets of name and URL pairs, and if none of these structures match, it returns nothing. :) 

declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="{ID}"
where $i/js:string[@key='identifier']=$ID

return
for $item in $i/js:*[@key='softwareHelp']
return
  xml-to-json(
    if ($item/self::js:map) then
      <js:array>
        <js:map>
          <js:string key="title">{string($item/js:*[@key='name'])}</js:string>
          <js:string key="link">{string($item/js:*[@key='url'])}</js:string>
        </js:map>
      </js:array>
    else if ($item/self::js:array) then
      <js:array>
      { for $l in $item/* return
        <js:map>
          <js:string key="title">{string($l/js:*[@key='name'])}</js:string>
          <js:string key="link">{string($l/js:*[@key='url'])}</js:string>
        </js:map>
      }
      </js:array>
  )
