import React, { useState } from 'react';
import CoreModules from 'fmtm/CoreModules';
import { useOLMap } from '../MapComponent/OpenLayersComponent';
import { MapContainer as MapComponent } from '../MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '../MapComponent/OpenLayersComponent/Layers';

const basicGeojsonTemplate = {
  type: 'FeatureCollection',
  features: [],
};
const ProjectMap = ({}) => {
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });
  const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);

  const [projectBoundaries, setProjectBoundaries] = useState(null);
  const [buildingBoundaries, setBuildingBoundaries] = useState(null);

  if (projectTaskBoundries?.length > 0 && projectBoundaries === null) {
    const taskGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectTaskBoundries?.[0]?.taskBoundries?.map((task) => ({
          ...task.outline_geojson,
          id: task.outline_geojson.properties.uid,
        })),
      ],
    };
    setProjectBoundaries(taskGeojsonFeatureCollection);
  }
  if (projectBuildingGeojson?.length > 0 && buildingBoundaries === null) {
    const buildingGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectBuildingGeojson?.map((building) => ({
          ...building.geometry.geometry,
          id: building.id,
        })),
      ],
      // features: projectBuildingGeojson.map((feature) => ({ ...feature.geometry, id: feature.id }))
    };
    setBuildingBoundaries(buildingGeojsonFeatureCollection);
  }
  return (
    <CoreModules.Stack spacing={1} p={2.5} direction={'column'}>
      <CoreModules.Stack
        style={{ border: `4px solid ${defaultTheme.palette.error.main}` }}
        justifyContent={'center'}
        height={608}
      >
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
            <LayerSwitcherControl />
            {projectBoundaries?.type && (
              <VectorLayer
                geojson={projectBoundaries}
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
                zoomToLayer
                zIndex={5}
              />
            )}
            {buildingBoundaries?.type && <VectorLayer geojson={buildingBoundaries} zIndex={10} />}
            {/* )} */}
          </MapComponent>
        </div>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default ProjectMap;
