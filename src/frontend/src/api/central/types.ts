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
};

// RESPONSE
export type formType = {
  id: number;
  title: string;
};
