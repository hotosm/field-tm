import { Fill, Icon, Stroke, Style, Circle } from 'ol/style';
import { asArray } from 'ol/color';
import { Point } from 'ol/geom';
import AssetModules from '@/shared/AssetModules';
import { GeoGeomTypesEnum } from '@/types/enums';
import { centroid } from '@turf/centroid';
import getFeatureGeojson from '@/components/MapComponent/OpenLayersComponent/helpers/getFeatureGeojson';

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

function createPointStyle(fillColor: string, strokeColor: string) {
  return new Style({
    image: new Circle({
      fill: new Fill({
        color: fillColor,
      }),
      stroke: new Stroke({
        color: strokeColor,
        width: 1,
      }),
      radius: 8,
      declutterMode: 'obstacle',
    }),
    zIndex: 5,
  });
}

function createFeaturePolygonStyle(color: string, strokeOpacity: number = 1, strokeColor: string) {
  return new Style({
    stroke: new Stroke({
      color: strokeColor,
      width: 1,
      opacity: strokeOpacity,
    }),
    fill: new Fill({
      color: color,
    }),
  });
}

function createFeatureLineStyle(strokeColor: string) {
  return new Style({
    stroke: new Stroke({
      color: strokeColor,
      width: 3,
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
      declutterMode: 'obstacle',
    }),
    geometry: function (feature) {
      const polygonCoord = getFeatureGeojson(feature, {});
      const polygonCentroid = centroid(polygonCoord)?.geometry?.coordinates;
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
  const borderStrokeColor = 'rgb(15, 255, 255, 0.4)';

  const lockedPolygonStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.LOCKED_FOR_MAPPING,
    borderStrokeColor,
  );
  const lockedValidationStyle = createPolygonStyle(
    mapTheme.palette.mapFeatureColors.LOCKED_FOR_VALIDATION,
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
        color: mapTheme.palette.mapFeatureColors.UNLOCKED_TO_MAP,
      }),
    }),
    LOCKED_FOR_MAPPING: [lockedPolygonStyle, iconStyle],
    UNLOCKED_TO_VALIDATE: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.UNLOCKED_TO_VALIDATE,
      }),
    }),
    LOCKED_FOR_VALIDATION: [lockedValidationStyle, redIconStyle],
    UNLOCKED_DONE: new Style({
      stroke: new Stroke({
        color: borderStrokeColor,
        width: 3,
      }),
      fill: new Fill({
        color: mapTheme.palette.mapFeatureColors.UNLOCKED_DONE,
      }),
    }),
  };
  return geojsonStyles[status];
};

export const getFeatureStatusStyle = (
  geomType: string,
  mapTheme: Record<string, any>,
  mappingStatus: string,
  isEntitySelected: boolean,
) => {
  let geojsonStyles;
  if (geomType === 'Point') {
    geojsonStyles = {
      READY: createPointStyle(
        mapTheme.palette.entityStatusColors.ready,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(255,255,255,1)',
      ),
      OPENED_IN_ODK: createPointStyle(
        mapTheme.palette.entityStatusColors.opened_in_odk,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(255,255,255,1)',
      ),
      SURVEY_SUBMITTED: createPointStyle(
        mapTheme.palette.entityStatusColors.survey_submitted,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(255,255,255,1)',
      ),
      MARKED_BAD: createPointStyle(
        mapTheme.palette.entityStatusColors.marked_bad,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(255,255,255,1)',
      ),
      VALIDATED: createPointStyle(
        mapTheme.palette.entityStatusColors.validated,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(255,255,255,1)',
      ),
    };
  } else if (geomType === 'Polygon') {
    geojsonStyles = {
      READY: createFeaturePolygonStyle(
        mapTheme.palette.entityStatusColors.ready,
        0.2,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(0,0,0,0.5)',
      ),
      OPENED_IN_ODK: createFeaturePolygonStyle(
        mapTheme.palette.entityStatusColors.opened_in_odk,
        0.2,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(0,0,0,0.5)',
      ),
      SURVEY_SUBMITTED: createFeaturePolygonStyle(
        mapTheme.palette.entityStatusColors.survey_submitted,
        1,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(0,0,0,0.5)',
      ),
      MARKED_BAD: createFeaturePolygonStyle(
        mapTheme.palette.entityStatusColors.marked_bad,
        1,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(0,0,0,0.5)',
      ),
      VALIDATED: createFeaturePolygonStyle(
        mapTheme.palette.entityStatusColors.validated,
        1,
        isEntitySelected ? 'rgb(224,10,7,1)' : 'rgb(0,0,0,0.5)',
      ),
    };
  } else if (geomType === 'LineString') {
    geojsonStyles = {
      READY: createFeatureLineStyle(mapTheme.palette.lineEntityStatusColors.ready),
      OPENED_IN_ODK: createFeatureLineStyle(mapTheme.palette.lineEntityStatusColors.opened_in_odk),
      SURVEY_SUBMITTED: createFeatureLineStyle(mapTheme.palette.lineEntityStatusColors.survey_submitted),
      MARKED_BAD: createFeatureLineStyle(mapTheme.palette.lineEntityStatusColors.marked_bad),
      VALIDATED: createFeatureLineStyle(mapTheme.palette.lineEntityStatusColors.validated),
    };
  }

  return geojsonStyles[mappingStatus];
};

export default getTaskStatusStyle;
