import { api } from '.';
import { getOsmCallbackParams } from '@/types';

export const getOsmLoginUrl = () => api.get('/auth/login/osm');

export const osmCallback = (params: getOsmCallbackParams) => api.get('/auth/callback/osm', { params });

export const logout = () => api.get('/auth/logout');

export const myData = () => api.get('/auth/me');

export const refreshCookies = () => api.get('/auth/refresh');
