import React from 'react';
import useOLMap from '@/hooks/useOlMap';

import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { DrawnGeojsonTypes, GeoJSONFeatureTypes } from '@/store/types/ICreateProject';
import MapControls from './MapControls';

type propsType = {
  drawToggle?: boolean;
  aoiGeojson: DrawnGeojsonTypes | null;
  extractGeojson?: GeoJSONFeatureTypes | null;
  splitGeojson?: GeoJSONFeatureTypes | null;
  onDraw?: ((geojson: any, area: string) => void) | null;
  onModify?: ((geojson: any, area: string) => void) | null;
  getAOIArea?: ((area?: string) => void) | null;
  toggleEdit: boolean;
  setToggleEdit: (value: boolean) => void;
};

const Map = ({
  drawToggle,
  aoiGeojson,
  extractGeojson,
  splitGeojson,
  onDraw,
  onModify,
  getAOIArea,
  toggleEdit,
  setToggleEdit,
}: propsType) => {
  const { mapRef, map }: { mapRef: any; map: any } = useOLMap({
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });
  const isDrawOrGeojsonFile = drawToggle || aoiGeojson;

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
        <MapControls map={map} toggleEdit={toggleEdit} setToggleEdit={setToggleEdit} />

        {isDrawOrGeojsonFile && !splitGeojson && (
          <VectorLayer
            geojson={aoiGeojson}
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

        {splitGeojson && (
          <VectorLayer
            geojson={splitGeojson}
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

        {extractGeojson && (
          <VectorLayer
            geojson={extractGeojson}
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
      </MapComponent>
    </div>
  );
};

export default Map;
