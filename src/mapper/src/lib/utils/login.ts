// The /auth/me endpoint does an UPSERT in the database, ensuring the user
// exists in the FMTM DB
export const getUserDetailsFromApi = async (fetchClient = fetch) => {
	try {
		const response = await fetchClient(`${import.meta.env.VITE_API_URL}/auth/me`, {
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

// Note the callback is handled in the management frontend under /osmauth,
// then the user is redirected back to the mapper frontend URL requested
export const osmLoginRedirect = async () => {
	try {
		const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/osm-login`);
		const data = await resp.json();
		window.location = data.login_url;
	} catch (error) {}
};

export const refreshCookies = async (fetchClient = fetch) => {
	try {
		const response = await fetchClient(`${import.meta.env.VITE_API_URL}/auth/refresh/mapper`, {
			credentials: 'include',
		});

		if (!response.ok) {
			throw new Error(`Status: ${response.status}`);
		}

		return response.json();
	} catch (err) {
		console.error('Error refreshing user cookie:', err);
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
