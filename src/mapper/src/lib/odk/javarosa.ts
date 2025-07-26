import type { Geometry as GeoJSONGeometry } from 'geojson';

export function geojsonGeomToJavarosa(geometry: GeoJSONGeometry) {
	if (geometry.type === 'GeometryCollection') {
		console.error('Unsupported GeoJSON type: GeometryCollection');
		return;
	}

	if (!geometry || !geometry.type || !geometry.coordinates) {
		throw new Error('Invalid GeoJSON feature: Missing geometry or coordinates.');
	}

	// Normalize geometries into a common structure for processing
	let coordinates: any[] = [];
	switch (geometry.type) {
		case 'Point':
			coordinates = [[geometry.coordinates]]; // [[x, y]]
			break;
		case 'LineString':
		case 'MultiPoint':
			coordinates = [geometry.coordinates]; // [[x, y], [x, y]]
			break;
		case 'Polygon':
		case 'MultiLineString':
			coordinates = geometry.coordinates; // [[[x, y], [x, y]]]
			break;
		case 'MultiPolygon':
			coordinates = geometry.coordinates.flat(); // Flatten [[[...]], [[...]]]
			break;
		default:
			throw new Error(`Unsupported GeoJSON geometry type: ${geometry}`);
	}

	// Convert to JavaRosa format
	const javarosaGeometry = coordinates
		.flatMap((polygonOrLine) =>
			polygonOrLine.map(([longitude, latitude]: [number, number]) => `${latitude} ${longitude} 0.0 0.0`),
		)
		.join(';');

	// Must append a final ; to finish the geom
	return `${javarosaGeometry};`;
}

export function javarosaToGeojsonGeom(javarosa: string): GeoJSONGeometry {
	if (!javarosa || !javarosa.trim()) {
		throw new Error('Invalid javarosa geometry input');
	}

	const coordinateSets = javarosa
		.trim()
		.split(';')
		.filter(Boolean)
		.map((point) => {
			const [lat, lon] = point.split(' ').slice(0, 2).map(parseFloat);
			return [lon, lat]; // GeoJSON expects [lon, lat]
		});

	if (coordinateSets.length === 1) {
		return {
			type: 'Point',
			coordinates: coordinateSets[0],
		};
	}

	if (
		coordinateSets.length > 2 &&
		coordinateSets[0][0] === coordinateSets[coordinateSets.length - 1][0] &&
		coordinateSets[0][1] === coordinateSets[coordinateSets.length - 1][1]
	) {
		return {
			type: 'Polygon',
			coordinates: [coordinateSets],
		};
	}

	return {
		type: 'LineString',
		coordinates: coordinateSets,
	};
}
