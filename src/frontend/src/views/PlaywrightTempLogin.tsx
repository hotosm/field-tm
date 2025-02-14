// This file is a workaround to populate state.login.authDetails
// the auth is overridden when testing due to DEBUG=True on the backend,
// but we need to update the frontend state to show we are logged in

import { refreshCookies, getUserDetailsFromApi } from '@/utilfunctions/login';
import { CommonActions } from '@/store/slices/CommonSlice';
import CoreModules from '@/shared/CoreModules.js';
import { LoginActions } from '@/store/slices/LoginSlice';

async function PlaywrightTempAuth() {
  const dispatch = CoreModules.useAppDispatch();
  // Sets a cookie in the browser that is used for auth
  await refreshCookies();
  const refreshSuccess = await refreshCookies();
  if (!refreshSuccess) {
    const apiUser = await getUserDetailsFromApi();
    if (!apiUser) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Temp login failed. Try OSM.',
        }),
      );
      return;
    }
    dispatch(LoginActions.setAuthDetails(apiUser));
  } else {
    console.error('Failed to refresh cookies.');
  }
}

export default PlaywrightTempAuth;
