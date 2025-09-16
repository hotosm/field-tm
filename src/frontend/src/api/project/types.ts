import {
  basemap_providers,
  GeoGeomTypesEnum,
  MapGeomTypes,
  project_roles,
  project_status,
  project_visibility,
  task_split_type,
  tile_output_formats,
} from '@/types/enums';
import type { Point, Polygon, FeatureCollection, Geometry } from 'geojson';
import type { taskType } from '@/types';

export type FieldMappingApp = 'ODK' | 'QField' | 'FieldTM';

export interface projectBaseType {
  id: number;
  organisation_id: string;
  odkid: number;
  author_sub: number;
  name: string;
  short_description: string;
  description: string;
  per_task_instructions: string;
  slug: string;
  location_str: string;
  outline: Polygon;
  status: string;
  total_tasks: number;
  osm_category: string;
  odk_form_id: string;
  odk_form_xml: string;
  visibility: project_visibility;
  mapper_level: string;
  priority: string;
  featured: boolean;
  due_date: null | string;
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
  odk_token: string;
  data_extract_url: string;
  task_split_type: task_split_type;
  task_split_dimension: number | null;
  task_num_buildings: number | null;
  hashtags: string[];
  custom_tms_url: string;
  geo_restrict_force_error: boolean;
  geo_restrict_distance_meters: number;
  primary_geom_type: GeoGeomTypesEnum;
  new_geom_type: GeoGeomTypesEnum;
  use_odk_collect: boolean;
  created_at: string;
  updated_at: string;
}

// PAYLOAD TYPES
export type generateProjectBasemapPayloadType = {
  tile_source: basemap_providers;
  file_format: tile_output_formats;
  tms_url?: string;
};

export type createProjectPayloadType = Partial<projectBaseType>;

export type updateProjectPayloadType = Partial<projectType>;

export type taskSplitPayloadType = {
  project_geojson: string;
  extract_geojson?: string;
  no_of_buildings?: number;
};

export type previewSplitBySquarePayload = {
  project_geojson: string;
  dimension_meters: number;
  extract_geojson?: string;
};

export type generateDataExtractPayloadType = {
  geojson_file: string;
  osm_category: string;
  centroid: boolean;
  geom_type: MapGeomTypes;
};

export type uploadDataExtractPayloadType = { data_extract_file: string };

export type generateFilesPayloadType = {
  combined_features_count: number;
};

export type createStubProjectPayloadType = Pick<
  projectBaseType,
  'name' | 'short_description' | 'description' | 'organisation_id' | 'outline'
> & {
  merge: boolean;
};

export type uploadProjectTaskBoundariesPayloadType = {
  task_geojson: string;
};

export type entitiesMappingStatusPayloadType = {
  entity_id: string;
  status: number;
  label: string;
  submission_ids?: string;
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

export type odkEntitiesGeojsonParamsType = {
  minimal?: boolean;
};

export type downloadFeaturesParamsType = {
  project_id: number;
  task_id?: number;
};

export type projectUsersParamsType = {
  role: project_roles;
};

export type deleteEntityParamsType = {
  project_id: number;
};

export type addProjectManagerParamsType = {
  sub: string;
  project_id?: string;
  org_id?: string;
  mapper?: boolean;
};

export type createStubProjectParamsType = {
  project_id?: number;
  org_id?: string;
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

export interface projectType extends projectBaseType {
  tasks: taskType[];
  organisation_name: string;
  organisation_logo: string | null;
  centroid: Point;
  last_active: string;
  total_tasks: number;
  num_contributors: number;
  total_submissions: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
}

export type odkEntitiesGeojsonType = FeatureCollection<Geometry, odkEntitiesGeojsonPropertiesType>;

type odkEntitiesGeojsonPropertiesType = {
  task_id: string;
  osm_id: string;
  tags: string;
  version: string;
  changeset: string;
  timestamp: string;
  status: string;
  created_by: string;
  updated_at: string | null;
};

export type odkEntitiesMappingStatusesType = {
  id: string;
  task_id: number;
  osm_id: number;
  status: number;
  submission_ids: string;
  geometry: string;
  created_by: string;
  updated_at: string;
};

export type contributorsType = {
  user: string;
  submissions: number;
};

export type projectUserType = {
  user_sub: string;
  project_id: number;
  role: project_roles;
  username: string;
};
