# Vendored: developer-ishan/mcp-pexels (MIT)

Source: https://github.com/developer-ishan/mcp-pexels @ 218c9a8 (v1.0.2), copied 2026-11-04, unmodified `src/`.
`dist/index.js` is a single-file esbuild bundle of `src/index.ts` (deps inlined) so the server runs in a fresh
session with only `node`, no `npm install`. Registered for this repo in `/.mcp.json` as `pexels`.

Reviewed: only calls https://api.pexels.com, sends the key only as the Authorization header, no logging, no writes.
Read-only tools: pexels_search_videos, pexels_search_photos, pexels_popular_videos, pexels_curated_photos,
pexels_get_video, pexels_get_photo, pexels_featured_collections, pexels_my_collections, pexels_collection_media.

Rebuild after updating src:
  cd tools/mcp-pexels && npm ci --ignore-scripts && \
  npx -y esbuild@0.24.0 src/index.ts --bundle --platform=node --format=esm --target=node20 --outfile=dist/index.js && \
  rm -rf node_modules
