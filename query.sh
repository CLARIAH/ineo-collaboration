# query
curl -X GET "http://indexer:9200/ineo/_search" -H 'Content-Type: application/json' -d '
{
  "query": {
    "term": {
      "document.id": "http_58__47__47_data.collectienederland.nl_47_id_47_dataset_47_provinciaal-depot-bodemvondsten-noord-brabant"
    }
  }
}
'

curl -X GET "http://indexer:9200/ineo/_search" -H 'Content-Type: application/json' -d '
{
  "query": {
    "term": {
      "document.title": "provinciaal-depot-bodemvondsten-noord-brabant"
    }
  }
}
'

# delete all
curl -X POST "http://indexer:9200/ineo/_delete_by_query" -H 'Content-Type: application/json' -d '
{
  "query": {
    "match_all": {}
  }
}
'

# count
curl -X GET "http://indexer:9200/ineo/_count" -H 'Content-Type: application/json' -d '
{
  "query": {
    "match_all": {}
  }
}
'
