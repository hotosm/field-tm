import { Fill, Icon, Stroke, Style } from 'ol/style';
import { transform } from 'ol/proj';
import { Point } from 'ol/geom';
import AssetModules from '@/shared/AssetModules';
import { task_priority_str } from '@/types/enums';

function createPolygonStyle(fillColor, strokeColor) {
  return new Style({
    stroke: new Stroke({
      color: strokeColor,
      width: 3,
    }),
    fill: new Fill({
      color: fillColor,
    }),
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
      const convertedCenter = transform(feature.values_.centroid, 'EPSG:4326', 'EPSG:3857');
      return new Point(convertedCenter);
    },
  });
}

const strokeColor = 'rgb(0,0,0,0.5)';

const getTaskStatusStyle = (feature, mapTheme) => {
  let id = feature.getId().toString().replace('_', ',');
  const status = id.split(',')[1];
  const lockedPolygonStyle = createPolygonStyle(mapTheme.palette.mapFeatureColors.locked_for_mapping_rgb, strokeColor);
  const lockedValidationStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_validation_rgb,
    strokeColor,
  );
  const iconStyle = createIconStyle(AssetModules.LockPng);
  const redIconStyle = createIconStyle(AssetModules.RedLockPng);

  const geojsonStyles = {
    READY: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.ready_rgb,
      }),
    }),
    LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
    MAPPED: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.mapped_rgb,
      }),
    }),
    LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],

    VALIDATED: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.validated_rgb,
      }),
    }),
    INVALIDATED: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.invalidated_rgb,
      }),
    }),
    BAD: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.bad_rgb,
      }),
    }),
    SPLIT: new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.split_rgb,
      }),
    }),
  };
  return geojsonStyles[status];
};

export default getTaskStatusStyle;
