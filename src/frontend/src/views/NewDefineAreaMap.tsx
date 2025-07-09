import React from 'react';
import useOLMap from '@/hooks/useOlMap';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { DrawnGeojsonTypes, GeoJSONFeatureTypes } from '@/store/types/ICreateProject';
import MapControlComponent from '@/components/createnewproject/MapControlComponent';
import LayerSwitchMenu from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';

type NewDefineAreaMapProps = {
  drawToggle?: boolean;
  splittedGeojson?: GeoJSONFeatureTypes | null;
  uploadedOrDrawnGeojsonFile: DrawnGeojsonTypes | null;
  buildingExtractedGeojson?: GeoJSONFeatureTypes | null;
  lineExtractedGeojson?: GeoJSONFeatureTypes;
  onDraw?: ((geojson: any, area: string) => void) | null;
  onModify?: ((geojson: any, area: string) => void) | null;
  hasEditUndo?: boolean;
  getAOIArea?: ((area?: string) => void) | null;
};

const NewDefineAreaMap = ({
  drawToggle,
  uploadedOrDrawnGeojsonFile,
  splittedGeojson,
  buildingExtractedGeojson,
  lineExtractedGeojson,
  onDraw,
  onModify,
  hasEditUndo,
  getAOIArea,
}: NewDefineAreaMapProps) => {
  const { mapRef, map }: { mapRef: any; map: any } = useOLMap({
    center: [0, 0],
    zoom: 1,
    maxZoom: 25,
  });
  const isDrawOrGeojsonFile = drawToggle || uploadedOrDrawnGeojsonFile;

  return (
    <div className="map-container fmtm-w-full fmtm-h-[600px] lg:fmtm-h-full">
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map naxatw-relative naxatw-min-h-full naxatw-w-full"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <div className="fmtm-absolute fmtm-right-2 fmtm-top-5 fmtm-z-20">
          <LayerSwitchMenu map={map} />
        </div>
        <LayerSwitcherControl visible={'osm'} />
        <MapControlComponent map={map} hasEditUndo={hasEditUndo} />
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

export default NewDefineAreaMap;
