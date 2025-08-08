import { api } from '.';

export const getOsmLoginUrl = () => api.get('/auth/login/osm/management');

export const osmCallback = () => api.get('/auth/callback/osm');

export const logout = () => api.get('/auth/logout');

export const myData = () => api.get('/auth/me');

export const refreshCookies = () => api.get('/auth/refresh/management');
