(: This query check if issueTracker exists in the codemeta files. 
If so it returns Issue tracker as the title with the issueTracker codemeta value as the link. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $issueTracker :=


 for $i in js:map
  where $i/js:string[@key='identifier']=$ID
  return
    if (exists($i/js:*[@key='issueTracker']))
    then
        <js:map>
          <js:string key='title'>Issue tracker</js:string>
          <js:string key='link'>{string($i/js:*[@key='issueTracker'])}</js:string>
        </js:map>


return
  xml-to-json(
    <js:array>
      {
        $issueTracker
      }
    </js:array>
  )