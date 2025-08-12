import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { ClusterLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import useOLMap from '@/hooks/useOlMap';
import LayerSwitchMenu from '../MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';
import { geojsonObjectModel, geojsonObjectModelType } from '@/constants/geojsonObjectModal';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import { Fill, Icon, Style, Text } from 'ol/style';
import MarkerIcon from '@/assets/images/map-pin-primary.png';
import type { projectSummaryType } from '@/types';

const getIndividualClusterPointStyle = (featureProperty) => {
  const style = new Style({
    image: new Icon({
      anchor: [0.5, 1],
      scale: 1.1,
      anchorXUnits: 'fraction',
      anchorYUnits: 'pixels',
      src: MarkerIcon,
    }),
    text: new Text({
      text: `#${featureProperty?.project_id}`,
      fill: new Fill({
        color: 'black',
      }),
      offsetY: 42,
      font: '20px',
    }),
  });
  return style;
};

const ProjectSummaryMap = ({ projectList }: { projectList: projectSummaryType[] }) => {
  const navigate = useNavigate();

  const projectListFeatureCollection: geojsonObjectModelType = {
    ...geojsonObjectModel,
    features: projectList.map((project) => ({
      type: 'Feature',
      properties: {
        project_id: project.id?.toString(),
      },
      geometry: project.centroid || [],
    })),
  };

  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 20,
  });

  const projectClickOnMap = (properties: any) => {
    const projectId = properties.project_id;
    navigate(`/project/${projectId}`);
  };

  return (
    <div className="fmtm-w-full fmtm-h-full fmtm-rounded-lg fmtm-overflow-hidden">
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
        {projectListFeatureCollection && projectListFeatureCollection?.features?.length > 0 && (
          <ClusterLayer
            map={map}
            source={projectListFeatureCollection}
            zIndex={100}
            visibleOnMap={true}
            style={{
              ...defaultStyles,
              background_color: '#D73F37',
              color: '#eb9f9f',
              opacity: 90,
            }}
            mapOnClick={projectClickOnMap}
            getIndividualStyle={getIndividualClusterPointStyle}
          />
        )}
      </MapComponent>
    </div>
  );
};

export default ProjectSummaryMap;
