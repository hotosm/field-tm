import { api } from '.';
import { qfieldCredsParamsType } from '@/api/qfield/types';

export const testQFieldCredentials = (params: qfieldCredsParamsType) =>
  api.post('/qfield/test-credentials', {}, { params });
