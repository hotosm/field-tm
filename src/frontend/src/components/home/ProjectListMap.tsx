import React, { useState, useEffect } from 'react';
import { useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { ClusterLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import CoreModules from '@/shared/CoreModules';
import { geojsonObjectModel } from '@/constants/geojsonObjectModal';
import { defaultStyles, getStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MarkerIcon from '@/assets/images/red_marker.png';
import { useNavigate } from 'react-router-dom';
import environment from '@/environment';
import { Style, Text, Icon, Fill } from 'ol/style';

type HomeProjectSummaryType = {
  features: { geometry: any; properties: any; type: any }[];
  type: string;
  SRID: {
    type: string;
    properties: {
      name: string;
    };
  };
};

// const projectGeojsonLayerStyle = {
//   ...defaultStyles,
//   fillOpacity: 0,
//   lineColor: '#ffffff',
//   labelFontSize: 20,
//   lineThickness: 7,
//   lineOpacity: 40,
//   showLabel: true,
//   labelField: 'project_id',
//   labelOffsetY: 35,
//   labelFontWeight: 'bold',
//   labelMaxResolution: 10000,
//   icon: { scale: [0.09, 0.09], url: MarkerIcon },
// };

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

  const [projectGeojson, setProjectGeojson] = useState<HomeProjectSummaryType | null>(null);
  const { mapRef, map } = useOLMap({
    // center: fromLonLat([85.3, 27.7]),
    center: [0, 0],
    zoom: 4,
    maxZoom: 17,
  });
  const homeProjectSummary = CoreModules.useAppSelector((state) => state.home.homeProjectSummary);
  useEffect(() => {
    if (!homeProjectSummary && homeProjectSummary?.length === 0) return;
    const convertedHomeProjectSummaryGeojson: HomeProjectSummaryType = {
      ...geojsonObjectModel,
      features: homeProjectSummary.map((project) => ({
        type: 'Feature',
        properties: {
          ...project,
          project_id: `#${project.id}`,
        },
        geometry: {
          type: 'Point',
          coordinates: project.centroid[0],
        },
      })),
    };

    setProjectGeojson(convertedHomeProjectSummaryGeojson);
  }, [homeProjectSummary]);

  const projectClickOnMap = (properties: any) => {
    const encodedProjectId = environment.encode(properties.id);
    navigate(`/project_details/${encodedProjectId}`);
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
          <LayerSwitcherControl visible={'outdoors'} />
          {/* {projectGeojson && projectGeojson?.features?.length > 0 && (
            <VectorLayer
              geojson={projectGeojson}
              style={projectGeojsonLayerStyle}
              viewProperties={{
                size: map?.getSize(),
                padding: [50, 50, 50, 50],
                constrainResolution: true,
                duration: 2000,
              }}
              mapOnClick={projectClickOnMap}
              zoomToLayer
              zIndex={5}
              // hoverEffect={(selectedFeature, layer) => {
              //   if (!selectedFeature)
              //     return layer.setStyle((feature, resolution) =>
              //       getStyles({
              //         style: { ...projectGeojsonLayerStyle },
              //         feature,
              //         resolution,
              //       }),
              //     );
              //   else {
              //     selectedFeature.setStyle((feature, resolution) =>
              //       getStyles({
              //         style: { ...projectGeojsonLayerStyle, icon: { scale: [0.15, 0.15], url: MarkerIcon } },
              //         feature,
              //         resolution,
              //       }),
              //     );
              //   }
              //   // selectedFeature.setStyle({
              //   //   ...projectGeojsonLayerStyle,
              //   //   icon: { scale: [0.15, 0.15], url: MarkerIcon },
              //   // });
              //   // selectedFeature.setStyle();
              // }}
            />
          )} */}
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
