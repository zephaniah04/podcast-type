# `pexels_my_collections`

List collections that belong to the **authenticated user** (i.e. the account whose API key is in `.env`). Collections can be created and managed on the Pexels website or mobile apps — this endpoint is read-only.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/collections`
- **Docs:** <https://www.pexels.com/api/documentation/#collections-all>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{ "per_page": 10 }
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
  "per_page": 10,
  "total_results": 5,
  "next_page": null,
  "_rateLimit": { "limit": 20000, "remaining": 19677, "reset": 1590529646 }
}
```

Use the returned `id` with [`pexels_collection_media`](./pexels_collection_media.md) to fetch the photos and videos inside one of your collections.

## Errors

- **`per_page > 80`** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError`.
