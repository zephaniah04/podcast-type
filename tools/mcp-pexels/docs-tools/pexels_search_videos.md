# `pexels_search_videos`

Search the full Pexels video library by free-text query, with optional filters for orientation, size, and locale.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/videos/search`
- **Docs:** <https://www.pexels.com/api/documentation/#videos-search>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `query` | string (min length 1) | ✅ | Search term. Examples: `Nature`, `Tigers`, `Group of people working`. |
| `orientation` | enum | — | One of `landscape`, `portrait`, `square`. |
| `size` | enum | — | Minimum video size. `large` (4K), `medium` (Full HD), `small` (HD). |
| `locale` | enum | — | Locale of the search. Same 28 values as `pexels_search_photos`. |
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{
  "query": "forest",
  "orientation": "landscape",
  "size": "medium",
  "per_page": 3
}
```

## Example output

```json
{
  "page": 1,
  "per_page": 3,
  "total_results": 20475,
  "url": "https://www.pexels.com/videos/",
  "videos": [
    {
      "id": 1448735,
      "width": 4096,
      "height": 2160,
      "url": "https://www.pexels.com/video/video-of-forest-1448735/",
      "image": "https://images.pexels.com/videos/1448735/free-video-1448735.jpg?...",
      "duration": 32,
      "user": { "id": 574687, "name": "Ruvim Miksanskiy", "url": "https://www.pexels.com/@digitech" },
      "video_files": [
        {
          "id": 58650,
          "quality": "hd",
          "file_type": "video/mp4",
          "width": 2048,
          "height": 1080,
          "fps": 23.976,
          "link": "https://player.vimeo.com/external/291648067.hd.mp4?..."
        }
      ],
      "video_pictures": [
        { "id": 133236, "picture": "https://static-videos.pexels.com/videos/1448735/pictures/preview-0.jpg", "nr": 0 }
      ]
    }
  ],
  "_rateLimit": { "limit": 20000, "remaining": 19681, "reset": 1590529646 }
}
```

## Errors

- **Missing `query`** → Zod validation error.
- **`per_page > 80`** → Zod validation error.
- **Invalid `orientation` / `size` / `locale`** → Zod validation error.
- **Non-2xx from Pexels** → `PexelsApiError`.
