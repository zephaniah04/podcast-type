# `pexels_collection_media`

Retrieve all the media (photos **and** videos) within a single Pexels collection. Filter by media type and choose ascending or descending order.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/collections/:id`
- **Docs:** <https://www.pexels.com/api/documentation/#collections-media>

The collection must be either featured or owned by the authenticated user — private collections of other users cannot be accessed.

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `id` | string (min length 1) | ✅ | Collection id (Pexels uses short alphanumeric ids like `9mp14cx`). |
| `type` | enum | — | Filter media type. One of `photos`, `videos`. Omit (or pass invalid value) to receive both. |
| `sort` | enum | — | Order of items. `asc` (default on the Pexels side) or `desc`. |
| `page` | integer ≥ 1 | — | Page number. Default `1`. |
| `per_page` | integer 1–80 | — | Results per page. Default `15`, max `80`. |

## Example input

```json
{
  "id": "9mp14cx",
  "type": "photos",
  "sort": "desc",
  "per_page": 2
}
```

## Example output

Each item in `media` carries a `type` discriminator (`"Photo"` or `"Video"`) so consumers can branch on it.

```json
{
  "id": "9mp14cx",
  "media": [
    {
      "type": "Photo",
      "id": 2061057,
      "width": 4850,
      "height": 3224,
      "url": "https://www.pexels.com/photo/gray-and-white-kitten-on-white-bed-2061057/",
      "photographer": "Tranmautritam",
      "photographer_url": "https://www.pexels.com/@tranmautritam",
      "photographer_id": 8509,
      "avg_color": "#BBBEC3",
      "src": { "original": "...", "large": "...", "medium": "...", "small": "...", "portrait": "...", "landscape": "...", "tiny": "..." },
      "liked": false
    },
    {
      "type": "Video",
      "id": 854982,
      "width": 1280,
      "height": 720,
      "duration": 11,
      "url": "https://www.pexels.com/video/video-of-a-tabby-cat-854982/",
      "image": "...",
      "user": { "id": 2659, "name": "Pixabay", "url": "https://www.pexels.com/@pixabay" },
      "video_files": [
        { "id": 17755, "quality": "hd", "file_type": "video/mp4", "width": 1280, "height": 720, "link": "..." }
      ],
      "video_pictures": [{ "id": 19591, "nr": 0, "picture": "..." }]
    }
  ],
  "page": 1,
  "per_page": 2,
  "total_results": 6,
  "next_page": "https://api.pexels.com/v1/collections/9mp14cx/?page=2&per_page=2",
  "_rateLimit": { "limit": 20000, "remaining": 19676, "reset": 1590529646 }
}
```

## Errors

- **Missing `id`** → Zod validation error.
- **Invalid `type`** (anything other than `photos` / `videos`) → Zod validation error.
- **Invalid `sort`** (anything other than `asc` / `desc`) → Zod validation error.
- **`per_page > 80`** → Zod validation error.
- **Unknown / inaccessible collection id** → `PexelsApiError` with `status: 404`.
