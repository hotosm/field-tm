import { api } from '.';
import { updateProjectFormPayloadType, uploadXlsformPayloadType } from '@/types';

export const getFormLists = () => api.get('/central/list-forms');

export const uploadProjectXlsform = (payload: uploadXlsformPayloadType, params: { project_id: number }) =>
  api.post('/central/upload-xlsform', payload, { params });

export const updateProjectForm = (payload: updateProjectFormPayloadType, params: { project_id: number }) =>
  api.post('/central/update-form', payload, { params });

export const downloadForm = (params: { project_id: number }) =>
  api.get('/central/download-form', { params, responseType: 'blob' });
