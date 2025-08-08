import { api } from '.';

export const getUsers = (params) => api.get('/users', { params });

export const getUserList = () => api.get('/users/usernames');

export const getProjectUserInvites = () => api.get('/users/invites');

export const inviteNewUser = () => api.get('/users/invite');

export const acceptInvite = (token) => api.get(`/users/invite/${token}`);

export const updateExistingUser = (id) => api.get(`/users/${id}`);

export const getUserById = (id) => api.get(`/users/${id}`);

export const deleteUserById = (id) => api.delete(`/users/${id}`);
