/* eslint-disable no-promise-executor-return */
import * as olExtent from 'ol/extent';
import { Point } from 'ol/geom';
import VectorLayer from 'ol/layer/Vector';
import VectorTileLayer from 'ol/layer/VectorTile';
import { fromLonLat } from 'ol/proj';

export function zoomToLatLng(map, latLng, options = {}) {
  const [lat, lng] = latLng;
  map.getView().fit(new Point(fromLonLat([lng, lat])), {
    padding: [50, 50, 50, 50],
    duration: 900,
    constrainResolution: true,
    maxZoom: 18,
    ...options,
  });
}

export function getCurrentMapExtent(map) {
  return map.getView().calculateExtent(map.getSize());
}

export function getOverallLayerExtentx(map) {
  const extent = olExtent.createEmpty();
  const layers = map.getLayers();
  layers.forEach((layer) => {
    if (layer instanceof VectorLayer) {
      olExtent.extend(extent, layer.getSource().getExtent());
    }
  });
  return extent;
}

export function isExtentValid(extent) {
  return !extent.some((value) => value === Infinity || Number.isNaN(value));
}

export async function getOverallLayerExtent(map) {
  const extent = olExtent.createEmpty();
  const layerArr = map.getLayers().getArray();
  for (let i = 0; i < layerArr.length; i += 1) {
    const layer = layerArr[i];
    if (layer instanceof VectorTileLayer) {
      // eslint-disable-next-line
      await new Promise((resolve) =>
        layerArr[i].getSource().on('tileloadend', async (evt) => {
          const feature = await evt.tile.getFeatures();
          feature.forEach((feat) => {
            const featureExtent = feat.getExtent();
            olExtent.extend(extent, featureExtent);
          });
          resolve();
          // setTimeout(() => resolve(), 1000);
        }),
      );
    } else if (layer instanceof VectorLayer) {
      const featExtent = layer.getSource().getExtent();
      olExtent.extend(extent, featExtent);
    }
  }
  return extent;
}
