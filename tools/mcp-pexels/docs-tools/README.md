# Tool Reference

Detailed documentation for every MCP tool exposed by `mcp-pexels`. Each tool wraps a single Pexels API endpoint.

Every tool response includes a top-level `_rateLimit` field:

```json
{
  "_rateLimit": {
    "limit": 20000,
    "remaining": 19684,
    "reset": 1590529646
  }
}
```

`reset` is a UNIX timestamp marking when the monthly quota rolls over.

## Photos

- [`pexels_search_photos`](./pexels_search_photos.md) — search photos by query with optional filters.
- [`pexels_curated_photos`](./pexels_curated_photos.md) — real-time list of photos curated by the Pexels team.
- [`pexels_get_photo`](./pexels_get_photo.md) — fetch a single photo by id.

## Videos

- [`pexels_search_videos`](./pexels_search_videos.md) — search videos by query with optional filters.
- [`pexels_popular_videos`](./pexels_popular_videos.md) — current popular videos with size/duration filters.
- [`pexels_get_video`](./pexels_get_video.md) — fetch a single video by id.

## Collections

- [`pexels_featured_collections`](./pexels_featured_collections.md) — Pexels-curated featured collections.
- [`pexels_my_collections`](./pexels_my_collections.md) — collections belonging to the authenticated user.
- [`pexels_collection_media`](./pexels_collection_media.md) — photos & videos inside a specific collection.

## Common error shape

All tools throw `PexelsApiError` on non-2xx responses. The MCP server translates this into a tool error:

```json
{
  "isError": true,
  "content": [{ "type": "text", "text": "Pexels API error 404: { \"error\": \"Not Found\" }" }]
}
```

Zod validation errors (missing required params, out-of-range values) are surfaced the same way before any HTTP call is made.
