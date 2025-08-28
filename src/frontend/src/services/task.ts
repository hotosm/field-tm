import { api } from '.';
import {
  addNewTaskEventPayloadType,
  addNewTaskEventParamsType,
  getTasksParamsType,
  getTaskActivityParamsType,
  getTaskEventHistoryParamsType,
} from '@/types';

export const getTasks = (params: getTasksParamsType) => api.get('/tasks', { params });

export const getTaskActivity = (params: getTaskActivityParamsType) => api.get('tasks/activity', { params });

export const getTaskById = (id: number, params: getTasksParamsType) => api.get(`/tasks/${id}`, { params });

export const addNewTaskEvent = (id: number, payload: addNewTaskEventPayloadType, params: addNewTaskEventParamsType) =>
  api.post(`/tasks/${id}/event`, payload, { params });

export const getTaskEventHistory = (id: number, params: getTaskEventHistoryParamsType) =>
  api.get(`/tasks/${id}/history`, { params });
