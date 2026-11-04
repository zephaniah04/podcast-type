import type { PexelsClient } from "../http/client.js";
import type { ToolDefinition } from "../types/tool.js";
import { photoTools } from "./photos.js";
import { videoTools } from "./videos.js";
import { collectionTools } from "./collections.js";

export function allTools(client: PexelsClient): ToolDefinition[] {
  return [...photoTools(client), ...videoTools(client), ...collectionTools(client)];
}
