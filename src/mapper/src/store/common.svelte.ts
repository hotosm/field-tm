import { getLocalStorage, setLocalStorage } from '$lib/fs/local-storage.svelte';
import type { Basemap } from '$lib/utils/basemaps';
import { getBasemapList } from '$lib/utils/basemaps';

import { languageTag } from '$translations/runtime.js';

interface ConfigJson {
	logoUrl: string;
	logoText: string;
	cssFile: string;
}

interface AlertDetails {
	variant: 'success' | 'default' | 'warning' | 'danger';
	message: string;
}

let alert: AlertDetails = $state({ variant: 'default', message: '' });
let projectSetupStep: number | null = $state(null);
let projectBasemaps: Basemap[] = $state([]);
let projectPmtilesUrl: string | null = $state(null);
let selectedTab: string = $state('map');
let locale: string = $state(getLocalStorage('locale') ?? languageTag());
let config: ConfigJson | null = $state(null);

function getCommonStore() {
	return {
		get selectedTab() {
			return selectedTab;
		},
		setSelectedTab: (tab: string) => (selectedTab = tab),
		get locale() {
			return locale;
		},
		setLocale: (newLocale: string) => {
			setLocalStorage('locale', newLocale);
			locale = newLocale;
		},
		get config() {
			return config;
		},
		setConfig: (fetchedConfig: ConfigJson) => (config = fetchedConfig),
	};
}

function getAlertStore() {
	return {
		get alert() {
			return alert;
		},
		setAlert: (alertDetails: AlertDetails) =>
			(alert = { variant: alertDetails.variant, message: alertDetails.message }),
		clearAlert: (alertDetails: AlertDetails) => (alert = { variant: 'default', message: '' }),
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
