import { project_status, GeoGeomTypesEnum, task_split_type, project_visibility } from '@/types/enums';
import type { BBox, Point, Polygon } from 'geojson';

export type projectInfoType = {
  id: number;
  name: string;
  outline: Polygon;
  odkid: number;
  author_sub: number;
  organisation_id: string;
  short_description: string;
  description: string;
  per_task_instructions: string;
  slug: string;
  task_split_type: task_split_type;
  location_str: string;
  custom_tms_url: string;
  status: string;
  visibility: project_visibility;
  osm_category: string;
  odk_form_id: string;
  odk_form_xml: string;
  mapper_level: string;
  priority: string;
  featured: boolean;
  odk_central_url: string;
  odk_central_user: string;
  odk_token: string;
  data_extract_url: string;
  task_split_dimension: number | null;
  task_num_buildings: number | null;
  primary_geom_type: GeoGeomTypesEnum;
  new_geom_type: GeoGeomTypesEnum;
  geo_restrict_distance_meters: number;
  geo_restrict_force_error: boolean;
  use_odk_collect: boolean;
  hashtags: string[];
  due_date: null | string;
  updated_at: string;
  created_at: string;
  tasks: taskType[];
  organisation_name: string;
  organisation_logo: string | null;
  centroid: Point;
  bbox: BBox;
  last_active: string | null;
  total_tasks: number;
  num_contributors: number | null;
  total_submissions: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
};

export type taskType = {
  id: number;
  outline: Polygon;
  project_id: number;
  project_task_index: number;
  feature_count: number;
  task_state: string;
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
};

export type downloadProjectFormLoadingType = { type: 'form' | 'geojson' | 'csv' | 'json'; loading: boolean };

export type projectDashboardDetailTypes = {
  slug: string;
  organisation_name: string;
  total_tasks: number;
  created_at: string;
  organisation_id: number;
  organisation_logo: string;
  total_submissions: number | null;
  total_contributors: number | null;
  last_active: string;
  status: project_status;
};

export type projectTaskBoundriesType = {
  id: number;
  taskBoundries: taskBoundriesTypes[];
};

export type taskBoundriesTypes = {
  id: number;
  index: number;
  outline: Polygon;
  task_state: string;
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
};

export type tileType = {
  id: string;
  url: string | null;
  tile_source: string;
  background_task_id: string;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  created_at: string;
  bbox: any;
  format: string | null;
  mimetype: string | null;
};

export type EntityOsmMap = {
  id: string;
  osm_id: number;
  status: number;
  task_id: number;
  updated_at: string;
  submission_ids: string | null;
  geometry: string | null;
  created_by: string | null;
};
