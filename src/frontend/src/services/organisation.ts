import { api } from '.';

export const getOrganisations = () => api.get('/organisation');

export const createOrganisation = (payload, params) => api.post('/organisation', { payload }, { params });

export const getMyOrganisations = () => api.get('/organisation/my-organisations');

export const getUnapprovedOrganisations = () => api.get('/organisation/unapproved');

export const deleteUnapprovedOrganisation = (id) => api.delete(`/organisation/unapproved/${id}`);

export const approveOrganisation = (params) => api.post('/organisation/approve', {}, { params });

export const addNewOrganisationAdmin = (params) => api.post(`/organisation/new-admin`, {}, { params });

export const getOrganisationAdmins = (params) => api.get('/organisation/org-admins', { params });

export const getOrganisationDetail = (id, params) => api.get(`/organisation/${id}`, { params });

export const updateOrganisation = (id, payload, params) => api.put(`/organisation/${id}`, payload, { params });

export const deleteOrganisation = (id) => api.delete(`/organisation/${id}`);

export const removeOrganisationAdmin = (id, params) => api.delete(`/organisation/org-admin/${id}`, { params });
