import oamLogo from '$assets/images/oam-logo.svg';

export const osmStyle = {
	id: 'OSM Raster',
	version: 8,
	name: 'OpenStreetMap',
	sources: {
		osm: {
			type: 'raster',
			tiles: [
				'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
				'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
				'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
			],
			minzoom: 0,
			maxzoom: 19,
			attribution:
				'© <a target="_blank" rel="noopener" href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
		},
	},
	layers: [
		{
			id: 'osm',
			type: 'raster',
			source: 'osm',
			layout: {
				visibility: 'visible',
			},
		},
	],
};

let stamenStyle = {
	id: 'Stamen Raster',
	version: 8,
	name: 'Black & White',
	sources: {
		stamen: {
			type: 'raster',
			tiles: ['https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png'],
			minzoom: 0,
			maxzoom: 19,
			attribution: `© <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> <a href="https://stamen.com/" target="_blank">
           © Stamen Design</a> 
           © <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a>
           `,
		},
	},
	layers: [
		{
			id: 'stamen',
			type: 'raster',
			source: 'stamen',
			layout: {
				visibility: 'visible',
			},
		},
	],
};

let esriStyle = {
	id: 'ESRI Raster',
	version: 8,
	name: 'ESRI',
	sources: {
		esri: {
			type: 'raster',
			tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
			minzoom: 0,
			maxzoom: 19,
			attribution: '© ESRI',
		},
	},
	layers: [
		{
			id: 'esri',
			type: 'raster',
			source: 'esri',
			layout: {
				visibility: 'visible',
			},
		},
	],
};

let satellite = {
	id: 'Satellite',
	version: 8,
	name: 'Satellite',
	sources: {
		satellite: {
			type: 'raster',
			tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
			tileSize: 256,
			attribution: 'ArcGIS',
		},
	},
	layers: [
		{
			id: 'satellite',
			type: 'raster',
			source: 'satellite',
			layout: {
				visibility: 'visible',
			},
		},
	],
};

export const customStyle = {
	id: 'Custom',
	version: 8,
	name: 'Custom',
	metadata: {
		thumbnail: oamLogo,
	},
	sources: {
		custom: {
			type: 'raster',
			url: '',
			tileSize: 512,
			attribution: 'Protmaps',
		},
	},
	layers: [
		{
			id: 'custom',
			type: 'raster',
			source: 'custom',
			layout: {
				visibility: 'visible',
			},
		},
	],
};

export const baseLayers = [stamenStyle, esriStyle, satellite];
