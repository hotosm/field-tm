// PARAMS
export type odkCredsParamsType = {
  external_project_instance_url: string;
  external_project_username: string;
  external_project_password: string;
};

export type xlsformTemplateDownloadParamsType = {
  form_type: 'OSM Buildings' | 'OSM Healthcare' | 'OSM Highways';
};

// RESPONSE
export type metricsType = {
  total_features_surveyed: number;
  countries_covered: number;
  total_projects: number;
  total_users: number;
  total_organisations: number;
};
