(: This query evaluates the structure of the funder and funding fields to create objects with "title" and "link" for fill funding in the template.
If there's a funder field, it constructs an object with "title" as the name under funder and "link" as the url under funder.
If funding is an object (dictionary in jsoniq), it constructs an object with "title" as the name under funding or funding.funder and "link" as the url under funding or funding.funder.
If funding is an array, it constructs an array of objects by iterating through each item in the funding array. 
The [[1]] syntax is applied to these arrays, attempting to access the second value within each array.
If none of the conditions above are met, it returns the string "null". :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

for $i in js:map
let $ID:="alpinograph"
where $i/js:string[@key='identifier']=$ID
return

if (exist($i/js:*[@key='funder'])) then
[{"title": $i/js:*[@key='funder']/js:*[@key='name'], "link": $i/js:*[@key='funder']/js:*[@key='url']}]
else if ($i/js:*[@key='funding'] instance of object) then
[{"title": [$i/js:*[@key='funding']/js:*[@key='name'],$i/js:*[@key='funding']/js:*[@key='funder']/js:*[@key='name']][[1]], "link": [$i/js:*[@key='funding']/js:*[@key='url'], $i/js:*[@key='funding']/js:*[@key='funder']/js:*[@key='url']][[1]]}]
else if ($i/js:*[@key='funding'] instance of array) then [
for $item in $i/js:*[@key='funding']/*
return {"title": $item/js:*[@key='name'], "link": $item/js:*[@key='url']}]

else "null"