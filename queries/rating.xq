(: This query filters resources where the reviewRating is equal or more than 3,
and returns the identifier field from the filtered resources. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

xml-to-json(
  <js:array>{
for $i in js:map
let $rating := $i/js:map[@key='review']/js:number[@key='reviewRating']
where number($rating) ge 3
return $i/js:string[@key='identifier']
}</js:array>)