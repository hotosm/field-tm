import { writable } from 'svelte/store';

export const setAlert = writable({
	variant: '',
	message: '',
});
