import { GeoGeomTypesEnum, task_split_type, project_visibility, field_mapping_app } from '@/types/enums';
import type { BBox, Point, Polygon } from 'geojson';

export type projectInfoType = {
  id: number;
  name: string;
  outline: Polygon;
  odkid: number;
  author_sub: number;
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
  centroid: Point;
  bbox: BBox;
  last_active: string | null;
  total_tasks: number;
  num_contributors: number | null;
  total_submissions: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
  field_mapping_app: field_mapping_app;
  external_project_id: number | null;
  project_url: string | null;
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

export type EntityOsmMap = {
  id: string;
  osm_id: number;
  status: number;
  task_id: number;
  updated_at: string;
  geometry: string | null;
  created_by: string | null;
};
