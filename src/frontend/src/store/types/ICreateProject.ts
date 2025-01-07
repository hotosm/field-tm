import { task_split_type } from '@/types/enums';

export type CreateProjectStateTypes = {
  editProjectDetails: ProjectDetailsTypes;
  editProjectResponse?: EditProjectResponseTypes | null;
  projectDetails: Partial<ProjectDetailsTypes>;
  projectDetailsResponse: EditProjectResponseTypes | null;
  projectDetailsLoading: boolean;
  editProjectDetailsLoading: boolean;
  formCategoryList: FormCategoryListTypes[];
  formCategoryLoading: boolean;
  generateProjectLoading: boolean;
  generateProjectSuccess: boolean;
  generateProjectError: boolean;
  organisationList: OrganisationListTypes[];
  organisationListLoading: boolean;
  dividedTaskLoading: boolean;
  dividedTaskGeojson: null | splittedGeojsonType;
  formUpdateLoading: boolean;
  taskSplittingGeojsonLoading: boolean;
  taskSplittingGeojson: splittedGeojsonType | null;
  updateBoundaryLoading: boolean;
  drawnGeojson: DrawnGeojsonTypes | null;
  drawToggle: boolean;
  validateCustomFormLoading: boolean;
  uploadAreaSelection: 'upload_file' | 'draw' | null;
  totalAreaSelection: string | null;
  splitTasksSelection: task_split_type | null;
  dataExtractGeojson: GeoJSONFeatureTypes | null;
  createProjectValidations: {};
  isUnsavedChanges: boolean;
  canSwitchCreateProjectSteps: boolean;
  isTasksGenerated: Record<string, any>;
  isFgbFetching: boolean;
  toggleSplittedGeojsonEdit: boolean;
  customFileValidity: boolean;
  additionalFeatureGeojson: GeoJSONFeatureTypes | null;
  descriptionToFocus: string | null;
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
  status: number;
  outline: GeoJSONFeatureTypes;
  tasks: ProjectTaskTypes[];
  xform_category: string;
  hashtags: string;
};

export type ProjectDetailsTypes = {
  dimension: number;
  data_extract_url?: string;
  task_split_dimension?: number;
  task_num_buildings?: number;
  no_of_buildings: number;
  odk_central_user?: string;
  odk_central_password?: string;
  organisation?: number;
  odk_central_url?: string;
  name?: string;
  hashtags?: string;
  short_description?: string;
  description?: string;
  task_split_type?: number;
  xform_category?: string;
  data_extract_options?: string;
  form_ways?: string;
  organisation_id?: number | null;
  formWays?: string;
  formCategorySelection?: string;
  average_buildings_per_task?: number;
  dataExtractWays?: string;
  per_task_instructions?: string;
  custom_tms_url: string;
  hasCustomTMS: boolean;
  customFormUpload: any;
  hasAdditionalFeature: boolean;
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
