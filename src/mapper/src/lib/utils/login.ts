import type { LoginProviderKey } from '$store/common.svelte';

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

export const loginRedirect = async (provider: LoginProviderKey) => {
	try {
		let url: string | undefined;

		switch (provider) {
			case 'osm':
				url = `${import.meta.env.VITE_API_URL}/auth/login/osm/mapper`;
				break;
			case 'google':
				url = `${import.meta.env.VITE_API_URL}/auth/login/google`;
				break;
		}

		if (!url) return;

		const resp = await fetch(url);
		const data = await resp.json();
		window.location.href = data.login_url;
	} catch (error) {
		console.error('Login redirect failed:', error);
	}
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
