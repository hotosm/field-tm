import { createPopup } from '@/utilfunctions/createPopup';

export const getUserDetailsFromApi = async (redirectTo: string = '/') => {
  const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/me/`, {
    credentials: 'include',
  });

  if (resp.status !== 200) {
    return false;
  }

  const apiUser = await resp.json();

  if (!apiUser) return false;

  const params = new URLSearchParams({
    username: apiUser.username,
    id: apiUser.id,
    picture: apiUser.profile_img,
    redirect_to: redirectTo,
    role: apiUser.role,
  }).toString();

  const redirectUrl = `/osmauth?${params}`;
  window.location.href = redirectUrl;

  return true;
};

export const createLoginWindow = async (redirectTo: string) => {
  // Create popup outside of request (required for Safari security)
  const popup = createPopup('OSM Auth', '');

  try {
    const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/osm-login/`);
    const data = await resp.json();

    if (!popup) {
      console.warn('Popup blocked or unavailable.');
      return;
    }

    // Set URL for popup from response
    popup.location = data.login_url;

    // Get OAuth2 authorization url, extract state
    const authUrl = new URL(data.login_url);
    const authParams = new URLSearchParams(authUrl.search);
    const responseState = authParams.get('state');

    const handleLoginPopup = (event) => {
      // OAuth2 state param validation
      if (event.data.authCode && event.data.state === responseState) {
        // Clean up the postMessage event listener
        window.removeEventListener('message', handleLoginPopup);

        const authCode = event.data.authCode;
        const state = event.data.state;
        const callbackUrl = `${import.meta.env.VITE_API_URL}/auth/callback/?code=${authCode}&state=${state}`;

        const completeLogin = async () => {
          // NOTE this encapsulates async methods to call sequentially
          // Sets a cookie in the browser that is used for auth
          await fetch(callbackUrl, { credentials: 'include' });
          await getUserDetailsFromApi(redirectTo);
        };
        completeLogin();
      } else {
        console.log('Login states do not match');
      }
    };

    // Add the postMessage event listener
    window.addEventListener('message', handleLoginPopup);
  } catch (error) {
    console.error('Error fetching data:', error);
  }
};

export const revokeCookie = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/logout/`, { credentials: 'include' });
    if (!response.ok) {
      console.error('/auth/logout endpoint did not return 200 response');
    }
  } catch (error) {
    throw error;
  }
};
