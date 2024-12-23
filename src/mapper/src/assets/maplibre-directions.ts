// snapline: line from waypoint to road
export const layers = [
	{
		id: 'maplibre-gl-directions-snapline',
		type: 'line',
		source: 'maplibre-gl-directions',
		layout: {
			'line-cap': 'round',
			'line-join': 'round',
		},
		paint: {
			'line-dasharray': [2, 2],
			'line-color': '#000000',
			'line-opacity': 0.65,
			'line-width': 2,
		},
		filter: ['==', ['get', 'type'], 'SNAPLINE'],
	},

	// primary route
	{
		id: 'maplibre-gl-directions-routeline',
		type: 'line',
		source: 'maplibre-gl-directions',
		layout: {
			'line-cap': 'butt',
			'line-join': 'round',
		},
		paint: {
			'line-width': 12,
			'line-opacity': 1,
			'line-color': '#4285f4',
		},
		filter: ['==', ['get', 'route'], 'SELECTED'],
	},

	// alternative route
	{
		id: 'maplibre-gl-directions-alt-routeline',
		type: 'line',
		source: 'maplibre-gl-directions',
		layout: {
			'line-cap': 'butt',
			'line-join': 'round',
		},
		paint: {
			'line-width': 12,
			'line-opacity': 0.8,
			'line-color': '#547fff',
		},
		filter: ['==', ['get', 'route'], 'ALT'],
	},

	// only apply icon-style to the destination waypoint as we have icon for the origin
	{
		id: 'maplibre-gl-directions-waypoint',
		type: 'symbol',
		source: 'maplibre-gl-directions',
		layout: {
			'icon-image': 'location',
			'icon-anchor': 'bottom',
			'icon-ignore-placement': true,
			'icon-overlap': 'always',
			'icon-size': 0.5,
		},
		filter: ['all', ['==', ['get', 'type'], 'WAYPOINT'], ['==', ['get', 'category'], 'DESTINATION']],
	},
];
