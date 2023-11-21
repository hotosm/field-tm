import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LoginActions } from '../store/slices/LoginSlice';
import CoreModules from '../shared/CoreModules.js';

function Authorized() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = CoreModules.useAppDispatch();
  const [isReadyToRedirect, setIsReadyToRedirect] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    let authCode = params.get('code');
    let state = params.get('state');

    // First case: authCode is passed
    // return to get user details
    if (authCode !== null) {
      window.opener.postMessage({ authCode, state }, '*');
      window.close();
      return;
    }

    // Second case: not authCode is passed
    // persist user details in state
    const id = params.get('id');
    const username = params.get('username');
    const sessionToken = params.get('session_token');
    const osm_oauth_token = params.get('osm_oauth_token');
    const picture = params.get('picture');
    dispatch(LoginActions.setAuthDetails(username, sessionToken, osm_oauth_token));
    dispatch(LoginActions.SetLoginToken({ username, id, sessionToken, osm_oauth_token, picture }));

    const redirectUrl = params.get('redirect_to') || '/';
    setIsReadyToRedirect(true);
    navigate(redirectUrl);
  }, [dispatch, location.search, navigate]);

  return <>{!isReadyToRedirect ? null : <div>redirecting</div>}</>;
}

export default Authorized;
