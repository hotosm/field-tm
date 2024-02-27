export type taskInfoType = {
  task_id: string;
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

export type federalWiseProjectCount = {
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
