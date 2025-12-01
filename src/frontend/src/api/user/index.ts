import { useMutation, UseMutationOptions, useQuery } from '@tanstack/react-query';
import {
  acceptInvite,
  deleteUserById,
  getProjectUserInvites,
  getUserById,
  getUserList,
  getUsers,
  inviteNewUser,
  updateExistingUser,
} from '@/services/user';
import type { TMutationOptions, TQueryOptions } from '@/types';
import type {
  deleteUserByIdParamsType,
  getProjectUserInvitesParamsType,
  getUserListParamsType,
  getUserListType,
  getUsersParamsType,
  inviteNewUserParamsType,
  projectUserInvite,
  updateExistingUserPayloadType,
  userType,
} from './types';
import { paginationType } from '@/store/types/ICommon';
import { project_roles } from '@/types/enums';
import { AxiosError } from 'axios';

export function useGetUsersQuery({
  params,
  options,
}: {
  params: getUsersParamsType;
  options: TQueryOptions<{ results: userType[]; pagination: paginationType }>;
}) {
  return useQuery({
    queryFn: () => getUsers(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useGetUserListQuery({
  params,
  options,
}: {
  params: getUserListParamsType;
  options: TQueryOptions<getUserListType[]>;
}) {
  return useQuery({
    queryFn: () => getUserList(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useProjectUserInvitesQuery({
  params,
  options,
}: {
  params: getProjectUserInvitesParamsType;
  options: TQueryOptions<projectUserInvite[]>;
}) {
  return useQuery({
    queryFn: () => getProjectUserInvites(params),
    select: (data) => data.data,
    ...options,
  });
}

export function useInviteNewUserMutation(
  options: UseMutationOptions<
    string[],
    AxiosError<Error>,
    {
      payload: { inviteVia: string; user: string[]; role: project_roles; projectId: number };
      params: inviteNewUserParamsType;
    }
  >,
) {
  return useMutation({
    mutationFn: async ({ payload, params }) => {
      const results: string[] = [];
      const { inviteVia, user, role, projectId } = payload;

      const requests = user.map(async (u) => {
        const body = {
          project_id: projectId,
          role,
          ...(inviteVia === 'osm' ? { osm_username: u.trim() } : { email: u.trim() }),
        };

        try {
          const res = await inviteNewUser(body, params);
          if (res.status === 201) {
            results.push(res.data.message);
          }
        } catch (err: any) {
          const msg = err?.response?.data?.detail || 'Something went wrong';
          results.push(msg);
        }
      });

      await Promise.all(requests);
      return results;
    },
    ...options,
  });
}

export function useAcceptInviteQuery({ token, options }: { token: string; options: TQueryOptions<any> }) {
  return useQuery({
    queryFn: () => acceptInvite(token),
    select: (data) => data.data,
    ...options,
  });
}

export function useUpdateExistingUserMutation({
  user_sub,
  options,
}: {
  user_sub: string;
  options: TMutationOptions<any, updateExistingUserPayloadType>;
}) {
  return useMutation({
    mutationKey: ['update-user', user_sub],
    mutationFn: (payload: updateExistingUserPayloadType) => updateExistingUser(user_sub, payload),
    ...options,
  });
}

export function useGetUserByIdQuery({ id, options }: { id: string; options: TQueryOptions<any> }) {
  return useQuery({
    queryFn: () => getUserById(id),
    select: (data) => data.data,
    ...options,
  });
}

export function useDeleteUserByIdMutation({
  id,
  params,
  options,
}: {
  id: string;
  params: deleteUserByIdParamsType;
  options: TMutationOptions<any, void>;
}) {
  return useMutation({
    mutationKey: ['delete-user', id],
    mutationFn: () => deleteUserById(id, params),
    ...options,
  });
}
