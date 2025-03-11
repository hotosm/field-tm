import { m } from '$translations/messages.js';

type drawerItemsType = {
	name: string;
	path: string;
};

export const drawerItems: drawerItemsType[] = [
	{
		name: m['header.about'](),
		path: 'https://docs.fmtm.dev/about/about/',
	},
	{
		name: m['header.guide_for_mappers'](),
		path: 'https://docs.fmtm.dev/manuals/mapping/',
	},
	{
		name: m['header.support'](),
		path: 'https://github.com/hotosm/fmtm/issues/',
	},
	{
		name: m['header.download_custom_odk_collect'](),
		path: 'https://github.com/hotosm/odkcollect/releases/download/v2024.3.5-entity-select/ODK-Collect-v2024.3.5-HOTOSM-FMTM.apk',
	},
];
