import { basemap_providers, project_status, project_visibility, tile_output_formats } from '@/types/enums';
import type { Point } from 'geojson';

// PAYLOAD TYPES
export type generateProjectBasemapPayloadType = {
  tile_source: basemap_providers;
  file_format: tile_output_formats;
  tms_url?: string;
};

// PARAMS TYPES
export type projectSummariesParamsType = {
  page: number;
  results_per_page: number;
  org_id?: number;
  user_sub?: string;
  hashtags?: string;
  search?: string;
  minimal?: boolean;
  status?: project_status;
};

// RESPONSE TYPES
export type projectSummaryType = {
  id: number;
  name: string;
  organisation_id: number;
  priority: number;
  hashtags: string[];
  location_str: string;
  short_description: string;
  status: project_status;
  visibility: project_visibility;
  organisation_logo: string | null;
  centroid: Point;
  total_tasks: number;
  num_contributors: number;
  total_submissions: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
};

export type tileType = {
  id: string;
  url: string;
  tile_source: basemap_providers;
  background_task_id: string;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  created_at: string;
  bbox: null;
  format: tile_output_formats;
  mimetype: string;
};
