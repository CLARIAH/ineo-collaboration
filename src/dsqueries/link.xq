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
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
    let $landingPageRef := $i/js:*[@key="_landingPageRef"][1]
    return if (exists($landingPageRef)) then parse-json($landingPageRef)('url') else ()
  )

let $parsed :=
  (for $resource in $resourceRef
  return
  try {
   let $jsonObject := parse-json(normalize-space($resource))
   where contains($jsonObject('url'), "dx.doi.org") or contains($jsonObject('url'), "data.beeldengeluid")
   return $jsonObject('url')

} catch * { () }
)

let $selflink :=
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return $i/js:*[@key="_selfLink"])

return
xml-to-json(
<js:string>{
  if (exists($parsed)) then $parsed
  else if (exists($landingPageRef)) then normalize-space(tokenize($landingPageRef, ",")[1])
else string($selflink)
}</js:string>
)
