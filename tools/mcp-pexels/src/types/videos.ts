export interface VideoUser {
  id: number;
  name: string;
  url: string;
}

export interface VideoFile {
  id: number;
  quality: "hd" | "sd" | "hls";
  file_type: string;
  width: number | null;
  height: number | null;
  fps?: number;
  link: string;
}

export interface VideoPicture {
  id: number;
  picture: string;
  nr: number;
}

export interface Video {
  id: number;
  width: number;
  height: number;
  url: string;
  image: string;
  duration: number;
  user: VideoUser;
  video_files: VideoFile[];
  video_pictures: VideoPicture[];
  full_res?: string | null;
  tags?: string[];
}

export interface VideosSearchResponse {
  videos: Video[];
  url: string;
  page: number;
  per_page: number;
  total_results: number;
  next_page?: string;
  prev_page?: string;
}

export type PopularVideosResponse = VideosSearchResponse;

export type GetVideoResponse = Video;
