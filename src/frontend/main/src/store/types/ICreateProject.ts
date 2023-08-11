export interface ICreateProjectState {
  editProjectDetails: IEditProjectDetails;
  editProjectResponse?: IEditProjectResponse | null;
  projectDetails: IProjectDetails;
  projectDetailsResponse: IEditProjectResponse | null;
  projectDetailsLoading: boolean;
  projectArea: IProjectArea | null;
  projectAreaLoading: boolean;
  formCategoryList: IFormCategoryList | [];
  generateQrLoading: boolean;
  organizationList: IOrganizationList[];
  organizationListLoading: boolean;
  generateQrSuccess: IGenerateQrSuccess | null;
  generateProjectLogLoading: boolean;
  generateProjectLog: IGenerateProjectLog | null;
  createProjectStep: number;
  dividedTaskLoading: boolean;
  dividedTaskGeojson: string | null;
  formUpdateLoading: boolean;
  taskSplittingGeojsonLoading: boolean;
  taskSplittingGeojson: ITaskSplittingGeojson | null;
  updateBoundaryLoading: boolean;
  drawnGeojson: IDrawnGeojson | null;
  drawToggle: boolean;
}
export interface IAuthor {
  username: string;
  id: number;
}

export interface IGeometry {
  type: string;
  coordinates: number[][][];
}

export interface IGeoJSONFeature {
  type: string;
  geometry: IGeometry;
  properties: Record<string, any>;
  id: string;
  bbox: null | number[];
}

export interface IProjectTask {
  id: number;
  project_id: number;
  project_task_index: number;
  project_task_name: string;
  outline_geojson: IGeoJSONFeature;
  outline_centroid: IGeoJSONFeature;
  task_status: number;
  locked_by_uid: number | null;
  locked_by_username: string | null;
  task_history: any[];
  qr_code_base64: string;
  task_status_str: string;
}

export interface IProjectInfo {
  name: string;
  short_description: string;
  description: string;
}

interface IEditProjectResponse {
  id: number;
  odkid: number;
  author: IAuthor;
  project_info: IProjectInfo[];
  status: number;
  outline_geojson: IGeoJSONFeature;
  project_tasks: IProjectTask[];
  xform_title: string;
  hashtags: string[];
}
export interface IEditProjectDetails {
  name: string;
  description: string;
  short_description: string;
}

export interface IProjectDetails {
  dimension: number;
  no_of_buildings: number;
  odk_central_user?: string;
  odk_central_password?: string;
  organization?: number;
  odk_central_url?: string;
  name?: string;
  hashtags?: string;
  short_description?: string;
  description?: string;
  splitting_algorithm?: string;
  xform_title?: string;
  data_extract_options?: string;
  data_extractWays?: string;
  form_ways?: string;
}

export interface IProjectArea {
  // Define properties related to the project area here
}

export interface IFormCategoryList {
  id: number;
  title: string;
}

export interface IGenerateQrSuccess {
  Message: string;
  task_id: string;
}

export interface IOrganizationList {
  logo: string;
  id: number;
  url: string;
  slug: string;
  name: string;
  description: string;
  type: 1;
}

export interface IGenerateProjectLog {
  status: string;
  message: string | null;
  progress: number;
  logs: string;
}

export interface ITaskSplittingGeojson {
  // Define properties related to the task splitting GeoJSON here
}

export interface IDrawnGeojson {
  type: string;
  properties: null;
  geometry: IGeometry;
}
