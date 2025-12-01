import { api } from '.';
import { updateProjectFormPayloadType, odkCredsParamsType } from '@/types';

export const testOdkCredentials = (params: odkCredsParamsType) => api.post('/central/test-credentials', {}, { params });

export const getFormLists = () => api.get('/central/list-forms');

export const uploadProjectXlsform = (payload: FormData, params: { project_id: number }) =>
  api.post('/central/upload-xlsform', payload, { params });

export const updateProjectForm = (payload: updateProjectFormPayloadType, params: { project_id: number }) =>
  api.post('/central/update-form', payload, { params });

export const downloadForm = (params: { project_id: number }) =>
  api.get('/central/download-form', { params, responseType: 'blob' });

export const detectFormLanguages = (payload: FormData) => api.post('/central/detect-form-languages', payload);

export const listFormMedia = (params: { project_id: number }) => api.post('/central/list-form-media', {}, { params });
