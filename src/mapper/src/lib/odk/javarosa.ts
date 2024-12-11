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
	return javarosaGeometry;
}
