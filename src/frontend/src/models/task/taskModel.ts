export type taskSubmissionInfoType = {
  task_id: string;
  index: string;
  submission_count: number;
  last_submission: string | null;
  feature_count: number;
};

export type EntityOsmMap = {
  id: string;
  osm_id: number;
  status: number;
  task_id: number;
  updated_at: string;
  geometry: string | null;
  created_by: string | null;
};
