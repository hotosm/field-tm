import React from 'react';
import useOLMap from '@/hooks/useOlMap';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';

type submissionInstanceMapPropType = {
  featureGeojson: Record<string, any>;
};

const SubmissionInstanceMap = ({ featureGeojson }: submissionInstanceMapPropType) => {
  const { mapRef, map }: { mapRef: any; map: any } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });

  map?.on('loadstart', function () {
    map.getTargetElement().classList.add('spinner');
  });
  map?.on('loadend', function () {
    map.getTargetElement().classList.remove('spinner');
  });

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
        <LayerSwitcherControl visible={'osm'} />
        {featureGeojson?.type && (
          <VectorLayer
            geojson={featureGeojson}
            zIndex={10}
            zoomToLayer
            style={{ ...defaultStyles, lineColor: '#D73F37', lineThickness: 2 }}
          />
        )}
      </MapComponent>
    </div>
  );
};

export default SubmissionInstanceMap;
