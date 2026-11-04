# `pexels_curated_photos`

Fetch a real-time, paginated list of photos curated by the Pexels editorial team. Pexels adds at least one new photo per hour, so the feed always reflects current trending content.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/curated`
- **Docs:** <https://www.pexels.com/api/documentation/#photos-curated>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{ "per_page": 5 }
```

## Example output

```json
{
  "page": 1,
  "per_page": 5,
  "photos": [
    {
      "id": 2880507,
      "width": 4000,
      "height": 6000,
      "url": "https://www.pexels.com/photo/woman-in-white-long-sleeved-top-and-skirt-standing-on-field-2880507/",
      "photographer": "Deden Dicky Ramdhani",
      "photographer_url": "https://www.pexels.com/@drdeden88",
      "photographer_id": 1378810,
      "avg_color": "#7E7F7B",
      "src": {
        "original": "https://images.pexels.com/photos/2880507/pexels-photo-2880507.jpeg",
        "large": "...",
        "medium": "...",
        "small": "...",
        "portrait": "...",
        "landscape": "...",
        "tiny": "..."
      },
      "liked": false,
      "alt": "..."
    }
  ],
  "next_page": "https://api.pexels.com/v1/curated/?page=2&per_page=5",
  "_rateLimit": { "limit": 20000, "remaining": 19683, "reset": 1590529646 }
}
```

## Errors

- **`per_page > 80`** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError`.
