import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LoginActions } from '@/store/slices/LoginSlice';
import { getUserDetailsFromApi } from '@/utilfunctions/login';
import { useAppDispatch } from '@/types/reduxTypes';
import { Loader2 } from 'lucide-react';

function OsmAuth() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const [isSigningIn, setIsSigningIn] = useState(false);
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
          setIsSigningIn(true);
          const response = await fetch(
            `${import.meta.env.VITE_API_URL}/auth/callback/osm?code=${authCode}&state=${state}`,
            { credentials: 'include' },
          );

          if (!response.ok) {
            throw new Error(`Callback request failed with status ${response.status}`);
          }

          dispatch(LoginActions.setLoginModalOpen(false));

          if (requestedPath) {
            sessionStorage.removeItem('requestedPath');
            const { protocol, hostname, port } = window.location;
            if (hostname.startsWith('mapper.')) {
              // redirect to mapper frontend (navigate doesn't work as it's on svelte)
              window.location.href = `${protocol}//mapper.${hostname}${port ? `:${port}` : ''}/${requestedPath}`;
            } else {
              // Call /auth/me to populate the user details in the header
              const apiUser = await getUserDetailsFromApi();
              if (apiUser) {
                dispatch(LoginActions.setAuthDetails(apiUser));
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
        } finally {
          setIsSigningIn(false);
        }
      }
    };

    loginRedirect();
  }, [location.search]);

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <>
      {isSigningIn ? (
        <div className="fmtm-h-full fmtm-flex fmtm-flex-col fmtm-justify-center fmtm-items-center">
          <Loader2 className="fmtm-h-10 fmtm-w-10 fmtm-animate-spin fmtm-text-primaryRed" />
          <h3 className="fmtm-text-grey-700 fmtm-font-semibold">Signing in...</h3>
        </div>
      ) : null}
    </>
  );
}

export default OsmAuth;
