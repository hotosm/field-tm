// This file is a workaround to populate state.login.authDetails
// the auth is overridden when testing due to DEBUG=True on the backend,
// but we need to update the frontend state to show we are logged in

import axios from 'axios';
import { getUserDetailsFromApi } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';
import CoreModules from '@/shared/CoreModules.js';
import { LoginActions } from '@/store/slices/LoginSlice';

async function PlaywrightTempAuth() {
  const dispatch = CoreModules.useAppDispatch();
  // Sets a cookie in the browser that is used for auth
  await axios.get(`${import.meta.env.VITE_API_URL}/auth/temp-login`);

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
}

export default PlaywrightTempAuth;
