# `pexels_get_photo`

Retrieve a single photo by its Pexels id.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/photos/:id`
- **Docs:** <https://www.pexels.com/api/documentation/#photos-show>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `id` | integer ≥ 1 | ✅ | The Pexels photo id. |

## Example input

```json
{ "id": 2014422 }
```

## Example output

```json
{
  "id": 2014422,
  "width": 3024,
  "height": 3024,
  "url": "https://www.pexels.com/photo/brown-rocks-during-golden-hour-2014422/",
  "photographer": "Joey Farina",
  "photographer_url": "https://www.pexels.com/@joey",
  "photographer_id": 680589,
  "avg_color": "#978E82",
  "src": {
    "original": "https://images.pexels.com/photos/2014422/pexels-photo-2014422.jpeg",
    "large": "...",
    "medium": "...",
    "small": "...",
    "portrait": "...",
    "landscape": "...",
    "tiny": "..."
  },
  "liked": false,
  "alt": "Brown Rocks During Golden Hour",
  "_rateLimit": { "limit": 20000, "remaining": 19682, "reset": 1590529646 }
}
```

## Errors

- **Missing or non-integer `id`** → Zod validation error.
- **`id < 1`** → Zod validation error.
- **Unknown id** → `PexelsApiError` with `status: 404`.
