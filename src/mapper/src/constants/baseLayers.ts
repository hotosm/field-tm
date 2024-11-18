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

export const baseLayers = [stamenStyle, esriStyle, satellite];
