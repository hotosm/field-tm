import { Fill, Icon, Stroke, Style } from 'ol/style';
import { asArray, asString } from 'ol/color';
import { getCenter } from 'ol/extent';
import { Point } from 'ol/geom';
import AssetModules from '@/shared/AssetModules';
import { GeoGeomTypesEnum } from '@/types/enums';

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

function createFeaturePolygonStyle(color: string, strokeOpacity: number = 1) {
  return new Style({
    stroke: new Stroke({
      color: 'rgb(0,0,0,0.5)',
      width: 1,
      opacity: strokeOpacity,
    }),
    fill: new Fill({
      color: color,
    }),
  });
}

function createIconStyle(iconSrc: string, scale: number = 0.8, color: any = 'red') {
  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      scale: scale,
      anchorXUnits: 'fraction',
      anchorYUnits: 'pixels',
      src: iconSrc,
      color: color,
      opacity: 1,
    }),
    geometry: function (feature) {
      const polygonCentroid = getCenter(feature.getGeometry().getExtent());
      return new Point(polygonCentroid);
    },
  });
}

function updateRbgAlpha(colorString: string, alphaVal: number) {
  const val = asArray(colorString);
  return `rgb(${val.slice(0, 3).join(',')},${alphaVal})`;
}

const strokeColor = 'rgb(0,0,0,0.3)';
const secondaryStrokeColor = 'rgb(0,0,0,1)';

const getTaskStatusStyle = (feature: Record<string, any>, mapTheme: Record<string, any>, taskLockedByUser: boolean) => {
  const status = feature.getProperties().task_state;

  const isTaskStatusLocked = ['LOCKED_FOR_MAPPING', 'LOCKED_FOR_VALIDATION'].includes(status);
  const borderStrokeColor = isTaskStatusLocked && taskLockedByUser ? secondaryStrokeColor : strokeColor;

  const lockedPolygonStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_mapping,
    borderStrokeColor,
  );
  const lockedValidationStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.locked_for_validation,
    borderStrokeColor,
  );
  const iconStyle = createIconStyle(AssetModules.LockPng);
  const redIconStyle = createIconStyle(AssetModules.RedLockPng);

  const geojsonStyles = {
    UNLOCKED_TO_MAP: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.ready,
      }),
    }),
    LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
    UNLOCKED_TO_VALIDATE: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.mapped,
      }),
    }),
    LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],
    UNLOCKED_DONE: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.validated,
      }),
    }),
  };
  return geojsonStyles[status];
};

export const getFeatureStatusStyle = (geomType: string, mapTheme: Record<string, any>, mappingStatus: string) => {
  let geojsonStyles;

  if (geomType === GeoGeomTypesEnum.POINT) {
    geojsonStyles = {
      READY: createIconStyle(
        AssetModules.MapPinGrey,
        1.1,
        updateRbgAlpha(mapTheme.palette.entityStatusColors.ready, 1),
      ),
      OPENED_IN_ODK: createIconStyle(
        AssetModules.MapPinGrey,
        1.1,
        updateRbgAlpha(mapTheme.palette.entityStatusColors.opened_in_odk, 1),
      ),
      SURVEY_SUBMITTED: createIconStyle(
        AssetModules.MapPinGrey,
        1.1,
        updateRbgAlpha(mapTheme.palette.entityStatusColors.survey_submitted, 1),
      ),
      MARKED_BAD: createIconStyle(
        AssetModules.MapPinGrey,
        1.1,
        updateRbgAlpha(mapTheme.palette.entityStatusColors.marked_bad, 1),
      ),
      VALIDATED: createIconStyle(
        AssetModules.MapPinGrey,
        1.1,
        updateRbgAlpha(mapTheme.palette.entityStatusColors.validated, 1),
      ),
    };
  } else if (geomType === GeoGeomTypesEnum.POLYGON) {
    geojsonStyles = {
      READY: createFeaturePolygonStyle(mapTheme.palette.entityStatusColors.ready, 0.2),
      OPENED_IN_ODK: createFeaturePolygonStyle(mapTheme.palette.entityStatusColors.opened_in_odk, 0.2),
      SURVEY_SUBMITTED: createFeaturePolygonStyle(mapTheme.palette.entityStatusColors.survey_submitted),
      MARKED_BAD: createFeaturePolygonStyle(mapTheme.palette.entityStatusColors.marked_bad),
      VALIDATED: createFeaturePolygonStyle(mapTheme.palette.entityStatusColors.validated),
    };
  } else if (geomType === GeoGeomTypesEnum.LINESTRING) {
    console.warn('linestring style not set');
  }

  return geojsonStyles[mappingStatus];
};

export default getTaskStatusStyle;
