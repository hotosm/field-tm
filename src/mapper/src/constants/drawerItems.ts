import { m } from '$translations/messages.js';

export type drawerItemsType = {
	name: string;
	path: string;
};

export const defaultDrawerItems: drawerItemsType[] = [
	{
		name: m['header.about'](),
		path: 'https://docs.fieldtm.hotosm.org/about/about/',
	},
	{
		name: m['header.guide_for_mappers'](),
		path: 'https://docs.fieldtm.hotosm.org/manuals/mapping/',
	},
	{
		name: m['header.support'](),
		path: 'https://github.com/hotosm/field-tm/issues/',
	},
	{
		name: m['header.translate'](),
		path: 'https://hosted.weblate.org/engage/hotosm',
	},
	{
		name: m['header.download_odk_collect'](),
		path: 'https://play.google.com/store/apps/details?id=org.odk.collect.android',
	},
];
