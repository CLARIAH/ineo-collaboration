(: This query focuses on the consumed and produced data formats within the isSourceCodeOf of codemeta.
It first checks the structure of the consumesData and producesData fields within the isSourceCodeOf.
If these fields are arrays, it iterates through each item to extract the encodingFormat.
If they are objects, it directly retrieves the encodingFormat.
It constructs a list of consumed and produced data formats ($consumesFormats and $producesFormats respectively (e.g. plain/text)).
The values are then split by the "/" delimiter, ensuring uniqueness in the format names (e.g. plain, text). :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $results := (
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID

  return
    let $consumesFormats :=
      if ($i/js:*[@key='isSourceCodeOf']/js:*[@key='consumesData']/self::js:array) then
      for $data in $i/js:*[@key='isSourceCodeOf']/js:*[@key='consumesData']/*
      return
      $data/js:*[@key='encodingFormat']
      else if ($i/js:*[@key='isSourceCodeOf']/js:*[@key='consumesData']/self::js:map) then
      $i/js:*[@key='isSourceCodeOf']/js:*[@key='consumesData']/js:*[@key='encodingFormat']
      else
      ()

    let $producesFormats :=
    if ($i/js:*[@key='isSourceCodeOf']/js:*[@key='producesData']/self::js:array) then
      for $data in $i/js:*[@key='isSourceCodeOf']/js:*[@key='producesData']/*
      return
      $data/js:*[@key='encodingFormat']
    else if ($i/js:*[@key='isSourceCodeOf']/js:*[@key='producesData']/self::js:map) then
      $i/js:*[@key='isSourceCodeOf']/js:*[@key='producesData']/js:*[@key='encodingFormat']
    else
    ()
    return ($consumesFormats, $producesFormats)

)


let $splitValues :=
  for $value in $results
  for $component in tokenize($value, "/")
  return $component

let $distinct-results := distinct-values($splitValues)
return
if (empty($distinct-results)) then ""
else
xml-to-json(
  <js:array>{
    for $item in $distinct-results
    return
    <js:string>{$item}</js:string>
  }</js:array>
)
