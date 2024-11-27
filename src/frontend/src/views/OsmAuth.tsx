import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules.js';
import { LoginActions } from '@/store/slices/LoginSlice';
import { getUserDetailsFromApi } from '@/utilfunctions/login';

function OsmAuth() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = CoreModules.useAppDispatch();
  const [isReadyToRedirect, setIsReadyToRedirect] = useState(false);
  const requestedPath = localStorage.getItem('requestedPath');

  useEffect(() => {
    // Redirect workaround required for localhost, until PR is merged:
    // https://github.com/openstreetmap/openstreetmap-website/pull/4287
    if (window.location.href.includes('127.0.0.1:7051')) {
      // Pass through same url params
      window.location.href = `http://fmtm.localhost:7050${location.pathname}${location.search}`;
      return;
    }

    const params = new URLSearchParams(location.search);
    let authCode = params.get('code');
    let state = params.get('state');

    const loginRedirect = async () => {
      // authCode is passed from OpenStreetMap redirect, so get cookie, then redirect
      if (authCode) {
        const callbackUrl = `${import.meta.env.VITE_API_URL}/auth/callback?code=${authCode}&state=${state}`;

        const completeLogin = async () => {
          // NOTE this encapsulates async methods to call sequentially
          // Sets a cookie in the browser that is used for auth
          await fetch(callbackUrl, { credentials: 'include' });
          const apiUser = await getUserDetailsFromApi();
          dispatch(LoginActions.setAuthDetails(apiUser));
        };
        await completeLogin();
      }

      setIsReadyToRedirect(true);
      dispatch(LoginActions.setLoginModalOpen(false));

      if (requestedPath) {
        if (requestedPath.includes('mapnow')) {
          // redirect to mapper frontend (navigate doesn't work as it's on svelte)
          window.location.href = `${window.location.origin}${requestedPath}`;
        } else {
          navigate(`${requestedPath}`);
          localStorage.removeItem('requestedPath');
        }
      }
    };
    loginRedirect();
  }, [dispatch, location.search, navigate]);

  return <>{!isReadyToRedirect ? null : <div>redirecting</div>}</>;
}

export default OsmAuth;
