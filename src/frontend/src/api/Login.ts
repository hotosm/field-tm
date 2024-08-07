import axios from 'axios';
import { getUserDetailsFromApi } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';
import { LoginActions } from '@/store/slices/LoginSlice';

export const TemporaryLoginService: Function = (url: string) => {
  return async (dispatch) => {
    const getTemporaryLogin = async (url: string) => {
      // Sets a cookie in the browser that is used for auth
      await axios.get(url);

      const apiUser = await getUserDetailsFromApi();
      if (!apiUser) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Temp login failed. Try OSM.',
            variant: 'error',
            duration: 2000,
          }),
        );
        return;
      }

      dispatch(LoginActions.setAuthDetails(apiUser));
    };

    await getTemporaryLogin(url);
  };
};
