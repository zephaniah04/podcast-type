import { z } from "zod";
import type { PexelsClient } from "../http/client.js";
import { defineTool, type ToolDefinition } from "../types/tool.js";
import type {
  CuratedPhotosResponse,
  GetPhotoResponse,
  PhotosSearchResponse,
} from "../types/photos.js";

const orientationSchema = z.enum(["landscape", "portrait", "square"]);
const sizeSchema = z.enum(["large", "medium", "small"]);

const namedColorSchema = z.enum([
  "red",
  "orange",
  "yellow",
  "green",
  "turquoise",
  "blue",
  "violet",
  "pink",
  "brown",
  "black",
  "gray",
  "white",
]);
const hexColorSchema = z.string().regex(/^#[0-9a-fA-F]{6}$/);
const colorSchema = z.union([namedColorSchema, hexColorSchema]);

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

const searchPhotosInput = z.object({
  query: z.string().min(1),
  orientation: orientationSchema.optional(),
  size: sizeSchema.optional(),
  color: colorSchema.optional(),
  locale: localeSchema.optional(),
  page: pageSchema,
  per_page: perPageSchema,
});

const curatedPhotosInput = z.object({
  page: pageSchema,
  per_page: perPageSchema,
});

const getPhotoInput = z.object({
  id: z.number().int().min(1),
});

export const photoTools = (client: PexelsClient): ToolDefinition[] => [
  defineTool({
    name: "pexels_search_photos",
    description: "Search Pexels photos by query with optional filters.",
    input: searchPhotosInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<PhotosSearchResponse>(
        "/v1/search",
        {
          query: input.query,
          orientation: input.orientation,
          size: input.size,
          color: input.color,
          locale: input.locale,
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_curated_photos",
    description: "Fetch a real-time list of photos curated by the Pexels team.",
    input: curatedPhotosInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<CuratedPhotosResponse>(
        "/v1/curated",
        {
          page: input.page,
          per_page: input.per_page,
        },
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
  defineTool({
    name: "pexels_get_photo",
    description: "Retrieve a single Pexels photo by its id.",
    input: getPhotoInput,
    handler: async (input) => {
      const { data, rateLimit } = await client.get<GetPhotoResponse>(
        `/v1/photos/${input.id}`,
      );
      return { ...data, _rateLimit: rateLimit };
    },
  }),
];
