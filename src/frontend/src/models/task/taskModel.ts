export type taskSubmissionInfoType = {
  task_id: string;
  index: string;
  submission_count: number;
  last_submission: string | null;
  feature_count: number;
};

export type taskFeaturePropertyType = {
  fid: number;
  geometry: any;
  name: string | null;
  uid: number;
};

export type taskWiseSubmissionCount = {
  code: string;
  count: number;
};

export type taskBoundariesType = {
  type: string;
  features: Record<string, any>[];
};

export type colorCodesType = Record<string, colorMinMaxType>;
type colorMinMaxType = {
  min: number;
  max: number;
};

export type legendColorArrayType = {
  min: number;
  max: number;
  color: string;
};

export type EntityOsmMap = {
  id: string;
  osm_id: number;
  status: number;
  task_id: number;
  updated_at: string;
  submission_ids: string | null;
  geometry: string | null;
  created_by: string | null;
};
