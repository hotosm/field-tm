// import { browser } from '$app/environment';

// // Gets an existing value, else sets the default value passed
// export class LocalStore<T> {
//   value = $state<T>() as T;
//   key = '';

//   constructor(key: string, value: T) {
//     this.key = key;
//     this.value = value;

//     if (browser) {
//       const item = localStorage.getItem(key);
//       if (item) this.value = this.deserialize(item);
//     }

//     $effect(() => {
//       localStorage.setItem(this.key, this.serialize(this.value));
//     });
//   }

//   serialize(value: T): string {
//     return JSON.stringify(value);
//   }

//   deserialize(item: string): T {
//     return JSON.parse(item);
//   }
// }

// export function localStore<T>(key: string, value: T) {
//   return new LocalStore(key, value);
// }

export function getLocalStorage<T = string>(key: string): T | null {
	const value = localStorage.getItem(key);
	if (value === null) return null;

	try {
		return JSON.parse(value);
	} catch {
		return value as T; // Return as string if not valid JSON
	}
}

export function setLocalStorage<T>(key: string, value: T): void {
	localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value));
}
