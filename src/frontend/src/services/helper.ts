import { api } from '.';
import { odkCredsParamsType, xlsformTemplateDownloadParamsType } from '@/types';

export const testOdkCredentials = (params: odkCredsParamsType) =>
  api.post('/helper/odk-credentials-test', {}, { params });

export const downloadTemplateXlsform = (params: xlsformTemplateDownloadParamsType) =>
  api.get('/helper/download-template-xlsform', { params });
