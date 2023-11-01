# Resources api

The api is available at https://ineo-resources-api-5b568b0ad6eb.herokuapp.com.

## Authorization

All requests need the "Authorization header". For example:

`curl 'https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/resources/' -H "Authorization: bearer $INEO_RESOURCES_API_TOKEN"`

## Request resources

When the http request method is `GET` you can request resources. This is an optional catch all route. So you can either fetch all resources at the base endpoint, or specific resources by specifying their id's in subsequent path segments.

- `/resources` returns all resources;
- `/resources/123` returns resource with id `123`;
- `/resources/123/456` returns resources with id's `123` and `456`.

The response contains the resource(s) as json.

## Request properties

All available properties can be requested through the endpoint `/properties/$type`:

- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/resourceTypes
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchActivities
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/researchDomains
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/informationTypes
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/languages
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/status
- https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/properties/mediaTypes

## Send resources

When the http request method is `POST` you can send resources to the base endpoint `/resources`. The expected body content type is `application/json`. Always send an array of objects. Each object must contain an operation and a document.

### Operations

You can perform three operations: create, update and delete.

A document must always contain an `id`. This `id` equals the path to the resource. So a document with id `alpino` will be available at `https://www.ineo.tools/resources/alpino`.

Images inside the `media.thumbnail` or `media.slider` will be uploaded to Ineo's CDN.

#### Create

A full resource looks like this:

```JSON
[
  {
    "operation": "create",
    "document": {
      "id": "string",
      "title": "string",
      "intro": "text",
      "publishedAt": "yyyy-mm-dd",
      "media": {
        "thumbnail": "https://picsum.photos/800/600.webp",
        "slider": [
          "https://picsum.photos/800/600.webp",
          "https://vimeo.com/538016781",
          "https://youtu.be/INUHCQST7CU",
        ]
      },
      "tabs": {
        "overview": {
          "body": "markdown",
          "bodyMore": "markdown"
        },
        "learn": { "body": "markdown" },
        "mentions": { "body": "markdown" },
        "metadata": { "body": "markdown" }
      },
      "properties": {
        "link": "url",
        "intro": "text",
        "resourceTypes": [],
        "researchActivities": [
          "https://vocabs.dariah.eu/tadirah/namingConvention"
        ],
        "researchDomains": [
          "https://w3id.org/nwo-research-fields#HistoryofScience"
        ],
        "informationTypes": [
          "1.22 Statistics",
          "2.8 Numeric data"
        ],
        "mediaTypes": [
          "1.997 vnd.svd"
        ],
        "status": [],
        "languages": [],
        "access": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "versions": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "programmingLanguages": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "standards": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "provenance": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "sourceCodeLocation": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "learn": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "community": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "resourceHost": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "resourceOwner": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "development": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "funding": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "generalContact": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "researchContact": [
          {
            "title": "string",
            "link": "url"
          }
        ],
        "problemContact": [
          {
            "title": "string",
            "link": "url"
          }
        ]
      }
    }
  }
]
```

#### Update

The update operation actually patches the document. So you only have to send the document properties that contain changes.

```JSON
[
  {
    "operation": "update",
    "document": {
      "id": "456",
      "title": "Change the title",
      "media": {
        "thumbnail": "https://picsum.photos/800/600.webp",
        "slider": [
          "https://picsum.photos/800/600.webp",
          "https://vimeo.com/538016781",
        ],
      }
    }
  }
]
```

#### Delete

Only the `id` is needed to delete a resource.

```JSON
[
  {
    "operation": "delete",
    "document": {
      "id": "789"
    }
  }
]
```

### Properties

| Name  | Value                                   |
| ----- | --------------------------------------- |
| link  | Url to the website of the resource.     |
| intro | A short description about the resource. |

| Name                 | Value                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| resourceTypes        | "Not yet available" or an array of `title` (Tools)                                                      |
| researchActivities   | "Not yet available" or an array of `link` ("https://vocabs.dariah.eu/tadirah/namingConvention")         |
| researchDomains      | "Not yet available" or an array of `link` ("https://w3id.org/nwo-research-fields#HistoryofScience")     |
| informationTypes     | "Not yet available" or an array of `index title` ("1.22 Statistics")                                    |
| mediaTypes           | "Not yet available" or an array of `index title` ("1.74 ecmascript")                                    |
| status               | "Not yet available" or an array of `title` ("Active")                                                   |
| languages            | "Not yet available" or an array of `title` ("Dutch")                                                    |
| access               | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| versions             | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| programmingLanguages | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| standards            | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| provenance           | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| sourceCodeLocation   | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |

Links
| Name | Value |
| -------------------- | ----- |
| learn | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| community | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |

Acknowledgements
| Name | Value |
| -------------------- | ----- |
| resourceHost | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| resourceOwner | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| development | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| funding | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |

Contact
| Name | Value |
| -------------------- | ----- |
| generalContact | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| researchContact | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |
| problemContact | an array of objects containing the title and otionally a url `[ { "title": "string", "link": "url" } ]` |

### Response

Each `POST` responds with an object containing the url that can be used to poll its status:

```JSON
{
  "url": "http://localhost:5001/transaction/4c3b8bb1-7b32-49c5-8f06-91f631b1473b"
}
```

#### 100

While the job queue is in progress the url will return `null` with http status code response code `100 Continue`.

#### 200

Each request consists of a single transaction, so either all of its operations succeed or they all fail. Upon success the http status response code is `200 OK`. The response body contains a summary of the transaction:

```JSON
{
  "transactionId": "QNqHkAlGW14Qk9SrSjrqcy",
  "results": [
    { "id": "123", "operation": "create" },
    { "id": "456", "operation": "update"}
    { "id": "789", "operation": "delete"}
  ],
  "documentIds": ["123", "456", "789"]
}
```

#### 500

When the transaction fails the http status response code is `500 Internal Server Error`. The response body contains a description of the error(s):

```JSON
{
  "description": "Mutation(s) failed with 1 error(s)",
  "items": [
    {
      "error": {
        "description": "Document by ID \"123\" already exists",
        "id": "123",
        "type": "documentAlreadyExistsError"
      },
      "index": 2
    }
  ],
  "type": "mutationError"
}
```
