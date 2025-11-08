(: This query takes the value of the name field in the codemeta. Some of these values are lowercase only.  
It first checks if there's a non-empty result. If there is, it capitalizes the first letter of the string stored in $result and returns the modified string:
substring($result, 1, 1): Extracts the first character of $result.
upper-case(): Converts the first character to uppercase.
substring($result, 2): Extracts the substring starting from the second character of $result.
concat(): Combines the uppercase first character with the rest of the string starting from the second character.

If $result is empty, it returns nothing. :)


declare namespace js="http://www.w3.org/2005/xpath-functions";

declare namespace functx = "http://www.functx.com";
declare function functx:capitalize-first
  ( $arg as xs:string? )  as xs:string? {

   concat(upper-case(substring($arg,1,1)),
             substring($arg,2))
 };

for $i in js:map
let $ID:="{ID}"
where $i/js:string[@key='identifier']=$ID
return
  xml-to-json(
          <js:string>{functx:capitalize-first(string($i/js:*[@key='name'][1]))}</js:string>
  )