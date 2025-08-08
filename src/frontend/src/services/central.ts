import { api } from '.';

export const getFormLists = () => api.get('/central/list-forms');

export const uploadProjectXlsform = (params) => api.post('/central/upload-xlsform', params);

export const updateProjectForm = (params) => api.post('/central/update-form', params);

export const downloadForm = (params) => api.get('/central/download-form', { params });
