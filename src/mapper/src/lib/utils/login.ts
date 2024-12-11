// Note the callback is handled in the management frontend under /osmauth,
// then the user is redirected back to the mapper frontend URL requested
export const osmLoginRedirect = async () => {
	try {
		const resp = await fetch(`${import.meta.env.VITE_API_URL}/auth/osm-login`);
		const data = await resp.json();
		window.location = data.login_url;
	} catch (error) {}
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
