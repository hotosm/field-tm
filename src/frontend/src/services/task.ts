import { api } from '.';
import { addNewTaskEventPayloadType, addNewTaskEventParamsType } from '@/types';

export const getTasks = (params) => api.get('/tasks', { params });

export const getTaskActivity = (params) => api.get('tasks/activity', { params });

export const getTaskById = (id, params) => api.get(`/tasks/${id}`, { params });

export const addNewTaskEvent = (id: number, payload: addNewTaskEventPayloadType, params: addNewTaskEventParamsType) =>
  api.post(`/tasks/${id}/event`, payload, { params });

export const getTaskEventHistory = (id, params) => api.get(`/tasks/${id}/history`, { params });
