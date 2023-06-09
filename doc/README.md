# Resources api

The api is available at https://ineo-resources-api-5b568b0ad6eb.herokuapp.com.

## Authorization

All requests need the "Authorization header". For example:

`curl 'https://ineo-resources-api-5b568b0ad6eb.herokuapp.com/resources/' -H "Authorization: bearer $INEO_RESOURCES_API_TOKEN"`

## Use GET to request resources

When the http request method is `GET` you can request resources. This is an optional catch all route. So you can either fetch all resources at the base endpoint, or specific resources by specifying their id's in subsequent path segments.

- `/resources` returns all resources;
- `/resources/123` returns resource with id `123`;
- `/resources/123/456` returns resources with id's `123` and `456`.

The response contains the resource(s) as json.

## Use POST to send resources

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
        "researchActivities": [],
        "researchDomains": [],
        "informationTypes": [],
        "mediaTypes": [],
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

| Name                 | Value                                                         |
| -------------------- | ------------------------------------------------------------- |
| resourceTypes        | "Not yet available" or +1 of `/properties/resourceTypes`      |
| researchActivities   | "Not yet available" or +1 of `/properties/researchActivities` |
| researchDomains      | "Not yet available" or +1 of `/properties/researchDomains`    |
| informationTypes     | "Not yet available" or +1 of `/properties/informationTypes`   |
| mediaTypes           | "Not yet available" or +1 of `/properties/mediaTypes`         |
| status               | "Not yet available" or +1 of `/properties/status`             |
| languages            | "Not yet available" or +1 of `/properties/languages`          |
| access               | multiple objects containing a title and optionally a url      |
| versions             | multiple objects containing a title and optionally a url      |
| programmingLanguages | multiple objects containing a title and optionally a url      |
| standards            | multiple objects containing a title and optionally a url      |
| provenance           | multiple objects containing a title and optionally a url      |
| sourceCodeLocation   | multiple objects containing a title and optionally a url      |

Links
| Name | Value |
| -------------------- | ----- |
| learn | multiple objects containing a title and optionally a url |
| community | multiple objects containing a title and optionally a url |

Acknowledgements
| Name | Value |
| -------------------- | ----- |
| resourceHost | multiple objects containing a title and optionally a url |
| resourceOwner | multiple objects containing a title and optionally a url |
| development | multiple objects containing a title and optionally a url |
| funding | multiple objects containing a title and optionally a url |

Contact
| Name | Value |
| -------------------- | ----- |
| generalContact | multiple objects containing a title and optionally a url |
| researchContact | multiple objects containing a title and optionally a url |
| problemContact | multiple objects containing a title and optionally a url |

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
