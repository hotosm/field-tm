import { paginationType } from '@/store/types/ICommon';
import { project_status } from '@/types/enums';

// PAYLOAD
export type updateReviewStatePayloadType = {
  instance_id: string;
  review_state: string;
};

// PARAMS
export type submissionsParamsType = {
  project_id: number;
};

export type downloadSubmissionParamsType = {
  file_type: 'geojson' | 'json' | 'csv';
  submitted_date_range?: string;
  project_id: number;
};

export type submissionTableParamsType = {
  page: number;
  results_per_page: number;
  task_id?: number;
  submitted_by?: string;
  review_state?: string;
  submitted_date_range?: string;
  project_id: number;
};

// RESPONSE
export type submissionFormFieldsType = {
  path: string;
  name: string;
  type: string;
  binary: unknown | null;
  selectMultiple: unknown | null;
};

export type submissionTableType = {
  results: Record<string, any>[];
  pagination: paginationType;
};

export type updateReviewStateType = {
  instanceId: string;
  submitterId: number;
  deviceId: string;
  createdAt: string;
  updatedAt: string;
  reviewState: string;
};

export type projectSubmissionDashboardType = {
  slug: string;
  created_at: string;
  last_active: string;
  status: project_status;
};
