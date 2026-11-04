# `pexels_get_video`

Retrieve a single video by its Pexels id.

- **Pexels endpoint:** `GET https://api.pexels.com/v1/videos/videos/:id` (the duplicated `videos/` segment is per the official documentation).
- **Docs:** <https://www.pexels.com/api/documentation/#videos-show>

## Input parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `id` | integer ≥ 1 | ✅ | The Pexels video id. |

## Example input

```json
{ "id": 2499611 }
```

## Example output

```json
{
  "id": 2499611,
  "width": 1080,
  "height": 1920,
  "url": "https://www.pexels.com/video/2499611/",
  "image": "https://images.pexels.com/videos/2499611/free-video-2499611.jpg?...",
  "duration": 22,
  "user": { "id": 680589, "name": "Joey Farina", "url": "https://www.pexels.com/@joey" },
  "video_files": [
    { "id": 125004, "quality": "hd", "file_type": "video/mp4", "width": 1080, "height": 1920, "fps": 23.976, "link": "..." },
    { "id": 125005, "quality": "sd", "file_type": "video/mp4", "width": 540, "height": 960, "fps": 23.976, "link": "..." }
  ],
  "video_pictures": [
    { "id": 308178, "picture": "https://static-videos.pexels.com/videos/2499611/pictures/preview-0.jpg", "nr": 0 }
  ],
  "_rateLimit": { "limit": 20000, "remaining": 19679, "reset": 1590529646 }
}
```

## Errors

- **Missing or non-integer `id`** → Zod validation error.
- **`id < 1`** → Zod validation error.
- **Unknown id** → `PexelsApiError` with `status: 404`.
