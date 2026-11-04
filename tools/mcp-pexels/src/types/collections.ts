export interface Collection {
  id: string;
  title: string;
  description: string | null;
  private: boolean;
  media_count: number;
  photos_count: number;
  videos_count: number;
}

export interface CollectionsListResponse {
  collections: Collection[];
  page: number;
  per_page: number;
  total_results: number;
  next_page?: string;
  prev_page?: string;
}

export type FeaturedCollectionsResponse = CollectionsListResponse;
export type MyCollectionsResponse = CollectionsListResponse;

export type CollectionMediaItem =
  | ({ type: "Photo" } & Record<string, unknown>)
  | ({ type: "Video" } & Record<string, unknown>);

export interface CollectionMediaResponse {
  id: string;
  media: CollectionMediaItem[];
  page: number;
  per_page: number;
  total_results: number;
  next_page?: string;
  prev_page?: string;
}
