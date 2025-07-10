import { task_split_type, MapGeomTypes, project_visibility, project_status } from '@/types/enums';

export type CreateProjectStateTypes = {
  editProjectDetails: ProjectDetailsTypes;
  editProjectResponse?: EditProjectResponseTypes | null;
  projectDetails: Partial<ProjectDetailsTypes>;
  projectDetailsResponse: EditProjectResponseTypes | null;
  createDraftProjectLoading: boolean;
  createProjectLoading: boolean;
  projectDetailsLoading: boolean;
  editProjectDetailsLoading: boolean;
  formExampleList: FormCategoryListTypes[];
  formCategoryLoading: boolean;
  generateProjectLoading: boolean;
  generateProjectSuccess: boolean;
  generateProjectWarning: string | null;
  generateProjectError: boolean;
  organisationList: OrganisationListTypes[];
  organisationListLoading: boolean;
  dividedTaskLoading: boolean;
  dividedTaskGeojson: null | splittedGeojsonType;
  formUpdateLoading: boolean;
  taskSplittingGeojsonLoading: boolean;
  updateBoundaryLoading: boolean;
  drawnGeojson: DrawnGeojsonTypes | null;
  drawToggle: boolean;
  validateCustomFormLoading: boolean;
  uploadAreaSelection: 'upload_file' | 'draw' | null;
  totalAreaSelection: string | null;
  taskSplittingMethod: task_split_type | null;
  dataExtractGeojson: GeoJSONFeatureTypes | null;
  createProjectValidations: {};
  isUnsavedChanges: boolean;
  canSwitchCreateProjectSteps: boolean;
  isTasksSplit: Record<string, any>;
  isFgbFetching: boolean;
  toggleSplittedGeojsonEdit: boolean;
  customFileValidity: boolean;
  descriptionToFocus: string | null;
  task_num_buildings: number | null;
  task_split_dimension: number | null;
  isProjectDeletePending: boolean;
  splitGeojsonBySquares: splittedGeojsonType | null;
  splitGeojsonByAlgorithm: splittedGeojsonType | null;
  basicProjectDetailsLoading: boolean;
  basicProjectDetails:
    | ({ id: number } & Pick<
        ProjectDetailsTypes,
        'name' | 'short_description' | 'description' | 'organisation_id' | 'outline'
      >)
    | null;
};
export type ValidateCustomFormResponse = {
  detail: { message: string; possible_reason: string };
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
  odkid: number;
  name: string;
  short_description: string;
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
  organisation: number;
  odk_central_url?: string;
  name: string;
  hashtags: string[];
  short_description: string;
  description: string;
  task_split_type?: number;
  osm_category?: string;
  data_extract_options?: string;
  organisation_id: number | null;
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

export type OrganisationListTypes = {
  id: number;
  name: string;
  approved: boolean;
  type: string;
  logo: string | null;
  description: string;
  slug: string;
  url: string;
  odk_central_url: string | null;
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
  name: string;
  value: project_visibility;
  label: string;
};
