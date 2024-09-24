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
  action_date: string;
  action_text: string;
  id: number;
  profile_img: null | string;
  status: string;
  username: string;
};

export type taskHistoryListType = {
  action: string;
  action_date: string;
  action_text: string;
  project_id: number;
  outlineGeojson: {
    type: string;
    geometry: {
      coordinates: [];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
  };
  profile_img: null | string;
  status: string;
  task_id: number;
  username: string;
};

export type projectInfoType = {
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
    bbox: null | number[];
  };
  priority: number;
  title: string;
  location_str: string;
  description: string;
  short_description: string;
  xform_category: string;
  xform_id: string;
  data_extract_url: string;
  odk_token: string;
  num_contributors: any;
  tasks_bad: any;
  tasks_mapped: any;
  tasks_validated: any;
  total_tasks: any;
  organisation_id: number;
  organisation_logo: string;
  instructions: string;
  custom_tms_url: string;
  created_at: string;
};

export type downloadProjectFormLoadingType = { type: 'form' | 'geojson' | 'csv' | 'json'; loading: boolean };

export type projectDashboardDetailTypes = {
  project_name_prefix: string;
  organisation_name: string;
  total_tasks: number | null;
  created_at: string;
  organisation_logo: string;
  total_submission: number | null;
  total_contributors: number | null;
  last_active: string;
};

export type projectTaskBoundriesType = {
  id: number;
  taskBoundries: taskBoundriesTypes[];
};

export type taskBoundriesTypes = {
  id: number;
  project_task_index: number;
  locked_by_uid: null | string;
  locked_by_username: null | string;
  outline_geojson: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: null | number[];
  };
  task_history: taskHistoryTypes[];
  task_status: string;
  index: number;
};

export type taskBoundriesGeojson = {
  id: number;
  outline_geojson: {
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
