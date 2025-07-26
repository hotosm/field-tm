import { clearAllOPFS } from '$lib/fs/opfs';

// Open a new tab for each testing session and the storage will be wiped to start fresh
export async function clearAllDevCaches() {
	if (!import.meta.env.DEV) return;

	// Check key to prevent clearing multiple times per session
	if (sessionStorage.getItem('devStorageWiped')) return;

	console.warn('💥 Local dev mode: Clearing all caches and storage');

	// 1. Clear local/session storage
	localStorage.clear();
	sessionStorage.clear();

	// 2. Clear all caches (Cache Storage API)
	if ('caches' in window) {
		const cacheNames = await caches.keys();
		await Promise.all(cacheNames.map((name) => caches.delete(name)));
	}

	// 3. Clear OPFS storage
	await clearAllOPFS();

	// Set key to prevent clearing multiple times per session
	sessionStorage.setItem('devStorageWiped', 'true');
}
