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
  action_date: string;
  action_text: string;
  changedToStatus: string;
  id: number;
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
  taskId: string;
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

export type downloadProjectFormLoadingType = { type: 'form' | 'geojson'; loading: boolean };
