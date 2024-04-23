import axios from 'axios';

export const TemporaryLoginService: Function = (url: string) => {
  return async (dispatch) => {
    const getTemporaryLogin = async (url) => {
      const login = await axios.get(url);
      const token = login.data.access_token;

      fetch(`${import.meta.env.VITE_API_URL}/auth/me/`, {
        headers: { 'access-token': token },
      })
        .then((resp) => resp.json())
        .then((userRes) => {
          const params = new URLSearchParams({
            username: userRes.username,
            osm_oauth_token: token,
            id: userRes.id,
            picture: userRes.profile_img,
            redirect_to: '/',
            role: userRes.role,
          }).toString();
          const redirectUrl = `/osmauth?${params}`;
          window.location.href = redirectUrl;
        });
      try {
      } catch (error) {}
    };

    await getTemporaryLogin(url);
  };
};
