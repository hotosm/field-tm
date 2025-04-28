export function getCookieValue(name: string): string | null {
	const cookies = document.cookie.split('; ').map((cookie) => cookie.trim());
	for (const cookie of cookies) {
		// We take the first match, as multiple cookies may exist
		if (cookie.startsWith(`${name}=`)) {
			return decodeURIComponent(cookie.split('=').slice(1).join('='));
		}
	}
	return null;
}

export function setCookieValue(name: string, value: string, days = 365) {
	const expires = new Date(Date.now() + days * 86400 * 1000).toUTCString();
	document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}
