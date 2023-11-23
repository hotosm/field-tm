export type CreateProjectStateTypes = {
  editProjectDetails: EditProjectDetailsTypes;
  editProjectResponse?: EditProjectResponseTypes | null;
  projectDetails: ProjectDetailsTypes;
  projectDetailsResponse: EditProjectResponseTypes | null;
  projectDetailsLoading: boolean;
  editProjectDetailsLoading: boolean;
  projectArea: ProjectAreaTypes | null;
  projectAreaLoading: boolean;
  formCategoryList: FormCategoryListTypes | [];
  formCategoryLoading: boolean;
  generateQrLoading: boolean;
  organizationList: OrganizationListTypes[];
  organizationListLoading: boolean;
  generateQrSuccess: GenerateQrSuccessTypes | null;
  generateProjectLogLoading: boolean;
  generateProjectLog: GenerateProjectLogTypes | null;
  createProjectStep: number;
  dividedTaskLoading: boolean;
  dividedTaskGeojson: string | null;
  formUpdateLoading: boolean;
  taskSplittingGeojsonLoading: boolean;
  taskSplittingGeojson: TaskSplittingGeojsonTypes | null;
  updateBoundaryLoading: boolean;
  drawnGeojson: DrawnGeojsonTypes | null;
  drawToggle: boolean;
  validateCustomFormLoading: boolean;
  validateCustomFormResponse: ValidateCustomFormResponse | null;
  uploadAreaSelection: string | null;
  totalAreaSelection: string | null;
  splitTasksSelection: string | null;
  buildingGeojson: null;
  lineGeojson: null;
  createProjectValidations: {};
  isUnsavedChanges: boolean;
  canSwitchCreateProjectSteps: boolean;
};
export type ValidateCustomFormResponse = {
  detail: { message: string; possible_reason: string };
};
export type AuthorTypes = {
  username: string;
  id: number;
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
};

export type ProjectTaskTypes = {
  id: number;
  project_id: number;
  project_task_index: number;
  project_task_name: string;
  outline_geojson: GeoJSONFeatureTypes;
  outline_centroid: GeoJSONFeatureTypes;
  task_status: number;
  locked_by_uid: number | null;
  locked_by_username: string | null;
  task_history: any[];
  qr_code_base64: string;
  task_status_str: string;
};

export type ProjectInfoTypes = {
  name: string;
  short_description: string;
  description: string;
};

type EditProjectResponseTypes = {
  id: number;
  odkid: number;
  author: AuthorTypes;
  project_info: ProjectInfoTypes[];
  status: number;
  outline_geojson: GeoJSONFeatureTypes;
  project_tasks: ProjectTaskTypes[];
  xform_title: string;
  hashtags: string[];
};
export type EditProjectDetailsTypes = {
  name: string;
  description: string;
  short_description: string;
};

export type ProjectDetailsTypes = {
  task_split_dimension: number;
  task_num_buildings: number;
  no_of_buildings: number;
  odk_central_user?: string;
  odk_central_password?: string;
  organization?: number;
  odk_central_url?: string;
  name?: string;
  hashtags?: string;
  short_description?: string;
  description?: string;
  task_split_type?: number;
  xform_title?: string;
  data_extract_options?: string;
  data_extractWays?: string;
  form_ways?: string;
  organisation_id?: number | null;
};

export type ProjectAreaTypes = {
  // Define properties related to the project area here
};

export type FormCategoryListTypes = {
  id: number;
  title: string;
};

export type GenerateQrSuccessTypes = {
  Message: string;
  task_id: string;
};

export type OrganizationListTypes = {
  logo: string;
  id: number;
  url: string;
  slug: string;
  name: string;
  description: string;
  type: 1;
};

export type GenerateProjectLogTypes = {
  status: string;
  message: string | null;
  progress: number;
  logs: string;
};

export type TaskSplittingGeojsonTypes = {
  // Define properties related to the task splitting GeoJSON here
};

export type DrawnGeojsonTypes = {
  type: string;
  properties: null;
  geometry: GeometryTypes;
};
