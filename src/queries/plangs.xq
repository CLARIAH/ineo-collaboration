(: This query extracts and organizes values from the "programmingLanguage" field in the codemeta.
It creates objects with "title" representing programming language names and "link" set to null, 
catering to different data types (string, object, array) within the codemeta field of programmingLanguage.:)


declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="vurmpipe"
where $i/js:string[@key='identifier']=$ID
for $item in $i/js:*[@key='programmingLanguage']
return
  xml-to-json(
    if ($item/self::js:string) then
      <js:array>
        <js:map>
          <js:string key="title">{string($item)}</js:string>
          <js:null key="link"/>
        </js:map>
      </js:array>
    else if ($item/self::js:map) then
      <js:array>
        <js:map>
          <js:string key="title">{string($item/js:*[@key='name'])}</js:string>
          <js:null key="link"/>
        </js:map>
      </js:array>
    else if ($item/self::js:array) then
      <js:array>
      { for $l in $item/* return
        <js:map>
          <js:string key="title">{string($l)}</js:string>
          <js:null key="link"/>
        </js:map>
      }
      </js:array>
  )