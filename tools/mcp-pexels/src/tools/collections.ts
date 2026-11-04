import { z } from "zod";
import type { PexelsClient } from "../http/client.js";
import { defineTool, type ToolDefinition } from "../types/tool.js";
import type {
  CollectionMediaResponse,
  FeaturedCollectionsResponse,
  MyCollectionsResponse,
} from "../types/collections.js";

const pageSchema = z.number().int().min(1).optional();
const perPageSchema = z.number().int().min(1).max(80).optional();

const featuredCollectionsInput = z.object({
  page: pageSchema,
  per_page: perPageSchema,
});

const myCollectionsInput = z.object({
  page: pageSchema,
  per_page: perPageSchema,
});

const collectionMediaInput = z.object({
  id: z.string().min(1),
  type: z.enum(["photos", "videos"]).optional(),
  sort: z.enum(["asc", "desc"]).optional(),
  page: pageSchema,
  per_page: perPageSchema,
});

export const collectionTools = (client: PexelsClient): ToolDefinition[] => [
  defineTool({
    name: "pexels_featured_collections",
    description: "List featured collections on Pexels.",
    input: featuredCollectionsInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<FeaturedCollectionsResponse>(
        "/v1/collections/featured",
        {
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_my_collections",
    description: "List the authenticated user's own Pexels collections.",
    input: myCollectionsInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<MyCollectionsResponse>(
        "/v1/collections",
        {
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_collection_media",
    description: "Retrieve photos and videos within a Pexels collection by id.",
    input: collectionMediaInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<CollectionMediaResponse>(
        `/v1/collections/${input.id}`,
        {
          type: input.type,
          sort: input.sort,
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
];
