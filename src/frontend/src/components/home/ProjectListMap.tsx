import React, { useState, useEffect } from 'react';
import { useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { ClusterLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import CoreModules from '@/shared/CoreModules';
import { geojsonObjectModel, geojsonObjectModelType } from '@/constants/geojsonObjectModal';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MarkerIcon from '@/assets/images/red_marker.png';
import { useNavigate } from 'react-router-dom';
import { Style, Text, Icon, Fill } from 'ol/style';
import { projectType } from '@/models/home/homeModel';
import LayerSwitchMenu from '../MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';

const getIndividualStyle = (featureProperty) => {
  const style = new Style({
    image: new Icon({
      src: MarkerIcon,
      scale: 0.08,
    }),
    text: new Text({
      text: featureProperty?.project_id,
      fill: new Fill({
        color: 'black',
      }),
      offsetY: 35,
      font: '20px Times New Roman',
    }),
  });
  return style;
};

const ProjectListMap = () => {
  const navigate = useNavigate();

  const [projectGeojson, setProjectGeojson] = useState<geojsonObjectModelType | null>(null);
  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 4,
    maxZoom: 20,
  });

  const homeProjectSummary: projectType[] = CoreModules.useAppSelector((state) => state.home.homeProjectSummary);
  useEffect(() => {
    if (homeProjectSummary?.length === 0) return;
    const convertedHomeProjectSummaryGeojson: geojsonObjectModelType = {
      ...geojsonObjectModel,
      features: homeProjectSummary.map((project) => ({
        type: 'Feature',
        properties: {
          ...project,
          project_id: `#${project.id}`,
        },
        geometry: {
          type: 'Point',
          coordinates: project.centroid || [],
        },
      })),
    };

    setProjectGeojson(convertedHomeProjectSummaryGeojson);
  }, [homeProjectSummary]);

  const projectClickOnMap = (properties: any) => {
    const projectId = properties.id;
    navigate(`/project/${projectId}`);
  };

  return (
    <div className="lg:fmtm-order-last lg:fmtm-w-[50%] fmtm-h-[33rem] lg:fmtm-h-full fmtm-bg-gray-300 fmtm-mx-4 fmtm-mb-2">
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
          <div className="fmtm-absolute fmtm-right-2 fmtm-top-2 fmtm-z-20">
            <LayerSwitchMenu map={map} />
          </div>
          <LayerSwitcherControl visible={'osm'} />
          {projectGeojson && projectGeojson?.features?.length > 0 && (
            <ClusterLayer
              map={map}
              source={projectGeojson}
              zIndex={100}
              visibleOnMap={true}
              style={{
                ...defaultStyles,
                background_color: '#D73F37',
                color: '#eb9f9f',
                opacity: 90,
              }}
              mapOnClick={projectClickOnMap}
              getIndividualStyle={getIndividualStyle}
            />
          )}
        </MapComponent>
      </div>
    </div>
  );
};

export default ProjectListMap;
