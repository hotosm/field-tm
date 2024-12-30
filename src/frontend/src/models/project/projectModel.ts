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
  outline: {
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
  location_str: string;
  description: string;
  short_description: string;
  xform_category: string;
  odk_form_id: string;
  data_extract_url: string;
  odk_token: string;
  num_contributors: any;
  tasks_bad: any;
  tasks_mapped: any;
  tasks_validated: any;
  total_tasks: any;
  organisation_id: number;
  organisation_logo: string;
  organisation_name: string;
  instructions: string;
  custom_tms_url: string;
  created_at: string;
};

export type downloadProjectFormLoadingType = { type: 'form' | 'geojson' | 'csv' | 'json'; loading: boolean };

export type projectDashboardDetailTypes = {
  slug: string;
  organisation_name: string;
  total_tasks: number;
  created_at: string;
  organisation_logo: string;
  total_submissions: number | null;
  total_contributors: number | null;
  last_active: string;
};

export type projectTaskBoundriesType = {
  id: number;
  taskBoundries: taskBoundriesTypes[];
};

export type taskBoundriesTypes = {
  id: number;
  index: number;
  project_task_index: number;
  actioned_by_uid: null | string;
  actioned_by_username: null | string;
  outline: {
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
  task_state: string;
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
