import environment from '../environment';
import { createPopup } from './createPopup';
declare global {
  interface Window {
    authComplete: any;
  }
}

// Code taken from https://github.com/mapbox/osmcha-frontend/blob/master/src/utils/create_popup.js

export const createLoginWindow = (redirectTo) => {
  const popup = createPopup('OSM auth', '');
  fetch(`${environment.baseApiUrl}/auth/osm_login/`)
    .then((resp) => resp.json())
    .then((resp) => {
      //@ts-ignore
      popup.location = resp.login_url;
      // Perform token exchange.
      // Get the URL from which you want to extract parameters
      const url = new URL(resp.login_url);

      // Get the search parameters from the URL
      const searchParams = new URLSearchParams(url.search);

      // Retrieve individual parameters by name
      const responseState = searchParams.get('state');
      window.authComplete = (authCode, state) => {
        let callback_url = `${environment.baseApiUrl}/auth/callback/?code=${authCode}&state=${state}`;

        try {
          if (responseState === state) {
            fetch(callback_url)
              .then((resp) => resp.json())
              .then((res) => {
                fetch(`${environment.baseApiUrl}/auth/me/`, {
                  headers: {
                    'access-token': res.access_token.access_token,
                  },
                })
                  .then((resp) => resp.json())
                  .then((userRes) => {
                    const params = new URLSearchParams({
                      username: userRes.user_data.username,
                      osm_oauth_token: res.access_token.access_token,
                      id: userRes.user_data.id,
                      picture: userRes.user_data.img_url,
                      redirect_to: redirectTo,
                    }).toString();
                    let redirectUrl = `/osmauth?${params}`;
                    window.location.href = redirectUrl;
                  });
              });
          } else {
            throw new Error('States do not match');
          }
        } catch (error) {
          console.log(error, 'error');
        }
      };
    });
};
