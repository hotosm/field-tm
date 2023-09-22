import React from 'react';
import useOLMap from '../hooks/useOlMap';
import { MapContainer as MapComponent } from '../components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '../components/MapComponent/OpenLayersComponent/Layers';

const EditProjectArea = ({ geojson }) => {
  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });

  return (
    <div className="map-container" style={{ height: '600px', marginLeft: '20px' }}>
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map naxatw-relative naxatw-min-h-full naxatw-w-full"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <LayerSwitcherControl />
        {geojson && (
          <VectorLayer
            geojson={geojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            zoomToLayer
          />
        )}
        {/*
        {dataExtractedGeojson && (
          <VectorLayer
            geojson={dataExtractedGeojson}
            // stylestyle={{
            //     ...getStyles,
            //     fillOpacity: 100,
            //     lineColor: getStyles.fillColor,
            //     lineThickness: 7,
            //     lineOpacity: 40,
            // }}
            viewProperties={{
              // easing: elastic,
              // animate: true,
              size: map?.getSize(),
              // maxZoom: 15,
              padding: [50, 50, 50, 50],
              // duration: 900,
              constrainResolution: true,
              duration: 2000,
            }}
            // zoomToLayer
          />
        )} */}
      </MapComponent>
    </div>
  );
};

export default EditProjectArea;
