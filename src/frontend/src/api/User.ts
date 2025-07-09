import axios, { AxiosResponse } from 'axios';
import { AppDispatch } from '@/store/Store';
import { UserActions } from '@/store/slices/UserSlice';
import { projectUserInvites, userType } from '@/models/user/userModel';
import { paginationType } from '@/store/types/ICommon';
import { CommonActions } from '@/store/slices/CommonSlice';
import { NavigateFunction } from 'react-router-dom';

const VITE_API_URL = import.meta.env.VITE_API_URL;

export const GetUserListService = (url: string, params: { page: number; results_per_page: number; search: string }) => {
  return async (dispatch: AppDispatch) => {
    dispatch(UserActions.SetUserListLoading(true));

    const getUserList = async (url: string) => {
      try {
        const response: AxiosResponse<{ results: userType[]; pagination: paginationType }> = await axios.get(url, {
          params,
        });
        dispatch(UserActions.SetUserList(response.data));
      } catch (error) {
      } finally {
        dispatch(UserActions.SetUserListLoading(false));
      }
    };

    await getUserList(url);
  };
};

export const UpdateUserRole = (url: string, payload: { role: 'READ_ONLY' | 'ADMIN' | 'MAPPER' }) => {
  return async (dispatch: AppDispatch) => {
    const updateUserRole = async (url: string) => {
      dispatch(UserActions.SetUpdateUserRoleLoading(true));
      try {
        const response: AxiosResponse<userType> = await axios.patch(url, payload);
        dispatch(UserActions.UpdateUserList(response.data));
        dispatch(
          CommonActions.SetSnackBar({
            message: `Updated ${response.data.username}'s role to ${response.data.role} successfully`,
            variant: 'success',
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed to update user role',
          }),
        );
      } finally {
        dispatch(UserActions.SetUpdateUserRoleLoading(false));
      }
    };

    await updateUserRole(url);
  };
};

export const GetUserListForSelect = (url: string, params: { search: string; signin_type?: 'osm' | 'google' }) => {
  return async (dispatch: AppDispatch) => {
    dispatch(UserActions.SetUserListForSelectLoading(true));

    const getUserList = async (url: string) => {
      try {
        const response: AxiosResponse<{ sub: string; username: string }[]> = await axios.get(url, {
          params,
        });
        dispatch(UserActions.SetUserListForSelect(response.data));
      } catch (error) {
      } finally {
        dispatch(UserActions.SetUserListForSelectLoading(false));
      }
    };

    await getUserList(url);
  };
};

export const GetUserNames = (
  url: string,
  params: { org_id?: number; project_id?: number; search: string; signin_type?: 'osm' | 'google' },
) => {
  return async (dispatch: AppDispatch) => {
    const getUserNames = async (url: string, params: { org_id?: number; project_id?: number }) => {
      try {
        dispatch(UserActions.GetUserNamesLoading(true));
        const response: AxiosResponse<Pick<userType, 'sub' | 'username'>[]> = await axios.get(url, { params });
        dispatch(UserActions.SetUserNames(response.data));
      } catch (error) {
      } finally {
        dispatch(UserActions.GetUserNamesLoading(false));
      }
    };
    await getUserNames(url, params);
  };
};

export const AcceptInvite = (url: string, navigate: NavigateFunction) => {
  return async (dispatch: AppDispatch) => {
    const getProjectUserInvites = async (url: string) => {
      try {
        await axios.get(url);
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to accept invitation',
            duration: 6000,
          }),
        );
      } finally {
        navigate('/');
      }
    };
    await getProjectUserInvites(url);
  };
};

export const GetProjectUserInvites = (url: string, params: { project_id: number }) => {
  return async (dispatch: AppDispatch) => {
    const getProjectUserInvites = async (url: string) => {
      try {
        dispatch(UserActions.GetProjectUserInvitesLoading(true));
        const response: AxiosResponse<projectUserInvites[]> = await axios.get(url, { params });
        dispatch(UserActions.SetProjectUserInvites(response.data));
      } catch (error) {
      } finally {
        dispatch(UserActions.GetProjectUserInvitesLoading(false));
      }
    };
    await getProjectUserInvites(url);
  };
};

export const InviteNewUser = (
  url: string,
  values: { inviteVia: string; user: string[]; role: string; projectId: number },
) => {
  return async (dispatch: AppDispatch) => {
    const { inviteVia, role, user: users, projectId } = values;

    const inviteNewUser = async (url: string) => {
      try {
        dispatch(UserActions.InviteNewUserPending(true));
        let errorResponses: string[] = [];
        const promises = users?.map(async (user) => {
          try {
            const payload: Record<string, any> = { project_id: projectId, role };

            if (inviteVia === 'osm') {
              payload.osm_username = user.trim();
            } else {
              payload.email = user.trim();
            }

            const response = await axios.post(url, payload, { params: { project_id: projectId } });
            if (response.status === 201) {
              errorResponses = [...errorResponses, response.data.message];
            }
          } catch (error) {
            errorResponses = [...errorResponses, error.response.data.detail];
          }
        });
        await Promise.all(promises);
        dispatch(UserActions.SetProjectUserInvitesError(errorResponses));
      } catch (error) {
      } finally {
        dispatch(UserActions.InviteNewUserPending(false));
        dispatch(GetProjectUserInvites(`${VITE_API_URL}/users/invites`, { project_id: projectId }));
      }
    };
    await inviteNewUser(url);
  };
};
