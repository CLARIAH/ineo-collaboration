declare namespace js="http://www.w3.org/2005/xpath-functions";

let $ID:="{ID}"

return xml-to-json(
  <js:array>{
      for $i in js:*
      where $i/js:string[@key='id']=$ID
      let $creators := $i/js:*[@key='creator']
      for $creator in $creators/*
      return
        <js:map>
          <js:string key="title">{string($creator)}</js:string>
          <js:string key="link">null</js:string>
        </js:map>
  }</js:array>
)
