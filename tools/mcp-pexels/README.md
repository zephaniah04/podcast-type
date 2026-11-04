# mcp-pexels — Pexels MCP server for Claude, Cursor, and other AI agents

[![npm version](https://img.shields.io/npm/v/mcp-pexels.svg)](https://www.npmjs.com/package/mcp-pexels)
[![npm downloads](https://img.shields.io/npm/dm/mcp-pexels.svg)](https://www.npmjs.com/package/mcp-pexels)
[![CI](https://github.com/developer-ishan/mcp-pexels/actions/workflows/ci.yml/badge.svg)](https://github.com/developer-ishan/mcp-pexels/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Node ≥20](https://img.shields.io/badge/node-%E2%89%A520-brightgreen.svg)](#requirements)
[![MCP compatible](https://img.shields.io/badge/MCP-1.0-blue)](https://modelcontextprotocol.io)

**A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes the [Pexels API](https://www.pexels.com/api/) — free stock photos, videos, and curated collections — as MCP tools that any compatible AI client (Claude Desktop, Claude Code, Cursor, Cline, Continue, etc.) can call directly from a chat.**

📦 **npm:** [mcp-pexels](https://www.npmjs.com/package/mcp-pexels) · 🏷 **Latest release:** [v1.0.0](https://github.com/developer-ishan/mcp-pexels/releases/tag/v1.0.0) · 💻 **Source:** [developer-ishan/mcp-pexels](https://github.com/developer-ishan/mcp-pexels)

> Photos & videos provided by [Pexels](https://www.pexels.com).

## Drop-in config

```json
{
  "mcpServers": {
    "pexels": {
      "command": "npx",
      "args": ["-y", "mcp-pexels"],
      "env": { "PEXELS_API_KEY": "your_key_here" }
    }
  }
}
```

Paste into your MCP client's config, restart, and the nine `pexels_*` tools are live. Get a free key at <https://www.pexels.com/api/>.

---

## Table of contents

- [What can you build with this?](#what-can-you-build-with-this)
- [Capabilities — nine tools](#capabilities--nine-tools)
- [Connect to your MCP client](#connect-to-your-mcp-client)
  - [Claude Desktop](#claude-desktop)
  - [Claude Code](#claude-code)
  - [Cursor](#cursor)
  - [Cline (VS Code)](#cline-vs-code)
  - [Continue.dev](#continuedev)
  - [Generic / other clients](#generic--other-clients)
- [Example prompts](#example-prompts)
- [How it compares](#how-it-compares)
- [FAQ](#faq)
- [Requirements](#requirements)
- [Development](#development)
- [Releasing](#releasing)
- [Contributing](#contributing)
- [Attribution & License](#attribution--license)

---

## What can you build with this?

Once `mcp-pexels` is connected to an AI client, the agent can pull royalty-free photos and videos straight into its workflow. A few concrete uses:

- **Slide-deck and document illustration** — "Find me a landscape photo of mountains at sunset for slide 3" → the agent searches Pexels, picks one, and embeds it.
- **Blog post / social media drafting** — "Suggest three thumbnail options for an article about remote work" → returns three Pexels URLs with photographer credit.
- **Background research for video editing** — "Show me popular drone footage under 30 seconds in 4K" → uses `pexels_popular_videos` with size and duration filters.
- **Mood boards** — "Build me a mood board of warm-toned coffee shop photos" → searches with `color: "orange"`.
- **Coding agents** — generate CSS/HTML with realistic placeholder imagery instead of `lorem-pixel` boxes.
- **Curated collections** — pull a specific Pexels collection (e.g. company-owned shots tagged on Pexels) into the agent's context.

Because every response includes a `_rateLimit` object, the agent can self-throttle and respect the Pexels free-tier quota (200 req/hour, 20 000/month).

---

## Capabilities — nine tools

| Domain | Tool | What it does |
|---|---|---|
| Photos | [`pexels_search_photos`](./docs/tools/pexels_search_photos.md) | Search photos by query with orientation / size / color / locale filters. |
| Photos | [`pexels_curated_photos`](./docs/tools/pexels_curated_photos.md) | Fetch the Pexels team's real-time curated photo feed. |
| Photos | [`pexels_get_photo`](./docs/tools/pexels_get_photo.md) | Retrieve a single photo by its numeric id. |
| Videos | [`pexels_search_videos`](./docs/tools/pexels_search_videos.md) | Search videos by query with orientation / size / locale filters. |
| Videos | [`pexels_popular_videos`](./docs/tools/pexels_popular_videos.md) | Fetch popular videos with optional width / height / duration constraints. |
| Videos | [`pexels_get_video`](./docs/tools/pexels_get_video.md) | Retrieve a single video by its numeric id. |
| Collections | [`pexels_featured_collections`](./docs/tools/pexels_featured_collections.md) | List Pexels featured collections. |
| Collections | [`pexels_my_collections`](./docs/tools/pexels_my_collections.md) | List the authenticated user's own collections. |
| Collections | [`pexels_collection_media`](./docs/tools/pexels_collection_media.md) | Retrieve the photos and videos inside a specific collection. |

Each tool response is the raw Pexels JSON merged with a top-level `_rateLimit` field exposing `limit`, `remaining`, and `reset` (UNIX timestamp).

See [`docs/tools/`](docs/tools/) for per-tool parameter tables and example payloads.

---

## Connect to your MCP client

All paths below use `npx -y mcp-pexels` — no global install required. Replace `your_key_here` with a real Pexels API key.

### Claude Desktop

**Option 1 — one-click `.mcpb` install (recommended).** Download the latest `mcp-pexels-*.mcpb` from the [Releases page](https://github.com/developer-ishan/mcp-pexels/releases/latest), double-click the file, paste your Pexels API key when Claude Desktop prompts, and click Install.

**Option 2 — manual JSON config.** Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pexels": {
      "command": "npx",
      "args": ["-y", "mcp-pexels"],
      "env": { "PEXELS_API_KEY": "your_key_here" }
    }
  }
}
```

Restart Claude Desktop.

### Claude Code

```bash
claude mcp add pexels -e PEXELS_API_KEY=your_key_here -- npx -y mcp-pexels
```

Or edit `~/.claude.json` directly and add the same `mcpServers` block as above.

### Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "pexels": {
      "command": "npx",
      "args": ["-y", "mcp-pexels"],
      "env": { "PEXELS_API_KEY": "your_key_here" }
    }
  }
}
```

### Cline (VS Code)

Open the Cline extension settings → **MCP Servers** → **Edit Settings**. Add:

```json
{
  "mcpServers": {
    "pexels": {
      "command": "npx",
      "args": ["-y", "mcp-pexels"],
      "env": { "PEXELS_API_KEY": "your_key_here" }
    }
  }
}
```

### Continue.dev

In `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "mcp-pexels"],
          "env": { "PEXELS_API_KEY": "your_key_here" }
        }
      }
    ]
  }
}
```

### Generic / other clients

If your client supports stdio MCP servers it just needs `command`, `args`, and `env`. Use the same shape as Cursor / Claude Desktop above. For inspector / debugging:

```bash
export PEXELS_API_KEY=your_key_here
npx -y @modelcontextprotocol/inspector npx -y mcp-pexels
```

This opens a browser UI where you can call each tool interactively.

---

## Example prompts

Once connected, try prompts like:

- *"Find me five landscape photos of mountains at golden hour. Make sure they're at least full HD."*
- *"Get me popular Pexels videos shorter than 15 seconds, 1080p or higher, of city traffic."*
- *"Pull photo id 2014422 and tell me the photographer."*
- *"List the featured Pexels collections — I want one I can browse for cooking photos."*
- *"Search videos of 'forest' in portrait orientation; pick the highest-quality HD file for me."*
- *"Show me Pexels photos with predominantly orange tones suitable for a fall-themed newsletter header."*

The agent will pick the appropriate tool, send the right parameters, and include photographer/videographer credit as part of its answer.

---

## How it compares

| | mcp-pexels | Raw Pexels REST API | Image-only general MCP servers |
|---|---|---|---|
| Photos | ✅ | ✅ | varies |
| Videos | ✅ | ✅ | usually ❌ |
| Collections | ✅ | ✅ | ❌ |
| Rate-limit headers exposed to agent | ✅ | ❌ (raw headers, agent must parse) | ❌ |
| Zod-validated input | ✅ | ❌ | varies |
| `npx`-installable, zero config | ✅ | ❌ | varies |
| Type-safe TS source | ✅ | n/a | varies |
| MIT-licensed | ✅ | n/a | varies |

If you only need photos and you already have a generic image MCP server wired up, that may be enough. If you want first-class video and collection support with rate-limit awareness, this is purpose-built for it.

---

## FAQ

### How do I get a Pexels API key?

Sign up at <https://www.pexels.com/api/> — keys are issued instantly and the free tier allows **200 requests/hour** and **20 000 requests/month**.

### Does this cost anything?

No. The Pexels API is free, the npm package is free (MIT), and `mcp-pexels` itself does not call any paid service.

### Will this work offline?

No — the server is a thin wrapper over the Pexels HTTPS API and requires network access.

### Can I use Pexels content commercially?

Yes, per the Pexels license, but you must attribute the platform and (when possible) the photographer. See [Attribution](#attribution--license).

### Does it work with Claude.ai (browser)?

Claude.ai's web product doesn't yet support stdio MCP servers — only Claude Desktop, Claude Code, and the API do. Anthropic is rolling out browser MCP support, so this should change.

### Is there a hosted / SaaS version?

No. Run it locally via `npx`. Because Pexels API keys are per-user, hosting a shared instance doesn't make sense.

### How do I update to a newer version?

`npx` always fetches the latest published version. If you've installed globally, run `npm update -g mcp-pexels`.

### Can I add more Pexels endpoints?

The Pexels API surface is fully implemented (9/9 endpoints as of Pexels API v1). New endpoints will be added via PR — see [Contributing](#contributing).

### Does it work with `@modelcontextprotocol/inspector`?

Yes:

```bash
export PEXELS_API_KEY=your_key_here
npx -y @modelcontextprotocol/inspector npx -y mcp-pexels
```

### How is rate limiting handled?

Every tool response includes a `_rateLimit` object with `limit`, `remaining`, and `reset` (UNIX timestamp). The agent can read this and self-throttle. If Pexels returns 429, the server surfaces it as a `PexelsApiError` so the agent sees the failure.

### Where does my API key go?

It is read from the `PEXELS_API_KEY` env var on the local process. It never leaves your machine except in `Authorization` headers to `api.pexels.com`. Nothing is logged.

---

## Requirements

- Node.js **≥ 20** (uses native `fetch` and `--env-file`)
- A free Pexels API key — [request one here](https://www.pexels.com/api/)

---

## Development

```bash
git clone https://github.com/developer-ishan/mcp-pexels.git
cd mcp-pexels
npm install
echo "PEXELS_API_KEY=your_key_here" > .env

npm test           # 42 mocked vitest cases, no network
npm run build      # tsc → dist/
npm run dev        # tsx watch
npm run test:watch # vitest in watch mode
npm start          # node --env-file=.env dist/index.js
```

### Project layout

```
src/
├── index.ts                  # MCP server entrypoint (stdio)
├── http/
│   ├── client.ts             # PexelsClient (injectable fetch for tests)
│   └── types.ts              # PexelsApiError, RateLimit, PexelsResponse
├── tools/
│   ├── index.ts              # composes the three domain factories
│   ├── photos.ts             # 3 photo tools
│   ├── videos.ts             # 3 video tools
│   └── collections.ts        # 3 collection tools
└── types/
    ├── tool.ts               # defineTool helper + ToolDefinition
    ├── photos.ts
    ├── videos.ts
    └── collections.ts

tests/
├── helpers/mockClient.ts     # makeMockClient() — fake fetch via vitest mocks
├── photos.test.ts            # 17 cases
├── videos.test.ts            # 13 cases
└── collections.test.ts       # 12 cases
```

### Testing approach

Tests construct a `PexelsClient` with a `vi.fn()` `fetchImpl` returned by `makeMockClient(responses)`. No real HTTP is performed. Each tool is exercised for:

1. **Happy path** — URL serialization and `Authorization` header.
2. **Error mapping** — non-2xx → `PexelsApiError` with `status` and `body`.
3. **Zod validation** — required params, enum membership, integer bounds.

---

## Releasing

This repo uses a tag-driven release workflow (`.github/workflows/release.yml`):

1. Bump the version: `npm version patch` (or `minor` / `major`) — creates a commit and tag.
2. Push: `git push && git push --tags`.
3. The workflow runs tests, builds, publishes to npm with provenance using the `NPM_TOKEN` repository secret, builds the **`.mcpb` bundle** via `npm run pack:mcpb`, and creates a GitHub release with auto-generated notes that includes the bundle as a downloadable asset.

See [`CHANGELOG.md`](./CHANGELOG.md) for version history.

---

## Contributing

Issues and pull requests welcome. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the development workflow and [`SECURITY.md`](./SECURITY.md) to report a vulnerability privately.

If you ship `mcp-pexels` inside a tool or product, open a PR adding it to the "Used by" list in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

### Listed on / submit to

- **[Smithery](https://smithery.ai/)** — auto-discovered via [`smithery.yaml`](./smithery.yaml).
- **[mcp.so](https://mcp.so)** — community directory.
- **[awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)** — curated GitHub list.
- **[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)** — Anthropic's official directory.

See [`docs/MARKETPLACES.md`](./docs/MARKETPLACES.md) for the submission cheatsheet.

---

## Attribution & License

When you use Pexels content, please follow the [Pexels API guidelines](https://www.pexels.com/api/documentation/#guidelines):

- Show a prominent link to Pexels — e.g. *"Photos provided by Pexels"*.
- Credit photographers/videographers when possible — e.g. *"Photo by John Doe on Pexels"*.

The `mcp-pexels` package itself is released under the [MIT License](./LICENSE).
