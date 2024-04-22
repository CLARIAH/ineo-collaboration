(: If applicationCategory is an array, it creates a variable $filteredItems that stores a filtered set of items.
It iterates through each item in applicationCategory[].
If an item is a string, it converts it to a string type and includes it in the $filteredItems array.
This query maps the applicationCategory to researchDomains.:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
  <js:array>
  {
    for $item in $i/js:array[@key='applicationCategory']/js:string
    return $item
  }
  </js:array>
  )

