# `pexels_featured_collections`

List the **featured collections** curated by Pexels. Collections cannot be created or modified through the API — only browsed.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/collections/featured`
- **Docs:** <https://www.pexels.com/api/documentation/#collections-featured>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{ "per_page": 1 }
```

## Example output

```json
{
  "collections": [
    {
      "id": "9mp14cx",
      "title": "Cool Cats",
      "description": null,
      "private": false,
      "media_count": 6,
      "photos_count": 5,
      "videos_count": 1
    }
  ],
  "page": 1,
  "per_page": 1,
  "total_results": 5,
  "next_page": "https://api.pexels.com/v1/collections/featured/?page=2&per_page=1",
  "_rateLimit": { "limit": 20000, "remaining": 19678, "reset": 1590529646 }
}
```

Use the returned `id` with [`pexels_collection_media`](./pexels_collection_media.md) to fetch the photos and videos inside a collection.

## Errors

- **`per_page > 80`** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError`.
