export interface ProjectDetailsModel {
  id: number;
  odkid: number;
  author: {
    username: string;
    id: number;
  };
  default_locale: string;
  project_info: {
    locale: string;
    name: string;
    short_description: string;
    description: string;
    instructions: string;
    per_task_instructions: string;
  };
  status: number;
  xform_title: string;
  location_str: string;
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
  project_tasks: {
    id: number;
    project_id: number;
    project_task_index: number;
    project_task_name: string;
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
    task_status: number;
    locked_by_uid: number;
    locked_by_username: string;
    task_history: {
      id: number;
      action_text: string;
      action_date: string;
    }[];
    qr_code_base64: string;
    task_status_str: string;
  }[];
}

export interface FormCategoryListModel {
  id: number;
  title: string;
}
export interface OrganisationListModel {
  name: string;
  slug: string;
  description: string;
  type: number;
  subscription_tier: null | string;
  id: number;
  logo: string;
  url: string;
}
