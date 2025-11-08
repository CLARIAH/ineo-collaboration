(: This query operates on a JSONL file, limiting results to 10 items and filtering based on a specified identifier defined by template.py.
It checks if the applicationCategory field in the codemeta is an array. If it is, it iterates through each item in the array and retrieves those whose @id field starts with "http",
returning an array of these @id values. If applicationCategory is not an array, it returns an empty result. :)

declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
<js:array>
{
  $i/js:array[@key='applicationCategory']/js:map/js:*[@key='@id'][starts-with(., "http")]
}
</js:array>
)
