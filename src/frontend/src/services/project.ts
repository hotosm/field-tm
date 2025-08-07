import { api } from '.';
import type { projectSummariesParamsType } from '@/api/project/types';

export const getProjects = (params) => api.get('/projects', { params });

export const patchCreateProject = (payload, params) => api.patch('/projects/', payload, { params });

export const getProjectSummaries = (params: projectSummariesParamsType) => api.get('/projects/summaries', { params });

export const getOdkEntitiesGeojson = (id, params) => api.get(`/projects/${id}/entities`, { params });

export const getOdkEntitiesMappingStatuses = (id) => api.get(`/projects/${id}/entities/statuses`);

export const getTilesList = (id) => api.get(`/projects/${id}/tiles`);

export const downloadFeatures = (params) => api.get('/projects/features/download', { params });

export const getContributors = (id) => api.get(`/projects/contributors/${id}`);

export const taskSplit = (payload) => api.post('/projects/task-split', payload);

export const previewSplitBySquare = (payload) => api.post('/projects/preview-split-by-square', payload);

export const generateDataExtract = (payload, params) =>
  api.post('/projects/generate-data-extract', { payload }, { params });

export const uploadDataExtract = (payload, params) =>
  api.post('/projects/upload-data-extract', { payload }, { params });

export const addProjectManager = (params) => api.post('/projects/add-manager');

export const getProjectUsers = (id, params) => api.get(`/projects/${id}/users`);

export const generateFiles = (id, payload) => api.post(`/projects/${id}/generate-project-data`, payload);

export const generateProjectBasemap = (id, payload) => api.post(`/projects/${id}/tiles-generate`, payload);

export const getProject = (id) => api.get(`/projects/${id}`);

export const updateProject = (id, payload) => api.patch(`/projects/${id}`, payload);

export const deleteProject = (id, params) => api.delete(`/projects/${id}`, { params });

export const uploadProjectTaskBoundaries = (id, payload) =>
  api.post(`/projects/${id}/upload-task-boundaries`, { payload });

export const createStubProject = (payload, params) => api.post('/projects/stub', payload, { params });

export const getProjectMinimal = (id) => api.get(`/projects/${id}/minimal`);

export const downloadProjectBoundary = (id) => api.get(`/projects/${id}/download`);

export const downloadTaskBoundaries = (id) => api.get(`/projects/${id}/download_tasks`);

export const deleteEntity = (id, params) => api.delete(`/projects/entity/${id}`, { params });

export const unassignUserFromProject = (id, user_sub) => api.delete(`/projects/${id}/users/${user_sub}`);
