(: This query processes each item in the "developmentStatus" field of the codemeta.
If developmentStatus is an object or array, it checks if the "skos:prefLabel" property is "WIP" (which is then changed to Work in Progress).
If not, it returns an array containing the value of "skos:prefLabel".
If the item is an array, it further processes each element in the array.
The [[1]] is used to access the first element in the resulting array.
If none of the conditions match, it returns nothing. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

return
xml-to-json(
  <js:array>{
      for $i in js:map
      where $i/js:string[@key='identifier']=$ID
      for $item in ($i/js:map[@key='developmentStatus'], $i/js:array[@key='developmentStatus']/js:map)
      return
      (
        <js:string>{$item/js:string[@key='skos:prefLabel'][.="WIP"]/replace(., "^WIP$", "Work in Progress")}</js:string>,
        $item/js:string[@key='skos:prefLabel'][.!="WIP"]
      )
  }</js:array>
)
