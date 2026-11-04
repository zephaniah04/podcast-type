import { PexelsApiError, type PexelsResponse, type RateLimit } from "./types.js";

export type FetchImpl = typeof fetch;

export interface PexelsClientOptions {
  apiKey: string;
  baseUrl?: string;
  fetchImpl?: FetchImpl;
}

export type QueryParams = Record<string, string | number | undefined>;

const DEFAULT_BASE_URL = "https://api.pexels.com";

function parseIntOrNull(value: string | null): number | null {
  if (value === null) return null;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : null;
}

function extractRateLimit(headers: Headers): RateLimit {
  return {
    limit: parseIntOrNull(headers.get("X-Ratelimit-Limit")),
    remaining: parseIntOrNull(headers.get("X-Ratelimit-Remaining")),
    reset: parseIntOrNull(headers.get("X-Ratelimit-Reset")),
  };
}

function buildUrl(baseUrl: string, path: string, params?: QueryParams): URL {
  const url = new URL(path, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url;
}

export class PexelsClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchImpl;

  constructor(opts: PexelsClientOptions) {
    this.apiKey = opts.apiKey;
    this.baseUrl = opts.baseUrl ?? DEFAULT_BASE_URL;
    this.fetchImpl = opts.fetchImpl ?? globalThis.fetch.bind(globalThis);
  }

  async get<T>(path: string, params?: QueryParams): Promise<PexelsResponse<T>> {
    const url = buildUrl(this.baseUrl, path.replace(/^\//, ""), params);
    const res = await this.fetchImpl(url.toString(), {
      method: "GET",
      headers: {
        Authorization: this.apiKey,
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new PexelsApiError(res.status, body);
    }

    const data = (await res.json()) as T;
    return { data, rateLimit: extractRateLimit(res.headers) };
  }
}
