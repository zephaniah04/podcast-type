#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { PexelsClient } from "./http/client.js";
import { PexelsApiError } from "./http/types.js";
import { allTools } from "./tools/index.js";

const pkg = JSON.parse(
  readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "..", "package.json"),
    "utf8",
  ),
) as { name: string; version: string };

const apiKey = process.env.PEXELS_API_KEY;
if (!apiKey) {
  console.error(
    "PEXELS_API_KEY env var is required. Set it in .env or your shell.",
  );
  process.exit(1);
}

const client = new PexelsClient({ apiKey });
const tools = allTools(client);
const toolsByName = new Map(tools.map((t) => [t.name, t]));

const server = new Server(
  { name: pkg.name, version: pkg.version },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: tools.map((t) => ({
    name: t.name,
    description: t.description,
    inputSchema: t.inputJsonSchema,
  })),
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const tool = toolsByName.get(req.params.name);
  if (!tool) {
    return {
      isError: true,
      content: [{ type: "text", text: `Unknown tool: ${req.params.name}` }],
    };
  }

  try {
    const args = tool.inputSchema.parse(req.params.arguments ?? {});
    const result = await tool.handler(args);
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  } catch (err) {
    const message =
      err instanceof PexelsApiError
        ? err.message
        : err instanceof Error
          ? err.message
          : String(err);
    return {
      isError: true,
      content: [{ type: "text", text: message }],
    };
  }
});

await server.connect(new StdioServerTransport());
