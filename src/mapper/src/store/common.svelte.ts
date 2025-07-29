import { getCookieValue, setCookieValue } from '$lib/fs/cookies';
import type { Basemap } from '$lib/map/basemaps';
import { getBasemapList } from '$lib/map/basemaps';
import type { drawerItemsType } from '$constants/drawerItems';
import { getLocale as getParaglideLocale, locales } from '$translations/runtime.js';

export const LOGIN_PROVIDER_KEYS = ['osm', 'google'] as const;
export type LoginProviderKey = (typeof LOGIN_PROVIDER_KEYS)[number];
export interface LoginProviders {
	osm: boolean;
	google: boolean;
}
interface ConfigJson {
	logoUrl: string;
	logoText: string;
	cssFile: string;
	cssFileWebforms: string;
	enableWebforms: boolean;
	loginProviders: LoginProviders;
	sidebarItemsOverride: drawerItemsType[];
}

interface AlertDetails {
	variant: 'success' | 'default' | 'warning' | 'danger';
	message: string;
	duration?: number;
}

let alert: AlertDetails = $state({ variant: 'default', message: '', duration: 4000 });
let projectSetupStep: number | null = $state(null);
let projectBasemaps: Basemap[] = $state([]);
let projectPmtilesUrl: string | null = $state(null);
let selectedTab: string = $state('map');
let config: ConfigJson | null = $state(null);
let useOdkCollectOverride: boolean = $state(false);
let enableWebforms = $derived<boolean>(!useOdkCollectOverride && config?.enableWebforms ? true : false);
let offlineDataIsSyncing: boolean = $state(false);
let offlineSyncPercentComplete: number | null = $state(null);

function getCommonStore() {
	function getLocaleFromStorage() {
		// Priority 1: cookie (defined previously)
		const cookieLocale = getCookieValue('PARAGLIDE_LOCALE');
		if (cookieLocale) {
			setNewLocale(cookieLocale);
			return cookieLocale;
		}

		// Priority 2: browser locale
		// We don't differentiate US and UK English, but all others we want the variants (e.g. pt-BR)
		const browserLocale = navigator.language.startsWith('en')
			? navigator.language.trim().split(/-|_/)[0]
			: navigator.language.trim();
		if (browserLocale) {
			setNewLocale(browserLocale);
			return browserLocale;
		}

		// Priority 3: from paraglide
		const fallbackLocale = getParaglideLocale();
		setNewLocale(fallbackLocale);
		return fallbackLocale;
	}

	function setNewLocale(newLocale: string) {
		if (!locales.includes(newLocale)) {
			console.warn(`Selected locale is not available: ${newLocale}. Setting to default 'en'.`);
			newLocale = 'en';
		}
		setCookieValue('PARAGLIDE_LOCALE', newLocale);
	}

	return {
		get selectedTab() {
			return selectedTab;
		},
		setSelectedTab: (tab: string) => (selectedTab = tab),
		get locale() {
			return getLocaleFromStorage();
		},
		setLocale: setNewLocale,
		get config() {
			return config;
		},
		setConfig: (fetchedConfig: ConfigJson) => (config = fetchedConfig),
		setUseOdkCollectOverride: (isEnabled: boolean) => (useOdkCollectOverride = isEnabled),
		get enableWebforms() {
			return enableWebforms;
		},
		get offlineDataIsSyncing() {
			return offlineDataIsSyncing;
		},
		setOfflineDataIsSyncing(newVal: boolean) {
			offlineDataIsSyncing = newVal;
		},
		get offlineSyncPercentComplete() {
			return offlineSyncPercentComplete;
		},
		setOfflineSyncPercentComplete(newVal: number | null) {
			if (newVal === null) {
				offlineSyncPercentComplete = newVal;
			} else {
				// Round and don't allow more than 100%
				offlineSyncPercentComplete = Math.min(100, Math.round(newVal));
			}
		},
	};
}

function getAlertStore() {
	return {
		get alert() {
			return alert;
		},
		setAlert: (alertDetails: AlertDetails) =>
			(alert = {
				variant: alertDetails.variant,
				message: alertDetails.message,
				duration: alertDetails.duration || 4000,
			}),
		clearAlert: (alertDetails: AlertDetails) => (alert = { variant: 'default', message: '', duration: 4000 }),
	};
}

function getProjectSetupStepStore() {
	return {
		get projectSetupStep() {
			return projectSetupStep;
		},
		setProjectSetupStep: (step: number) => (projectSetupStep = step),
	};
}

function getProjectBasemapStore() {
	async function refreshBasemaps(projectId: number) {
		const basemaps = await getBasemapList(projectId);
		setProjectBasemaps(basemaps);
	}

	function setProjectBasemaps(basemapArray: Basemap[]) {
		// First we sort by recent first, created_at string datetime key
		const sortedBasemaps = basemapArray.sort((a, b) => {
			return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
		});
		projectBasemaps = sortedBasemaps;
	}

	return {
		get projectBasemaps() {
			return projectBasemaps;
		},
		setProjectBasemaps: setProjectBasemaps,
		refreshBasemaps: refreshBasemaps,

		get projectPmtilesUrl() {
			return projectPmtilesUrl;
		},
		setProjectPmtilesUrl: (url: string) => {
			projectPmtilesUrl = url;
		},
	};
}

export { getAlertStore, getProjectSetupStepStore, getProjectBasemapStore, getCommonStore };
