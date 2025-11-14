import React from 'react';
import useOLMap from '@/hooks/useOlMap';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import LayerSwitchMenu from '../MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';
import { ClusterLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { Style, Circle } from 'ol/style';
import { Stroke } from 'ol/style';
import { hexToRgba } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { Fill } from 'ol/style';
import { geojsonType } from '@/store/types/ISubmissions';
import MapControlComponent from '@/components/SubmissionMap/MapControlComponent';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import MapLegend from './MapLegend';

type submissionInstanceMapPropType = {
  featureGeojson: { vectorLayerGeojson: geojsonType; clusterLayerGeojson: geojsonType };
  status: null | 'approved' | 'hasIssues';
};

const getFeatureColor = (status) => {
  switch (status) {
    case 'approved':
      return '#2d876c';
    case 'hasIssues':
      return '#D73F37';
    default:
      return '#5e5e5e';
  }
};

const getIndividualStyle = (featureProperty) => {
  const style = new Style({
    image: new Circle({
      radius: 10,
      stroke: new Stroke({
        color: hexToRgba('#D73F37'),
        width: 2,
      }),
      fill: new Fill({
        color: hexToRgba('#eb9f9f'),
        width: 40,
      }),
    }),
  });
  return style;
};

const SubmissionInstanceMap = ({ featureGeojson, status }: submissionInstanceMapPropType) => {
  const { mapRef, map }: { mapRef: any; map: any } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 20,
  });

  map?.on('loadstart', function () {
    map.getTargetElement().classList.add('spinner');
  });
  map?.on('loadend', function () {
    map.getTargetElement().classList.remove('spinner');
  });

  const taskSubmissionsPopupUI = (properties: Record<string, any>) => {
    return <div className="fmtm-h-fit">{properties?.label}</div>;
  };

  return (
    <div className="map-container" style={{ height: '100%' }}>
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map naxatw-relative naxatw-min-h-full naxatw-w-full"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <div className="fmtm-absolute fmtm-right-2 fmtm-top-2 fmtm-z-20">
          <LayerSwitchMenu map={map} />
        </div>
        <MapControlComponent map={map} />
        <LayerSwitcherControl visible={'osm'} />
        {featureGeojson?.vectorLayerGeojson?.type && (
          <VectorLayer
            geojson={featureGeojson?.vectorLayerGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
              maxZoom: 20,
            }}
            zIndex={10}
            zoomToLayer
            style={{
              ...defaultStyles,
              lineThickness: 2,
              circleRadius: 10,
              lineColor: getFeatureColor(status),
              fillColor: getFeatureColor(status),
            }}
          />
        )}
        {featureGeojson?.clusterLayerGeojson?.type && (
          <ClusterLayer
            map={map}
            source={featureGeojson?.clusterLayerGeojson}
            zIndex={100}
            visibleOnMap={true}
            zoomToLayer={false}
            style={{
              ...defaultStyles,
              background_color: '#D73F37',
              color: '#eb9f9f',
              opacity: 90,
            }}
            mapOnClick={() => {}}
            getIndividualStyle={getIndividualStyle}
          />
        )}
        <AsyncPopup map={map} popupUI={taskSubmissionsPopupUI} primaryKey="label" />
        <MapLegend />
      </MapComponent>
    </div>
  );
};

export default SubmissionInstanceMap;
