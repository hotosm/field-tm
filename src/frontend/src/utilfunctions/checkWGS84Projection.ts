import OLVectorLayer from 'ol/layer/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { Vector as VectorSource } from 'ol/source';
import { DrawnGeojsonTypes } from '@/store/types/ICreateProject';

function checkWGS84Projection(drawnGeojson: DrawnGeojsonTypes | null) {
  const vectorLyr = new OLVectorLayer({
    source: new VectorSource({
      features: new GeoJSON().readFeatures(drawnGeojson),
    }),
    declutter: true,
  });

  const extent = vectorLyr.getSource()?.getExtent();

  try {
    if (extent && extent?.length > 0) {
      const longitude = extent[0];
      const latitude = extent[1];
      if (
        isNaN(latitude) ||
        isNaN(longitude) ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180
      ) {
        return false;
      }
      return true; // All coordinates are within WGS 84 range
    }
    return false;
  } catch (error) {
    return false;
  }
}

export { checkWGS84Projection };
