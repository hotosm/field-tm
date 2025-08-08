import { api } from '.';

export const getTasks = (params) => api.get('/tasks', { params });

export const getTaskActivity = (params) => api.get('tasks/activity', { params });

export const getTaskById = (id, params) => api.get(`/tasks/${id}`, { params });

export const addNewTaskEvent = (id, params) => api.post(`/tasks/${id}/event`, { params });

export const getTaskEventHistory = (id, params) => api.get(`/tasks/${id}/history`, { params });
