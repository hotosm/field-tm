import { api } from '.';
import type {
  addProjectManagerParamsType,
  createProjectPayloadType,
  createStubProjectParamsType,
  createStubProjectPayloadType,
  deleteEntityParamsType,
  downloadFeaturesParamsType,
  generateDataExtractPayloadType,
  uploadDataExtractPayloadType,
  generateFilesPayloadType,
  generateProjectBasemapPayloadType,
  odkEntitiesGeojsonParamsType,
  previewSplitBySquarePayload,
  projectSummariesParamsType,
  projectUsersParamsType,
  taskSplitPayloadType,
  uploadProjectTaskBoundariesPayloadType,
  updateProjectPayloadType,
} from '@/api/project/types';

export const patchCreateProject = (payload: createProjectPayloadType, params: { project_id: number }) =>
  api.patch('/projects', payload, { params });

export const getProjectSummaries = (params: projectSummariesParamsType) => api.get('/projects/summaries', { params });

export const getOdkEntitiesGeojson = (id: number, params: odkEntitiesGeojsonParamsType) =>
  api.get(`/projects/${id}/entities`, { params });

export const getOdkEntitiesMappingStatuses = (project_id: number) =>
  api.get(`/projects/${project_id}/entities/statuses`);

export const getTilesList = (id: number) => api.get(`/projects/${id}/tiles`);

export const downloadFeatures = (params: downloadFeaturesParamsType) =>
  api.get('/projects/features/download', { params });

export const getContributors = (project_id: number) => api.get(`/projects/contributors/${project_id}`);

export const taskSplit = (payload: FormData) => api.post('/projects/task-split', payload);

export const previewSplitBySquare = (payload: FormData) => api.post('/projects/preview-split-by-square', payload);

export const generateDataExtract = (payload: FormData, params: { project_id: number }) =>
  api.post('/projects/generate-data-extract', payload, { params });

export const uploadDataExtract = (payload: uploadDataExtractPayloadType, params: { project_id: number }) =>
  api.post('/projects/upload-data-extract', payload, { params });

export const addProjectManager = (params: addProjectManagerParamsType) => api.post('/projects/add-manager', { params });

export const getProjectUsers = (project_id: number, params: projectUsersParamsType) =>
  api.get(`/projects/${project_id}/users`, { params });

export const generateFiles = (project_id: number, payload: generateFilesPayloadType) =>
  api.post(`/projects/${project_id}/generate-project-data`, payload);

export const generateProjectBasemap = (id: number, payload: generateProjectBasemapPayloadType) =>
  api.post(`/projects/${id}/tiles-generate`, payload);

export const getProject = (project_id: number) => api.get(`/projects/${project_id}`);

export const updateProject = (project_id: number, payload: updateProjectPayloadType) =>
  api.patch(`/projects/${project_id}`, payload);

export const deleteProject = (project_id: number, params: { org_id: number }) =>
  api.delete(`/projects/${project_id}`, { params });

export const uploadProjectTaskBoundaries = (project_id: number, payload: uploadProjectTaskBoundariesPayloadType) =>
  api.post(`/projects/${project_id}/upload-task-boundaries`, payload);

export const createStubProject = (payload: createStubProjectPayloadType, params: createStubProjectParamsType) =>
  api.post('/projects/stub', payload, { params });

export const getProjectMinimal = (project_id: number) => api.get(`/projects/${project_id}/minimal`);

export const downloadProjectBoundary = (project_id: number) => api.get(`/projects/${project_id}/download`);

export const downloadTaskBoundaries = (project_id: number) => api.get(`/projects/${project_id}/download_tasks`);

export const deleteEntity = (entity_uuid: string, params: deleteEntityParamsType) =>
  api.delete(`/projects/entity/${entity_uuid}`, { params });

export const unassignUserFromProject = (project_id: number, user_sub: string) =>
  api.delete(`/projects/${project_id}/users/${user_sub}`);
