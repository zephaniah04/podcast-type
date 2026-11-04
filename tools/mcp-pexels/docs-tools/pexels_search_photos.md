# `pexels_search_photos`

Search the full Pexels photo library by free-text query, with optional filters for orientation, size, color, and locale.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/search`
- **Docs:** <https://www.pexels.com/api/documentation/#photos-search>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `query` | string (min length 1) | ✅ | Search term. Examples: `Ocean`, `Tigers`, `Group of people working`. |
| `orientation` | enum | — | One of `landscape`, `portrait`, `square`. |
| `size` | enum | — | Minimum photo size. `large` (24 MP), `medium` (12 MP), `small` (4 MP). |
| `color` | enum or hex string | — | Named color (`red`, `orange`, `yellow`, `green`, `turquoise`, `blue`, `violet`, `pink`, `brown`, `black`, `gray`, `white`) **or** a 6-digit hex code like `#ff0000`. |
| `locale` | enum | — | Locale of the search. 28 supported values: `en-US`, `pt-BR`, `es-ES`, `ca-ES`, `de-DE`, `it-IT`, `fr-FR`, `sv-SE`, `id-ID`, `pl-PL`, `ja-JP`, `zh-TW`, `zh-CN`, `ko-KR`, `th-TH`, `nl-NL`, `hu-HU`, `vi-VN`, `cs-CZ`, `da-DK`, `fi-FI`, `uk-UA`, `el-GR`, `ro-RO`, `nb-NO`, `sk-SK`, `tr-TR`, `ru-RU`. |
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{
  "query": "ocean sunset",
  "orientation": "landscape",
  "color": "orange",
  "per_page": 3
}
```

## Example output

```json
{
  "page": 1,
  "per_page": 3,
  "total_results": 10000,
  "photos": [
    {
      "id": 3573351,
      "width": 3066,
      "height": 3968,
      "url": "https://www.pexels.com/photo/trees-during-day-3573351/",
      "photographer": "Lukas Rodriguez",
      "photographer_url": "https://www.pexels.com/@lukas-rodriguez-1845331",
      "photographer_id": 1845331,
      "avg_color": "#374824",
      "src": {
        "original": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png",
        "large": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?...&h=650&w=940",
        "medium": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?...&h=350",
        "small": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?...&h=130",
        "portrait": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?...",
        "landscape": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?...",
        "tiny": "https://images.pexels.com/photos/3573351/pexels-photo-3573351.png?..."
      },
      "liked": false,
      "alt": "Brown Rocks During Golden Hour"
    }
  ],
  "next_page": "https://api.pexels.com/v1/search/?page=2&per_page=3&query=ocean+sunset",
  "_rateLimit": { "limit": 20000, "remaining": 19684, "reset": 1590529646 }
}
```

## Errors

- **Missing `query`** → Zod validation error before any HTTP call.
- **`per_page > 80`** → Zod validation error.
- **`color` not in the named set and not a `#rrggbb` hex** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError` with `status` + raw body.
