// The /auth/me endpoint does an UPSERT in the database, ensuring the user
// exists in the FMTM DB
export const getUserDetailsFromApi = async () => {
  const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
    credentials: 'include',
  });

  if (resp.status !== 200) {
    return false;
  }

  const apiUser = await resp.json();

  if (!apiUser) return false;

  return apiUser;
};

export const osmLoginRedirect = async () => {
  try {
    const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/osm-login`);
    const data = await resp.json();
    window.location = data.login_url;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
};

export const revokeCookie = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/logout`, { credentials: 'include' });
    if (!response.ok) {
      console.error('/auth/logout endpoint did not return 200 response');
    }
  } catch (error) {
    throw error;
  }
};
