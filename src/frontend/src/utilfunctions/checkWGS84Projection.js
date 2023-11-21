function checkWGS84Projection(geojson) {
  try {
    for (const feature of geojson.features) {
      const coordinates = feature.geometry.coordinates;
      for (const coord of coordinates[0]) {
        const [longitude, latitude] = coord;
        if (
          isNaN(latitude) ||
          isNaN(longitude) ||
          latitude < -90 ||
          latitude > 90 ||
          longitude < -180 ||
          longitude > 180
        ) {
          //   setIsGeojsonWG84(false);
          return false; // Coordinates are out of WGS 84 range
        }
      }
    }
    // setIsGeojsonWG84(true);
    return true; // All coordinates are within WGS 84 range
  } catch (error) {
    // setIsGeojsonWG84(false);
    return false;
  }
}

export { checkWGS84Projection };
