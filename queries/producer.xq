(: This query focuses on extracting producer names (producer in codemeta) and associated URLs, ensuring that for arrays of names, it selects the English name with the respective URL.

If the "producer.name" field is a string, it constructs an object with a "title" representing the producer's name and a "link" pointing to the producer's URL.
If the "producer.name" field is an array, it further processes each name in the array.
In that array, it filters these names to extract the one where the "@language" property is "en" (English).
Constructs objects with a "title" representing the name in English and a "link" pointing to the producer's URL. :)


declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='identifier']=$ID
return
xml-to-json(
<js:array>
  <js:map>
    <js:string key='title'>{
      string(
        (
        $i/js:*[@key='producer']/js:string[@key='name'],
        ($i/js:*[@key='producer']/js:array[@key='name']/js:map[js:*[@key='@language']="en"]/js:*[@key='@value'])
      )[1]
    )
    }</js:string>
    <js:string key='link'>{
      string($i/js:*[@key='producer']/js:string[@key='url'])
    }</js:string>
  </js:map>
</js:array>
)