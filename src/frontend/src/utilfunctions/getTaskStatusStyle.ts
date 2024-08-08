import { Fill, Icon, Stroke, Style } from 'ol/style';
import { getCenter } from 'ol/extent';
import { Point } from 'ol/geom';
import AssetModules from '@/shared/AssetModules';
import { task_status } from '@/types/enums';
import { EntityOsmMap } from '@/store/types/IProject';

function createPolygonStyle(fillColor: string, strokeColor: string) {
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

function createIconStyle(iconSrc: string) {
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

const strokeColor = 'rgb(0,0,0,0.3)';
const secondaryStrokeColor = 'rgb(0,0,0,1)';

const getTaskStatusStyle = (feature: Record<string, any>, mapTheme: Record<string, any>, taskLockedByUser: boolean) => {
  let id = feature.getId().toString().replace('_', ',');
  const status = id.split(',')[1];

  const isTaskStatusLocked = ['LOCKED_FOR_MAPPING', 'LOCKED_FOR_VALIDATION'].includes(status);
  const borderStrokeColor = isTaskStatusLocked && taskLockedByUser ? secondaryStrokeColor : strokeColor;

  const lockedPolygonStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_mapping_rgb,
    borderStrokeColor,
  );
  const lockedValidationStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_validation_rgb,
    borderStrokeColor,
  );
  const iconStyle = createIconStyle(AssetModules.LockPng);
  const redIconStyle = createIconStyle(AssetModules.RedLockPng);

  const geojsonStyles = {
    READY: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.ready_rgb,
      }),
    }),
    LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
    MAPPED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.mapped_rgb,
      }),
    }),
    LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],

    VALIDATED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.validated_rgb,
      }),
    }),
    INVALIDATED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.invalidated_rgb,
      }),
    }),
    BAD: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.bad_rgb,
      }),
    }),
    SPLIT: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.split_rgb,
      }),
    }),
  };
  return geojsonStyles[status];
};

export const getFeatureStatusStyle = (osmId: string, mapTheme: Record<string, any>, entityOsmMap: EntityOsmMap[]) => {
  const entity = entityOsmMap?.find((entity) => entity?.osm_id === osmId) as EntityOsmMap;
  let status = task_status[entity?.status];

  const borderStrokeColor = '#FF0000';

  const lockedPolygonStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_mapping_rgb,
    borderStrokeColor,
  );
  const lockedValidationStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_validation_rgb,
    borderStrokeColor,
  );
  const iconStyle = createIconStyle(AssetModules.LockPng);
  const redIconStyle = createIconStyle(AssetModules.RedLockPng);

  const geojsonStyles = {
    READY: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.ready_rgb,
      }),
    }),
    LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
    MAPPED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.mapped_rgb,
      }),
    }),
    LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],

    VALIDATED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.validated_rgb,
      }),
    }),
    INVALIDATED: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.invalidated_rgb,
      }),
    }),
    BAD: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.bad_rgb,
      }),
    }),
    SPLIT: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 1,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.split_rgb,
      }),
    }),
  };
  return geojsonStyles[status];
};

export default getTaskStatusStyle;
