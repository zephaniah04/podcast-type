# `pexels_popular_videos`

Fetch the current popular Pexels videos. Filters let you constrain minimum dimensions and duration window.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/videos/popular`
- **Docs:** <https://www.pexels.com/api/documentation/#videos-popular>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `min_width` | integer ≥ 1 | — | Minimum width in pixels. |
| `min_height` | integer ≥ 1 | — | Minimum height in pixels. |
| `min_duration` | integer ≥ 1 | — | Minimum video duration in seconds. |
| `max_duration` | integer ≥ 1 | — | Maximum video duration in seconds. |
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{
  "min_width": 1920,
  "max_duration": 30,
  "per_page": 5
}
```

## Example output

```json
{
  "page": 1,
  "per_page": 5,
  "total_results": 4089,
  "url": "https://www.pexels.com/search/videos/Nature/",
  "videos": [
    {
      "id": 1093662,
      "width": 1920,
      "height": 1080,
      "url": "https://www.pexels.com/video/water-crashing-over-the-rocks-1093662/",
      "image": "https://images.pexels.com/videos/1093662/free-video-1093662.jpg?...",
      "duration": 8,
      "user": { "id": 417939, "name": "Peter Fowler", "url": "https://www.pexels.com/@peter-fowler-417939" },
      "video_files": [
        { "id": 37103, "quality": "hd", "file_type": "video/mp4", "width": 1920, "height": 1080, "link": "..." }
      ],
      "video_pictures": [
        { "id": 79696, "picture": "...", "nr": 0 }
      ]
    }
  ],
  "_rateLimit": { "limit": 20000, "remaining": 19680, "reset": 1590529646 }
}
```

## Errors

- **`min_*` or `max_duration < 1`** → Zod validation error.
- **`per_page > 80`** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError`.
