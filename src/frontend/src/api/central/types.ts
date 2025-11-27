// PAYLOAD
export type uploadXlsformPayloadType = {
  xlsform: string;
};

export type updateProjectFormPayloadType = {
  xform_id: string;
  xlsform: string;
};

// PARAMS
export type uploadXlsformParamsType = {
  project_id: number;
  use_odk_collect?: boolean;
  need_verification_fields?: boolean;
  mandatory_photo_upload?: boolean;
  default_language?: string;
};

// RESPONSE
export type formType = {
  id: number;
  title: string;
};

export type formLanguagesType = {
  detected_languages: string[];
  default_language: string[];
  supported_languages: string[];
};
