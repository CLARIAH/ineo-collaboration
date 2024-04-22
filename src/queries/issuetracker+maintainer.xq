(: This query first searches for an issue tracker ($issueTracker in the codemeta)  based on a specified identifier. If issuetracker exists, 
it constructs an object with a "title" of "Issue tracker" and a "link" to the issue tracker.
If no issue tracker is found, it returns information about project maintainers ($maintainers).
It constructs objects with "title" as the concatenated given- and family names of maintainer and appropriate "links" based on their email or sameAs fields.
It handles different scenarios for maintainer data, considering single objects, arrays, and diverse email formats.
It then gathers unique combinations of titles and links from the maintainers' data, ensuring proper formatting for email links :) 


declare namespace js="http://www.w3.org/2005/xpath-functions";
let $ID:="{ID}"
let $issueTracker :=
  for $i in js:map
  where $i/js:string[@key='identifier']=$ID
  return
    if (exists($i/js:string[@key='issueTracker'])) then
    element issueTracker {
      attribute title {"Issue tracker"},
      attribute link {$i/js:string[@key='issueTracker']}
    }
    else ()

let $maintainers :=
  if (empty($issueTracker))
  then (
    for $i in js:map
      where $i/js:string[@key='identifier']=$ID
      let $maintainer:=$i/js:array[@key='maintainer']
      return
      if (exists($maintainer/js:string[@key='email'])) then
        element maintainer {
          attribute title {concat(string($maintainer/js:string[@key='givenName']), " ", string($maintainer/js:string[@key='familyName']))},
          attribute link {
            let $email:=string($maintainer/js:string[@key='email'])
            return
            if (contains($email, "mailto:")) then $email
            else concat("mailto:", $email)
          }
        }
      else if (exists($maintainer/js:string[@key='sameAs'])) then
        element maintainer {
          attribute title {concat(string($maintainer/js:string['givenName']), " ", string($maintainer/js:string[@key='familyName']))},
          attribute link {string($maintainer/js:string[@key='familyName'])}
        }
      else
        element maintainer {
          attribute title {concat(string($maintainer/js:srring[@key='givenName']), " ", string($maintainer/js:string[@key='familyName']))},
          attribute link {$maintainer/@id}
        }
  )
  else ()

return (
  if (empty($issueTracker))
  then $maintainers
  else $issueTracker
)
