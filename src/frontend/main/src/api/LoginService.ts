import axios from 'axios';
import { LoginActions } from '../store/slices/LoginSlice';
import { SignInModel, SingUpModel } from '../models/login/loginModel';
import { CommonActions } from '../store/slices/CommonSlice';

export const SignUpService: Function = (url: string, body: SingUpModel) => {
  return async (dispatch) => {
    dispatch(CommonActions.SetLoading(true));

    const createUser = async (url, body) => {
      try {
        const createUserData = await axios.post(url, body);
        const resp: any = createUserData.data;
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'User Successfully Created.',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error: any) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error?.response?.data?.detail || 'Error in creating user.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CommonActions.SetLoading(false));
      }
    };

    await createUser(url, body);
  };
};

export const SignInService: Function = (url: string, body: SignInModel) => {
  return async (dispatch) => {
    dispatch(CommonActions.SetLoading(true));

    const signIn = async (url, body) => {
      try {
        const fetchUsers = await axios.get(url);
        const resp: any = fetchUsers.data;
        const userIndex = resp.findIndex((user) => user.username.toString() == body.username.toString());

        if (userIndex != -1) {
          if (resp[userIndex].hasOwnProperty('id')) {
            dispatch(LoginActions.SetLoginToken(resp[userIndex]));
            dispatch(
              CommonActions.SetSnackBar({
                open: true,
                message: 'Successfully Logged in.',
                variant: 'success',
                duration: 2000,
              }),
            );
            dispatch(CommonActions.SetLoading(false));
          } else {
            dispatch(
              CommonActions.SetSnackBar({
                open: true,
                message: "User does't exist",
                variant: 'error',
                duration: 2000,
              }),
            );
            dispatch(CommonActions.SetLoading(false));
          }
        } else {
          dispatch(
            CommonActions.SetSnackBar({
              open: true,
              message: "User does't exist",
              variant: 'error',
              duration: 2000,
            }),
          );
          dispatch(CommonActions.SetLoading(false));
        }
      } catch (error) {
        CommonActions.SetSnackBar({
          open: true,
          message: "User does't exist",
          variant: 'error',
          duration: 2000,
        });
        dispatch(CommonActions.SetLoading(false));
      }
    };

    await signIn(url, body);
  };
};
