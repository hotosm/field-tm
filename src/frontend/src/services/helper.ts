import { api } from '.';

export const testOdkCredentials = (params) => api.post('/helper/odk-credentials-test', {}, { params });

export const downloadTemplateXlsform = (params) => api.get('/helper/download-template-xlsform', { params });
