import React from "react";
import CoreModules from "fmtm/CoreModules";
import { MapContainer as MapComponent } from "../MapComponent/OpenLayersComponent";
import { useOLMap } from "../MapComponent/OpenLayersComponent";
import LayerSwitcherControl from "../MapComponent/OpenLayersComponent/LayerSwitcher";
import { VectorLayer } from "../MapComponent/OpenLayersComponent/Layers";

const ProjectInfomap = () => {
  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });
  return (
    <CoreModules.Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        gap: 2,
        height: "80%",
      }}
    >
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
        {/* <VectorLayer /> */}
      </MapComponent>
    </CoreModules.Box>
  );
};

export default ProjectInfomap;
