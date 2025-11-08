(: This query works on extracting and organizing inLanguage properties associated with consumed (consumesData) and produced data (producesData) formats within the targetProduct field of codemeta :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"
let $results := (
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID
  return
  if ($i/js:array[@key='targetProduct']) then
    for $item in $i/js:array[@key='targetProduct']/*
    let $consumesFormats :=
      if ($item/js:map[@key='consumesData']) then
        $item//js:map[@key='consumesData']//js:*[@key='inLanguage']/js:*[@key='name']
      else if ($item/js:array[@key='consumesData']) then
        for $data in $item/js:array[@key='consumesData']/*
        return $data/js:*[@key='inLanguage']/js:*[@key='name']
      else ()
    let $producesFormats :=
      if ($item/js:map[@key='producesData']) then
        $item/js:map[@key='producesData']/js:*[@key='inLanguage']/js:*[@key='name']
      else if ($item/js:array[@key='producesData']) then
        for $data in $item/js:*[@key='producesData']/*
        return $data/js:*[@key='inLanguage']/js:*[@key='name']
      else ()
    return ($consumesFormats, $producesFormats)
  else if ($i/js:map[@key='targetProduct']) then
    let $consumesFormats :=
      for $product in $i/js:map[@key='targetProduct']/js:*[@key='consumesData']
      return $product/js:*[@key='inLanguage']/js:*[@key='name']
    let $producesFormats :=
      for $prod in $i/js:map[@key='targetProduct']/js:*[@key='producesData']
      return $prod/js:*[@key='inLanguage']/js:*[@key='name']

    return ($consumesFormats, $producesFormats)
  else ()
)
let $distinct-results := distinct-values($results)
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