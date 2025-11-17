// PARAMS
export type odkCredsParamsType = {
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
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
