import { api } from '.';
import {
  downloadSubmissionParamsType,
  submissionsParamsType,
  submissionTableParamsType,
  updateReviewStatePayloadType,
} from '@/types';

export const getSubmissions = (params: submissionsParamsType) => api.get('/submission', { params });

export const downloadSubmission = (params: downloadSubmissionParamsType) =>
  api.get('/submission/download', { params, responseType: 'blob' });

export const getSubmissionFormFields = (params: { project_id: number }) =>
  api.get('/submission/submission-form-fields', { params });

export const getSubmissionTable = (params: submissionTableParamsType) =>
  api.get('/submission/submission-table', { params });

export const updateReviewState = (params: { project_id: number }, payload: updateReviewStatePayloadType) =>
  api.post('/submission/update-review-state', payload, { params });

export const getSubmissionPhotos = (id: string, params: { project_id: number }) =>
  api.get(`/submission/${id}/photos`, { params });

export const getProjectSubmissionDashboard = (id: number) => api.get(`/submission/${id}/dashboard`);

export const getSubmissionDetail = (id: string, params: { project_id: number }) =>
  api.get(`/submission/${id}`, { params });
