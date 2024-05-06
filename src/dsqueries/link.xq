(: This query aims to retrieve relevant URLs for the link property in INEO (Go to resource button), with a preference for URLs containing "dx.doi.org" in the field _resourceRef.
If there is not a dx.doi URL for the resource it searched for a URL in the _landingPageRef, and finally, if the _landingPageRef is not available,
it takes the self-link URL. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"


let $resourceRef :=
    (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return $i/js:*[@key="_resourceRef"])

let $landingPageRef :=
  (    for $i in js:map
    where $i/js:string[@key='id']=$ID
   return parse-json($i/js:*[@key="_landingPageRef"])('url'))

let $parsed :=
  (for $resource in $resourceRef
   let $jsonObject := parse-json($resource)
   where contains($jsonObject('url'), "dx.doi.org") or contains($jsonObject('url'), "data.beeldengeluid")
   return $jsonObject('url'))

let $selflink :=
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return $i/js:*[@key="_selfLink"])

return
  if (exists($parsed)) then $parsed
  else if (exists($landingPageRef)) then $landingPageRef
else $selflink
