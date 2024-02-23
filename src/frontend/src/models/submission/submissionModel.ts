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
