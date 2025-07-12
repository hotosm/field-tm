import React, { useState } from 'react';
import useOLMap from '@/hooks/useOlMap';

import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { DrawnGeojsonTypes, GeoJSONFeatureTypes } from '@/store/types/ICreateProject';
import MapControls from './MapControls';

type propsType = {
  drawToggle?: boolean;
  splittedGeojson?: GeoJSONFeatureTypes | null;
  uploadedOrDrawnGeojsonFile: DrawnGeojsonTypes | null;
  buildingExtractedGeojson?: GeoJSONFeatureTypes | null;
  lineExtractedGeojson?: GeoJSONFeatureTypes;
  onDraw?: ((geojson: any, area: string) => void) | null;
  onModify?: ((geojson: any, area: string) => void) | null;
  hasEditUndo?: boolean;
  getAOIArea?: ((area?: string) => void) | null;
  toggleEdit?: boolean;
  setToggleEdit?: (value: boolean) => void;
};

const Map = ({
  drawToggle,
  uploadedOrDrawnGeojsonFile,
  splittedGeojson,
  buildingExtractedGeojson,
  lineExtractedGeojson,
  onDraw,
  onModify,
  hasEditUndo,
  getAOIArea,
  toggleEdit,
  setToggleEdit,
}: propsType) => {
  const { mapRef, map }: { mapRef: any; map: any } = useOLMap({
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });
  const isDrawOrGeojsonFile = drawToggle || uploadedOrDrawnGeojsonFile;

  return (
    <div className="map-container fmtm-w-full fmtm-h-full">
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
        <MapControls hasEditUndo={hasEditUndo} toggleEdit={toggleEdit} setToggleEdit={setToggleEdit} />

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
            getAOIArea={getAOIArea}
            style={{ ...defaultStyles, lineColor: '#0fffff', lineThickness: 2, fillOpacity: 10, fillColor: '#000000' }}
          />
        )}

        {splittedGeojson && (
          <VectorLayer
            geojson={splittedGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 500,
            }}
            onModify={onModify}
            style={{ ...defaultStyles, lineColor: '#0fffff', lineThickness: 2, fillOpacity: 10, fillColor: '#000000' }}
          />
        )}

        {buildingExtractedGeojson && (
          <VectorLayer
            geojson={buildingExtractedGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 500,
            }}
            zoomToLayer
            style={{ ...defaultStyles, lineColor: '#1a2fa2', fillOpacity: 30, lineOpacity: 50 }}
          />
        )}

        {lineExtractedGeojson && (
          <VectorLayer
            geojson={lineExtractedGeojson}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
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

export default Map;
