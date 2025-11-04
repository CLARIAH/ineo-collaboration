(:
This query maps a URL to the link field in the template for INEO. The link field maps to the "Go to resource" button in INEO.

It first checks if there is a isSourceCodeOf field for WebApplication and WebSite (e.g. for mediasuite) in the codemeta.
If there is, then it takes the url of the isSourceCodeOf as the link. So, the targetproduct url has only priority over the url root field in case the type is "WebApplication" of "Website".

If the tool is not a WebApplication or a WebSite, it checks for the 'url' root field. It checks if the value of url is an object (dictionary)
or a string with a 'url' property in the codemeta file.
If there is not a url key in the codemeta (e.g. for alud) it returns the value of the codeRepository as a fallback :)


declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

for $i in js:map
where $i/js:string[@key='identifier']=$ID
return
xml-to-json(

(
  $i/js:*[@key='isSourceCodeOf']/js:*[@key='url'][$i/js:*[@key='isSourceCodeOf']/js:map/js:*[@key='@type'][.="WebApplication"]],
  $i/js:*[@key='isSourceCodeOf']/js:*[@key='url'][$i/js:*[@key='isSourceCodeOf']/js:map/js:*[@key='@type'][.="WebSite"]],
  $i/js:*[@key='url']/js:*[@key='url'],
  $i/js:*[@key='codeRepository']
)[1]
)
