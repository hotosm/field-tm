import { paginationType } from '@/store/types/ICommon';

export type submissionContributorsTypes = {
  user: string;
  contributions: number;
};

export type submissionFormFieldsTypes = {
  path: string;
  name: string;
  type: string;
  binary: any;
  selectMultiple: any;
};

export type submissionTableDataTypes = {
  results: Record<string, any>[];
  pagination: paginationType;
};

export type reviewListType = {
  id: string;
  title: string;
  className: string;
  hoverClass: string;
};

export type formSubmissionType = { date: string; count: number; label: string };
export type validatedMappedType = { date: string; validated: number; mapped: number; label: string };

export type updateReviewStateType = {
  instanceId: string;
  submitterId: number;
  deviceId: string;
  createdAt: string;
  updatedAt: string;
  reviewState: string;
};
