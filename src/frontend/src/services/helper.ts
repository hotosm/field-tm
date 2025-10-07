import { api } from '.';
import { xlsformTemplateDownloadParamsType } from '@/types';

export const downloadTemplateXlsform = (params: xlsformTemplateDownloadParamsType) =>
  api.get('/helper/download-template-xlsform', { params });
