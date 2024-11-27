type drawerItemsType = {
	name: string;
	path: string;
};

export const drawerItems: drawerItemsType[] = [
	{
		name: 'Explore Projects',
		path: `${window.location.origin}`,
	},
	{
		name: 'Learn',
		path: 'https://hotosm.github.io/fmtm',
	},
	{
		name: 'About',
		path: 'https://docs.fmtm.dev/About/',
	},
	{
		name: 'Support',
		path: 'https://github.com/hotosm/fmtm/issues/',
	},
	{
		name: 'Download Custom ODK Collect',
		path: 'https://github.com/hotosm/odkcollect/releases/download/v2024.2.4-entity-select/ODK-Collect-v2024.2.4-FMTM.apk',
	},
];
