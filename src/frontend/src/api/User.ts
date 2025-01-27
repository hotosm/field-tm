import axios, { AxiosResponse } from 'axios';
import { AppDispatch } from '@/store/Store';
import { UserActions } from '@/store/slices/UserSlice';
import { userType } from '@/models/user/userModel';

export const GetUserListService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(UserActions.SetUserListLoading(true));

    const getUserList = async (url: string) => {
      try {
        const response: AxiosResponse<userType[]> = await axios.get(url);
        dispatch(UserActions.SetUserList(response.data));
      } catch (error) {
      } finally {
        dispatch(UserActions.SetUserListLoading(false));
      }
    };

    await getUserList(url);
  };
};
