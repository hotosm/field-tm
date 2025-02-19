import React from 'react';
import { MapContainer as MapComponent, useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index';
import MapLegend from '@/components/DataConflation/ConflationMap/MapLegend';
import Button from '@/components/common/Button';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { DataConflationActions } from '@/store/slices/DataConflationSlice';
import LayerSwitchMenu from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';

const ConflationMap = () => {
  const dispatch = useAppDispatch();

  const submissionConflationGeojson = useAppSelector((state) => state.dataconflation.submissionConflationGeojson);
  const submissionConflationGeojsonLoading = useAppSelector(
    (state) => state.dataconflation.submissionConflationGeojsonLoading,
  );

  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
  });

  return (
    <>
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map naxatw-relative naxatw-min-h-full !fmtm-h-full fmtm-w-[200px] fmtm-rounded-lg fmtm-overflow-hidden"
      >
        <VectorLayer
          geojson={submissionConflationGeojson}
          viewProperties={{
            size: map?.getSize(),
            padding: [50, 50, 50, 50],
            constrainResolution: true,
            duration: 2000,
          }}
          zoomToLayer
          mapOnClick={(properties, feature) => {
            dispatch(
              DataConflationActions.SetSelectedFeatureOSMId(
                feature?.getProperties()?.xid
                  ? feature.getProperties().xid
                  : feature.getProperties()?.osm_id.toString(),
              ),
            );
          }}
        />
        <div className="fmtm-absolute fmtm-right-2 fmtm-top-16 fmtm-z-20">
          <LayerSwitchMenu map={map} />
        </div>
        <LayerSwitcherControl visible="osm" />
        <div className="fmtm-absolute fmtm-bottom-20 sm:fmtm-bottom-3 fmtm-left-3 fmtm-z-50 fmtm-rounded-lg">
          <MapLegend />
        </div>
        <div className="fmtm-absolute fmtm-bottom-20 sm:fmtm-top-3 fmtm-right-3 fmtm-z-50 fmtm-rounded-lg fmtm-h-fit">
          <Button variant="primary-red" onClick={() => {}} isLoading={submissionConflationGeojsonLoading}>
            Upload to OSM
          </Button>
        </div>
      </MapComponent>
    </>
  );
};

export default ConflationMap;
