import { project_status, GeoGeomTypesEnum } from '@/types/enums';

export type osmTag = {
  string: string;
};

export type dataExtractPropertyType = {
  osm_id: number;
  tags: Array<{ [key: string]: string }>;
  timestamp: Date;
  changeset: number;
  version: number;
};

export type taskHistoryTypes = {
  event_id: string;
  event: number;
  state: string;
  comment: string;
  username: string;
  profile_img: null | string;
  created_at: string;
};

export type projectInfoType = {
  id: number;
  name: string;
  outline: outlineType;
  odkid: number;
  author_id: number;
  organisation_id: number;
  short_description: string;
  description: string;
  per_task_instructions: string;
  slug: string;
  task_split_type: string;
  location_str: string;
  custom_tms_url: string;
  status: string;
  visibility: string;
  use_odk_collect: boolean;
  total_tasks: number;
  osm_category: string;
  odk_form_id: string;
  mapper_level: string;
  priority: string;
  featured: boolean;
  odk_central_url: string;
  odk_central_user: string;
  odk_token: string;
  data_extract_url: string;
  task_split_dimension: null | number;
  task_num_buildings: number;
  hashtags: string[];
  due_date: null | string;
  updated_at: string;
  created_at: string;
  tasks: taskType[];
  organisation_name: string;
  organisation_logo: string | null;
  centroid: { type: 'Point'; coordinates: [number, number] };
  bbox: [number, number, number, number];
  last_active: string;
  num_contributors: number | null;
  instructions: string;
  primary_geom_type: GeoGeomTypesEnum;
  new_geom_type: GeoGeomTypesEnum;
};

export type taskType = {
  id: number;
  outline: outlineType;
  project_id: number;
  project_task_index: number;
  feature_count: number;
  task_state: string;
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
};

export type outlineType = {
  type: string;
  coordinates: number[][][];
  properties: Record<string, any>;
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
  outline: outlineType;
  task_state: string;
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
};

export type taskBoundriesGeojson = {
  id: number;
  outline: {
    type: string;
    geometry: {
      coordinates: [];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
  };
  outline_centroid: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: null | number[];
  };
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
