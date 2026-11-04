import { z } from "zod";
import type { PexelsClient } from "../http/client.js";
import { defineTool, type ToolDefinition } from "../types/tool.js";
import type {
  GetVideoResponse,
  PopularVideosResponse,
  VideosSearchResponse,
} from "../types/videos.js";

const orientationSchema = z.enum(["landscape", "portrait", "square"]);
const sizeSchema = z.enum(["large", "medium", "small"]);

const localeSchema = z.enum([
  "en-US",
  "pt-BR",
  "es-ES",
  "ca-ES",
  "de-DE",
  "it-IT",
  "fr-FR",
  "sv-SE",
  "id-ID",
  "pl-PL",
  "ja-JP",
  "zh-TW",
  "zh-CN",
  "ko-KR",
  "th-TH",
  "nl-NL",
  "hu-HU",
  "vi-VN",
  "cs-CZ",
  "da-DK",
  "fi-FI",
  "uk-UA",
  "el-GR",
  "ro-RO",
  "nb-NO",
  "sk-SK",
  "tr-TR",
  "ru-RU",
]);

const pageSchema = z.number().int().min(1).optional();
const perPageSchema = z.number().int().min(1).max(80).optional();
const positiveIntSchema = z.number().int().min(1).optional();

const searchVideosInput = z.object({
  query: z.string().min(1),
  orientation: orientationSchema.optional(),
  size: sizeSchema.optional(),
  locale: localeSchema.optional(),
  page: pageSchema,
  per_page: perPageSchema,
});

const popularVideosInput = z.object({
  min_width: positiveIntSchema,
  min_height: positiveIntSchema,
  min_duration: positiveIntSchema,
  max_duration: positiveIntSchema,
  page: pageSchema,
  per_page: perPageSchema,
});

const getVideoInput = z.object({
  id: z.number().int().min(1),
});

export const videoTools = (client: PexelsClient): ToolDefinition[] => [
  defineTool({
    name: "pexels_search_videos",
    description: "Search Pexels videos by query with optional filters.",
    input: searchVideosInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<VideosSearchResponse>(
        "/v1/videos/search",
        {
          query: input.query,
          orientation: input.orientation,
          size: input.size,
          locale: input.locale,
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_popular_videos",
    description: "Fetch the current popular Pexels videos.",
    input: popularVideosInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<PopularVideosResponse>(
        "/v1/videos/popular",
        {
          min_width: input.min_width,
          min_height: input.min_height,
          min_duration: input.min_duration,
          max_duration: input.max_duration,
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_get_video",
    description: "Retrieve a single Pexels video by its id.",
    input: getVideoInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<GetVideoResponse>(
        `/v1/videos/videos/${input.id}`,
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
];
