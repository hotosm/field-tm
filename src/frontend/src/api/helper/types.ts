// PARAMS
export type odkCredsParamsType = {
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
};

export type xlsformTemplateDownloadParamsType = {
  form_type: 'OSM Buildings' | 'OSM Healthcare' | 'OSM Highways';
};
