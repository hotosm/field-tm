import {
  submissionContributorsTypes,
  submissionFormFieldsTypes,
  submissionTableDataTypes,
} from '@/models/submission/submissionModel';

export type SubmissionStateTypes = {
  submissionContributors: submissionContributorsTypes[];
  submissionContributorsLoading: boolean;
  submissionFormFields: submissionFormFieldsTypes[];
  submissionTableData: submissionTableDataTypes;
  submissionFormFieldsLoading: boolean;
  submissionTableDataLoading: boolean;
  submissionTableRefreshing: boolean;
  updateReviewStatusModal: updateReviewStatusModal;
  updateReviewStateLoading: boolean;
  mappedVsValidatedTask: mappedVsValidatedTaskType[];
  mappedVsValidatedTaskLoading: boolean;
};

type updateReviewStatusModal = {
  toggleModalStatus: boolean;
  instanceId: string | null;
  taskId: string | null;
  projectId: number | null;
  reviewState: string;
  taskUid: string | null;
  entity_id: string | null;
  label: string | null;
};

export type filterType = {
  task_id: string | null;
  submitted_by: string | null;
  review_state: string | null;
  submitted_date_range: string | null;
};

type mappedVsValidatedTaskType = {
  date: string;
  mapped: number;
  validated: number;
  label: string;
};

export type featureType = {
  type: 'Feature';
  geometry: Partial<{
    type: string;
    coordinates: any[];
  }>;
  properties: Record<string, any>;
};

export type geojsonType = {
  type: 'FeatureCollection';
  features: featureType[];
};
