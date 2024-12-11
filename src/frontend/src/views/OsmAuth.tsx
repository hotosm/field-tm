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
  const [error, setError] = useState<string | null>(null);
  const requestedPath = sessionStorage.getItem('requestedPath');

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
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL}/auth/callback?code=${authCode}&state=${state}`,
            { credentials: 'include' },
          );

          if (!response.ok) {
            throw new Error(`Callback request failed with status ${response.status}`);
          }

          setIsReadyToRedirect(true);
          dispatch(LoginActions.setLoginModalOpen(false));

          if (requestedPath) {
            sessionStorage.removeItem('requestedPath');
            if (requestedPath.includes('mapnow')) {
              // redirect to mapper frontend (navigate doesn't work as it's on svelte)
              window.location.href = `${window.location.origin}${requestedPath}`;
            } else {
              // Call /auth/me to populate the user details in the header
              const apiUser = await getUserDetailsFromApi();
              if (apiUser) {
                dispatch(LoginActions.setAuthDetails(apiUser));
                // To prevent calls to /auth/me in future
                localStorage.setItem('fmtm-user-exists', 'true');
              } else {
                console.error('Failed to fetch user details after cookie refresh.');
              }
              // Then navigate to the originally requested url
              navigate(`${requestedPath}`);
            }
          }
        } catch (err) {
          console.error('Error during callback:', err);
          setError('Failed to authenticate. Please try again.');
        }
      }
    };

    loginRedirect();
  }, [dispatch, location.search, navigate, requestedPath]);

  if (error) {
    return <div>Error: {error}</div>;
  }

  return <>{!isReadyToRedirect ? null : <div>redirecting</div>}</>;
}

export default OsmAuth;
