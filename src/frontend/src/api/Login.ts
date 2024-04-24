import axios from 'axios';
import { getUserDetailsFromApi } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';

export const TemporaryLoginService: Function = (url: string) => {
  return async (dispatch) => {
    const getTemporaryLogin = async (url) => {
      // Sets a cookie in the browser that is used for auth
      await axios.get(url);

      const loginSuccess = await getUserDetailsFromApi();
      if (!loginSuccess) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Temp login failed. Try OSM.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };

    await getTemporaryLogin(url);
  };
};
