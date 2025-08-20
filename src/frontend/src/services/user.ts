import { api } from '.';
import type {
  deleteUserByIdParamsType,
  getProjectUserInvitesParamsType,
  getUserListParamsType,
  getUsersParamsType,
  inviteNewUserParamsType,
  inviteNewUserPayloadType,
  updateExistingUserPayloadType,
} from '@/api/user/types';

export const getUsers = (params: getUsersParamsType) => api.get('/users', { params });

export const getUserList = (params: getUserListParamsType) => api.get('/users/usernames', { params });

export const getProjectUserInvites = (params: getProjectUserInvitesParamsType) => api.get('/users/invites', { params });

export const inviteNewUser = (payload: inviteNewUserPayloadType, params: inviteNewUserParamsType) =>
  api.post('/users/invite', payload, { params });

export const acceptInvite = (token: string) => api.get(`/users/invite/${token}`);

export const updateExistingUser = (user_sub: string, payload: updateExistingUserPayloadType) =>
  api.patch(`/users/${user_sub}`, payload);

export const getUserById = (id: string) => api.get(`/users/${id}`);

export const deleteUserById = (id: string, params: deleteUserByIdParamsType) => api.delete(`/users/${id}`, { params });
