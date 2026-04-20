(: This script focuses on extracting provider names and associated URLs from the "isSourceCodeOf" field,
ensuring that for arrays of names, it selects the English name with the respective URL. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="{ID}"
where $i/js:string[@key='identifier']=$ID
let $providerNames:=$i/js:*[@key='isSourceCodeOf']/js:*[@key='provider']/js:*[@key='name']
let $provider:=$i/js:map[@key='isSourceCodeOf']/js:*[@key='provider']
return

xml-to-json(
if (
  $providerNames/self::js:string
) then
        <js:array>
        <js:map>
          <js:string key="title">{
  string(
      $providerNames/self
  )
}</js:string>
          <js:string key="link">{
  string(
      $providerNames/js:*[@key='url']
  )
}</js:string>
        </js:map>
      </js:array>
else
        <js:array>
      {
   for $l in $providerNames/* return
      if (
    $l/js:string[@key='@language']="en"
  ) then
      <js:map>
        <js:string key="title">{
    string(
      $l/js:string[@key='@value']
    )
  }</js:string>
        <js:string key="url">{
          string(
      $provider/js:string[@key='url']
    )
        }</js:string>
      </js:map>
    }
      </js:array>
)
