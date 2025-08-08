import { api } from '.';

export const getSubmissions = (params) => api.get('/submission', { params });

export const downloadSubmission = (params) => api.get('/submission/download', { params });

export const getSubmissionFormFields = (params) => api.get('/submission/submission-form-fields', { params });

export const getSubmissionTable = (params) => api.get('/submission/submission-table', { params });

export const updateReviewState = (params) => api.post('/submission/update-review-state', params);

export const getSubmissionPhotos = (id) => api.get(`/submission/${id}/photos`);

export const getProjectSubmissionDashboard = (id) => api.get(`/submission/${id}/dashboard`);

export const getSubmissionDetail = (id, params) => api.get(`/submission/${id}`, { params });
