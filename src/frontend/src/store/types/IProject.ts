export type ProjectStateTypes = {
  projectLoading: boolean;
  projectTaskBoundries: projectTaskBoundriesType[];
  newProjectTrigger: boolean;
  projectInfo: projectInfoType | {};
  projectSubmissionLoading: boolean;
  projectSubmission: [];
  projectDataExtractLoading: boolean;
  downloadProjectFormLoading: downloadProjectFormLoadingType;
  generateProjectTilesLoading: boolean;
  tilesList: tilesListTypes[];
  tilesListLoading: boolean;
  downloadTilesLoading: boolean;
  downloadDataExtractLoading: boolean;
  taskModalStatus: boolean;
  mobileFooterSelection: string;
  geolocationStatus: boolean;
  projectDetailsLoading: boolean;
  projectDashboardDetail: projectDashboardDetailTypes;
  projectDashboardLoading: boolean;
};

type projectTaskBoundriesType = {
  id: number;
  taskBoundries: taskBoundriesTypes[];
};

type taskBoundriesTypes = {
  bbox: [number, number];
  id: number;
  locked_by_uid: null | string;
  locked_by_username: null | string;
  odk_token: string;
  outline_geojson: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: [string, string, string, string];
  };
  outline_centroid: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: [string, string, string, string];
  };
  task_history: taskHistoryTypes[];
  task_status: string;
};

type projectInfoType = {
  id: number;
  outline_geojson: {
    type: string;
    geometry: {
      type: string;
      coordinates: [];
    };
    properties: {
      id: number;
      bbox: [number, number, number, number];
    };
    id: number;
  };
  priority: number;
  priority_str: string;
  title: string;
  location_str: string;
  description: string;
  short_description: string;
  xform_title: string;
  data_extract_url: string;
  num_contributors: any;
  tasks_bad: any;
  tasks_mapped: any;
  tasks_validated: any;
  total_tasks: any;
};

type taskHistoryTypes = {
  action_date: string;
  action_text: string;
  id: number;
  profile_img: null | string;
  status: string;
  username: string;
};

type downloadProjectFormLoadingType = { type: 'form' | 'geojson'; loading: boolean };

type tilesListTypes = {
  id: number;
  project_id: number;
  status: string;
  tile_source: string;
};

type projectDashboardDetailTypes = {
  project_name_prefix: string;
  organisation_name: string;
  total_tasks: number | null;
  created: string;
  organisation_logo: string;
  total_submission: number | null;
  total_contributors: number | null;
  last_active: string;
};
