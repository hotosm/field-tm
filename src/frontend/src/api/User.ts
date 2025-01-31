import axios, { AxiosResponse } from 'axios';
import { AppDispatch } from '@/store/Store';
import { UserActions } from '@/store/slices/UserSlice';
import { userType } from '@/models/user/userModel';
import { paginationType } from '@/store/types/ICommon';
import { CommonActions } from '@/store/slices/CommonSlice';

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
            open: true,
            message: `Updated ${response.data.username}'s role to ${response.data.role} successfully`,
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Failed to update user role',
            variant: 'error',
            duration: 2000,
          }),
        );
      } finally {
        dispatch(UserActions.SetUpdateUserRoleLoading(false));
      }
    };

    await updateUserRole(url);
  };
};

export const GetUserListForSelect = (
  url: string,
  params: { page: number; results_per_page: number; search: string },
) => {
  return async (dispatch: AppDispatch) => {
    dispatch(UserActions.SetUserListForSelectLoading(true));

    const getUserList = async (url: string) => {
      try {
        const response: AxiosResponse<{ results: userType[]; pagination: paginationType }> = await axios.get(url, {
          params,
        });
        dispatch(UserActions.SetUserListForSelect(response.data.results));
      } catch (error) {
      } finally {
        dispatch(UserActions.SetUserListForSelectLoading(false));
      }
    };

    await getUserList(url);
  };
};
