// The /auth/me endpoint does an UPSERT in the database, ensuring the user
// exists in the Field-TM DB
export const getUserDetailsFromApi = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Status: ${response.status}`);
    }

    return response.json();
  } catch (err) {
    console.error('Error retrieving user details:', err);
  }
};

export const refreshCookies = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/refresh`, {
      credentials: 'include',
    });

    if (!response.ok) {
      return false;
    }

    return true;
  } catch (err) {
    return false;
  }
};

export const osmLoginRedirect = async () => {
  try {
    const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/login/osm`);
    const data = await resp.json();
    window.location = data.login_url;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
};

export const revokeCookies = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/logout`, { credentials: 'include' });
    if (!response.ok) {
      console.error('/auth/logout endpoint did not return 200 response');
    }
  } catch (error) {
    throw error;
  }
};
