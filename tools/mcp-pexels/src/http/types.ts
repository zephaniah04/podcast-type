export interface RateLimit {
  limit: number | null;
  remaining: number | null;
  reset: number | null;
}

export interface PexelsResponse<T> {
  data: T;
  rateLimit: RateLimit;
}

export class PexelsApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
  ) {
    super(`Pexels API error ${status}: ${body}`);
    this.name = "PexelsApiError";
  }
}
