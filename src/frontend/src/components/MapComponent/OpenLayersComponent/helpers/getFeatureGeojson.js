import GeoJSON from 'ol/format/GeoJSON';

export default function getFeatureGeojson(
  feature,
  options = {
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857',
  },
) {
  const format = new GeoJSON();
  const geoJsonStr = format.writeFeature(feature, options);
  return JSON.parse(geoJsonStr);
}
