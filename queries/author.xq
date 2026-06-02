(: This query essentially processes author data from a the jsonl file, extracts their names, affiliations, and associated links,
ensuring uniqueness in title-link pairs before returning the resulting JSON structure. It determines the author's title by checking various conditions
related to their affiliations and name. It constructs a string representing the author's name and affiliation(s) in different scenarios (whether it is an array or dictionary (object))

More specifically, for the links, it first attempts to retrieve a link associated with the author:
If a URL exists directly in the author data, it uses that.
If not, it checks if there's an alternative link specified as "sameAs."
If there's an @id present and it doesn't start with "https://tools.clariah.nl", it uses that as a link.
Otherwise, it returns an empty sequence for the link.

:)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

let $results := (
 for $i in js:map
  where $i/js:string[@key='identifier']=$ID
return (

 for $author in ($i/js:map[@key='author'],$i/js:array[@key="author"]/js:map)
  let $title :=
  if (exists($author/js:*[@key='affiliation']) and $author/js:*[@key='affiliation']/js:*[@key='name']/self::js:array) then
    for $name in $author/js:*[@key='affiliation']/js:*[@key='name']
      where string($name/js:*[@key='@language']) = "en"
      return
        $author/js:*[@key='givenName'] || " " || $author/js:*[@key='familyName'] || ", " || $name/js:*[@key='@value']
  else if (exists($author/js:*[@key='affiliation']) and $author/js:*[@key='affiliation']/js:*[@key='name']/self::js:string) then
    $author/js:*[@key='givenName'] || " " || $author/js:*[@key='familyName'] || ", " || $author/js:*[@key='affiliation']/js:*[@key='name']
  else if (exists($author/js:*[@key='affiliation']) and $author/js:*[@key='affiliation']/js:*[@key='legalName']/self::js:string) then
    $author/js:*[@key='givenName'] || " " || $author/js:*[@key='familyName'] || ", " || $author/js:*[@key='affiliation']/js:*[@key='legalName']
  else if (exists($author/js:*[@key='affiliation']) and $author/js:*[@key='affiliation']/self::js:array) then
    for $name in $author/js:*[@key='affiliation'][1]
    return
      $author/js:*[@key='givenName'] || " " || $author/js:*[@key='familyName'] || ", " || $name/js:*[@key='name']
  else
    $author/js:*[@key='givenName'] || " " || $author/js:*[@key='familyName']

  return
    <js:array>
      <js:map>
        <js:string key='title'>{$title}</js:string>
        <js:string key='link'>{string(
          (
            $author/js:*[@key="url"],
            $author/js:*[@key="sameAs"],
            $author/js:*[@key="@id"][not(starts-with(., "https://tools.clariah.nl"))],
            ()
          )[1])
        }</js:string>
      </js:map>
    </js:array>
  )
)

let $uniqueValues :=
  for $result in distinct-values(
    for $r in $results/js:map
    return concat(
      string($r/js:*[@key="title"]),
      "|",
      string-join(
        for $link in $r/js:*[@key="link"]
        return if ($link/self::js:string) then $link else (),
        "|"
      )
    )
  )
  let $title := substring-before($result, "|")
  let $link := substring-after($result, "|")
  group by $title
    return
      <js:map>
        <js:string key='title'>{$title}</js:string>
        <js:string key='link'>{$link}</js:string>
      </js:map>
return
  xml-to-json(<js:array>{$uniqueValues}</js:array>)
