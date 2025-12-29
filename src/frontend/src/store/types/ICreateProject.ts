import { MapGeomTypes, project_visibility, project_status } from '@/types/enums';

export type CreateProjectStateTypes = {
  editProjectDetails: ProjectDetailsTypes;
  editProjectResponse?: EditProjectResponseTypes | null;
  projectDetails: Partial<ProjectDetailsTypes>;
  projectDetailsResponse: EditProjectResponseTypes | null;
  createDraftProjectLoading: { loading: boolean; continue: boolean };
  createProjectLoading: boolean;
  projectDetailsLoading: boolean;
  editProjectDetailsLoading: boolean;
  formUpdateLoading: boolean;
  customFileValidity: boolean;
  task_num_buildings: number | null;
  task_split_dimension: number | null;
  isProjectDeletePending: boolean;
};

export type GeometryTypes = {
  type: string;
  coordinates: number[][][];
};

export type GeoJSONFeatureTypes = {
  type: string;
  geometry: GeometryTypes;
  properties: Record<string, any>;
  id: string;
  bbox: null | number[];
  features?: [];
};

export type ProjectTaskTypes = {
  id: number;
  index: number;
  project_id: number;
  outline: GeoJSONFeatureTypes;
  task_state: string;
  actioned_by_uid: number | null;
  actioned_by_username: string | null;
  task_history: any[];
  qr_code_base64: string;
};

type EditProjectResponseTypes = {
  id: number;
  external_project_id: number;
  project_name: string;
  description: string;
  status: project_status;
  outline: GeoJSONFeatureTypes;
  tasks: ProjectTaskTypes[];
  osm_category: string;
  hashtags: string[];
};

export type ProjectDetailsTypes = {
  dimension: number;
  data_extract_url?: string;
  task_split_dimension?: number;
  task_num_buildings?: number;
  no_of_buildings: number;
  odk_central_user?: string;
  odk_central_password?: string;
  odk_central_url?: string;
  project_name: string;
  hashtags: string[];
  description: string;
  task_split_type?: number;
  osm_category?: string;
  data_extract_options?: string;
  formExampleSelection?: string;
  osmFormSelectionName?: string;
  average_buildings_per_task?: number;
  dataExtractType?: string;
  per_task_instructions?: string;
  custom_tms_url: string;
  hasCustomTMS: boolean;
  xlsFormFileUpload: any;
  primaryGeomType: MapGeomTypes;
  includeCentroid: boolean;
  useMixedGeomTypes: boolean;
  newGeomType: MapGeomTypes;
  project_admins: number[];
  visibility: project_visibility;
  use_odk_collect: boolean;
  status: project_status;
  outline: splittedGeojsonType;
};

export type FormCategoryListTypes = {
  id: number;
  title: string;
};

export type DrawnGeojsonTypes = {
  type: string;
  properties: null;
  geometry: GeometryTypes;
  features?: [];
};

export type taskSplitOptionsType = {
  name: string;
  value: string;
  label: string;
  disabled: boolean;
};

export type dataExtractGeojsonType = {
  type: string;
  features: Record<string, any>[];
};

export type splittedGeojsonType = {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    geometry: { type: 'Polygon'; coordinates: number[][] };
    properties: Record<string, any>;
  }[];
};

export type projectVisibilityOptionsType = {
  project_name: string;
  value: project_visibility;
  label: string;
};
