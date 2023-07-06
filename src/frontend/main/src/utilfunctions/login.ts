// import { fetchLocalJSONAPI } from '../network/genericJSONRequest';
// import * as safeStorage from '../utils/safe_storage';

import environment from "../environment";

// import { OSM_REDIRECT_URI } from '../config';
const OSM_REDIRECT_URI = "http://127.0.0.1:8080/authorized"
// Code taken from https://github.com/mapbox/osmcha-frontend/blob/master/src/utils/create_popup.js
export function createPopup(title: string = 'Authentication', location: string) {
  const width = 500;
  const height = 630;
  const settings = [
    ['width', width],
    ['height', height],
    ['left', window.innerWidth / 2 - width / 2],
    ['top', window.innerHeight / 2 - height / 2],
  ]
    .map((x) => x.join('='))
    .join(',');

  const popup = window.open(location, '_blank', settings);
  if (!popup) return;

  return popup;
}

export const createLoginWindow = (redirectTo) => {
  const popup = createPopup('OSM auth', '');
  // let url = `system/authentication/login/?redirect_uri=${OSM_REDIRECT_URI}`;
  fetch(`${environment.baseApiUrl}/auth/osm_login/`).then((resp) => resp.json()).then((resp) => {
    popup.location = resp.login_url;
    // Perform token exchange.
    // Get the URL from which you want to extract parameters
    const url = new URL(resp.login_url);

    // Get the search parameters from the URL
    const searchParams = new URLSearchParams(url.search);

    // Retrieve individual parameters by name
    const code = searchParams.get('code');
    const responseState = searchParams.get('state');
    window.authComplete = (authCode, state) => {
      let callback_url = `${environment.baseApiUrl}/auth/callback/?code=${authCode}&state=${state}`;

      try {
        console.log(resp, 'resp');
        console.log(responseState, 'state');
        if (responseState === state) {
          fetch(callback_url).then((resp) => resp.json()).then((res) => {
            console.log(res.data, 'res token wala');
            console.log(JSON.stringify(res.data), 'JSON stringify res token wala');
            console.log(res, '2nd res token wala');
            console.log(JSON.stringify(res), '2nd JSON stringify res token wala');

            fetch(`${environment.baseApiUrl}/auth/me/`, {
              headers: {
                "access-token": res.access_token.access_token
                // 'Content-Type': 'application/x-www-form-urlencoded',
              }
            }).then((resp) => resp.json()).then((userRes) => {
              // localStorage.setItem("user", JSON.stringify(res.user_data));
              // window.close();
              console.log(userRes,'userRes')
              console.log(JSON.stringify(userRes),' string userRes')
              const params = new URLSearchParams({
                username: userRes.user_data.username,
                osm_oauth_token: res.access_token.access_token,
                // session_token: res.session_token,
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
