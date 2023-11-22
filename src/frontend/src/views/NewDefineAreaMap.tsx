import React from 'react';
import useOLMap from '../hooks/useOlMap';
import { MapContainer as MapComponent } from '../components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '../components/MapComponent/OpenLayersComponent/Layers';
import { GeoJSONFeatureTypes } from '../store/types/ICreateProject';

type NewDefineAreaMapProps = {
  drawToggle?: boolean;
  splittedGeojson: GeoJSONFeatureTypes;
  uploadedOrDrawnGeojsonFile: GeoJSONFeatureTypes;
  buildingExtractedGeojson?: GeoJSONFeatureTypes;
  lineExtractedGeojson?: GeoJSONFeatureTypes;
  onDraw?: () => void;
};
const NewDefineAreaMap = ({
  drawToggle,
  uploadedOrDrawnGeojsonFile,
  splittedGeojson,
  buildingExtractedGeojson,
  lineExtractedGeojson,
  onDraw,
  onModify,
}: NewDefineAreaMapProps) => {
  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });
  const isDrawOrGeojsonFile = drawToggle || uploadedOrDrawnGeojsonFile;

  return (
    <div className="map-container" style={{ height: '600px', width: '100%' }}>
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
        {splittedGeojson && (
          <VectorLayer
            geojson={splittedGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 500,
            }}
            zoomToLayer
          />
        )}
        {isDrawOrGeojsonFile && !splittedGeojson && (
          <VectorLayer
            geojson={uploadedOrDrawnGeojsonFile}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 500,
            }}
            onDraw={onDraw}
            onModify={onModify}
            zoomToLayer
          />
        )}

        {buildingExtractedGeojson && (
          <VectorLayer
            geojson={buildingExtractedGeojson}
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
              duration: 500,
            }}
            zoomToLayer
          />
        )}
        {lineExtractedGeojson && (
          <VectorLayer
            geojson={lineExtractedGeojson}
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
              duration: 500,
            }}
            zoomToLayer
          />
        )}
      </MapComponent>
    </div>
  );
};

export default NewDefineAreaMap;
