import {
  addNewOrganisationAdminParamsType,
  approveOrganisationParamsType,
  createOrganisationParamsType,
  createUpdateOrganisationPayloadType,
  removeOrganisationAdminParamsType,
  updateOrganisationParamsType,
} from '@/types';
import { api } from '.';

export const getOrganisations = () => api.get('/organisation');

export const createOrganisation = (
  payload: createUpdateOrganisationPayloadType,
  params: createOrganisationParamsType,
) => api.post('/organisation', { payload }, { params });

export const getMyOrganisations = () => api.get('/organisation/my-organisations');

export const getUnapprovedOrganisations = () => api.get('/organisation/unapproved');

export const deleteUnapprovedOrganisation = (id: number) => api.delete(`/organisation/unapproved/${id}`);

export const approveOrganisation = (params: approveOrganisationParamsType) =>
  api.post('/organisation/approve', {}, { params });

export const addNewOrganisationAdmin = (params: addNewOrganisationAdminParamsType) =>
  api.post(`/organisation/new-admin`, {}, { params });

export const getOrganisationAdmins = (params: { org_id: number }) => api.get('/organisation/org-admins', { params });

export const getOrganisationDetail = (id: number, params: { org_id: number }) =>
  api.get(`/organisation/${id}`, { params });

export const updateOrganisation = (
  id: number,
  payload: createUpdateOrganisationPayloadType,
  params: updateOrganisationParamsType,
) => api.patch(`/organisation/${id}`, payload, { params });

export const deleteOrganisation = (id: number, params: { project_id: number }) =>
  api.delete(`/organisation/${id}`, { params });

export const removeOrganisationAdmin = (user_sub: string, params: removeOrganisationAdminParamsType) =>
  api.delete(`/organisation/org-admin/${user_sub}`, { params });
