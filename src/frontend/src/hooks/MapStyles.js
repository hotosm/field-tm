import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import { Icon, Style } from 'ol/style';
import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { getCenter } from 'ol/extent';
import Point from 'ol/geom/Point.js';

function createPolygonStyle(fillColor, strokeColor) {
  return new Style({
    stroke: new Stroke({
      color: strokeColor,
      width: 3,
    }),
    fill: new Fill({
      color: fillColor,
    }),
    zIndex: 10,
  });
}
function createIconStyle(iconSrc) {
  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      scale: 0.8,
      anchorXUnits: 'fraction',
      anchorYUnits: 'pixels',
      src: iconSrc,
    }),
    geometry: function (feature) {
      const polygonCentroid = getCenter(feature.getGeometry().getExtent());
      return new Point(polygonCentroid);
    },
  });
}
export default function MapStyles() {
  const mapTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const [style, setStyle] = useState({});
  const strokeColor = 'rgb(0,0,0,0.3)';
  const secondaryStrokeColor = 'rgb(0,0,0,1)';

  useEffect(() => {
    // Example usage:
    const lockedPolygonStyle = createPolygonStyle(
      mapTheme.palette.mapFeatureColors.LOCKED_FOR_MAPPING,
      secondaryStrokeColor,
    );
    const lockedValidationStyle = createPolygonStyle(
      mapTheme.palette.mapFeatureColors.LOCKED_FOR_VALIDATION,
      secondaryStrokeColor,
    );
    const iconStyle = createIconStyle(AssetModules.LockPng);
    const redIconStyle = createIconStyle(AssetModules.RedLockPng);

    const geojsonStyles = {
      UNLOCKED_TO_MAP: new Style({
        stroke: new Stroke({
          color: strokeColor,
          width: 3,
        }),
        fill: new Fill({
          color: mapTheme.palette.mapFeatureColors.UNLOCKED_TO_MAP,
        }),
      }),
      LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
      UNLOCKED_TO_VALIDATE: new Style({
        stroke: new Stroke({
          color: strokeColor,
          width: 3,
        }),
        fill: new Fill({
          color: mapTheme.palette.mapFeatureColors.UNLOCKED_TO_VALIDATE,
        }),
      }),
      LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],
      UNLOCKED_DONE: new Style({
        stroke: new Stroke({
          color: strokeColor,
          width: 3,
        }),
        fill: new Fill({
          color: mapTheme.palette.mapFeatureColors.UNLOCKED_DONE,
        }),
      }),
    };
    setStyle(geojsonStyles);
  }, []);

  return style;
}
