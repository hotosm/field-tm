import { api } from '.';
import { updateProjectFormPayloadType } from '@/types';

export const getFormLists = () => api.get('/central/list-forms');

export const uploadProjectXlsform = (payload: FormData, params: { project_id: number }) =>
  api.post('/central/upload-xlsform', payload, { params });

export const updateProjectForm = (payload: updateProjectFormPayloadType, params: { project_id: number }) =>
  api.post('/central/update-form', payload, { params });

export const downloadForm = (params: { project_id: number }) => api.get('/central/download-form', { params });
