(: This query extracts either "licenseType" or "accessInfo" field based on their existence to INEO's Access.

If the "licenseType" contains "UNSPECIFIED," it takes, if it is there, the accessInfo as the 'title' otherwise it takes the licenceType (thus UNSPECIFIED).
If it contains "PUB," it returns a array with "Public" as the title.
If it contains "ACA," it returns a array indicating "Academic" as the title.
If it contains "RES," it returns a JSON array indicating "Restricted for individual" as the title.
If none of the conditions match, it returns an empty string (null)

For the link it uses the "license". If "license" does not exists, it returns an empty string (null) :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $licensetype :=
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return if (exists($i/js:*[@key='licenseType'])) then $i/js:*[@key='licenseType'] else ())


let $license :=
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return if (exists($i/js:*[@key='license'])) then $i/js:*[@key='license'][1] else ())


let $accessinfo :=
  (for $i in js:map
    where $i/js:string[@key='id']=$ID
   return if (exists($i/js:*[@key='accessInfo'])) then $i/js:*[@key='accessInfo'][1] else ())

let $formattedAccess :=
  (if ($licensetype) then $licensetype[1] else ())

return
xml-to-json(
  if ($accessinfo) then
  if (contains($formattedAccess, "UNSPECIFIED")) then
  <js:array>
    <js:map>
      <js:string key="title">{string($accessinfo)}</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "PUB")) then
    <js:array>
    <js:map>
      <js:string key="title">Public</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "ACA")) then
  <js:array>
    <js:map>
      <js:string key="title">Academic</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "RES")) then
  <js:array>
    <js:map>
      <js:string key="title">Restricted for individual</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>

  else ()
  (:else "Unspecified":)

  else
  if (contains($formattedAccess, "UNSPECIFIED")) then
  <js:array>
    <js:map>
      <js:string key="title">{string($formattedAccess)}</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "PUB")) then
  <js:array>
    <js:map>
      <js:string key="title">Public</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "ACA")) then
  <js:array>
    <js:map>
      <js:string key="title">Academic</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else if (contains($formattedAccess, "RES")) then
  <js:array>
    <js:map>
      <js:string key="title">Restricted for individual</js:string>
      <js:string key="link">{string($license)}</js:string>
    </js:map>
  </js:array>
  else ()
  )
