import React from "react";
import useOLMap from "../../hooks/useOlMap";
import { MapContainer as MapComponent } from "../MapComponent/OpenLayersComponent";
import LayerSwitcherControl from "../MapComponent/OpenLayersComponent/LayerSwitcher/index.js";
import { VectorLayer } from "../MapComponent/OpenLayersComponent/Layers";

function elastic(t) {
  return (
    Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1
  );
}
const basicGeojsonTemplate = {
  type: "FeatureCollection",
  features: [],
};
const TasksMap = ({ projectTaskBoundries, projectBuildingGeojson }) => {
  // const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  // const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);

  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });
  console.log(projectTaskBoundries, "projectTaskBoundries");

  return (
    <div className="map-container" style={{ height: "100%" }}>
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map naxatw-relative naxatw-min-h-full naxatw-w-full"
        style={{
          height: "100%",
          width: "100%",
        }}
      >
        <LayerSwitcherControl />
        {/* <VectorLayer
          geojson={taskGeojsonFeatureCollection}
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
        />
        <VectorLayer geojson={buildingGeojsonFeatureCollection} /> */}
      </MapComponent>
    </div>
  );
};

TasksMap.propTypes = {};

export default TasksMap;
