(: This query focuses on the consumed and produced data formats within the targetProduct of codemeta.
It first checks the structure of the consumesData and producesData fields within the targetProduct.
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
      if ($i/js:*[@key='targetProduct']/js:map/js:*[@key='consumesData']/self::js:array) then
      for $data in $i/js:*[@key='targetProduct']/js:map/js:*[@key='consumesData']
      return
      $data/js:*[@key='encodingFormat']
      else if ($i/js:*[@key='targetProduct']/js:map/js:*[@key='consumesData']/self::js:map) then
      $i/js:*[@key='targetProduct']/js:map/js:*[@key='consumesData']/js:*[@key='encodingFormat']
      else
      ()

    let $producesFormats :=
    if ($i/js:*[@key='targetProduct']/js:map/js:*[@key='producesData']/self::js:array) then
    for $data in $i/js:*[@key='targetProduct']/js:map/js:*[@key='producesData']
    return
    $data/js:*[@key='encodingFormat']
    else if ($i/js:*[@key='targetProduct']/js:map/js:*[@key='producesData']/self::js:map) then
    $i/js:*[@key='targetProduct']/js:*[@key='producesData']/js:map/js:*[@key='encodingFormat']
    else
    ()
    return ($consumesFormats, $producesFormats)

)


let $splitValues :=
  for $value in $results
  for $component in tokenize($value, "/")
  return $component

return [distinct-values($splitValues)]
