import React, { useState, useEffect } from 'react';
import { useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index.js';
import OLVectorLayer from 'ol/layer/Vector';
import { ClusterLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import CoreModules from '@/shared/CoreModules';
import { geojsonObjectModel } from '@/constants/geojsonObjectModal';
import { defaultStyles, getStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MarkerIcon from '@/assets/images/red_marker.png';
import { useNavigate } from 'react-router-dom';
import environment from '@/environment';
import { Style, Text, Icon, Fill } from 'ol/style';
import { projectType } from '@/models/home/homeModel';
import Control from 'ol/control/Control';
import { Feature } from 'ol';
import { circular } from 'ol/geom/Polygon';
import { Point } from 'ol/geom';
import { fromLonLat } from 'ol/proj';
import VectorSource from 'ol/source/Vector';
import logo from '@/assets/images/navigation.svg';
import RedNavigationMarker from '@/assets/images/rednavigationmarker.svg';
import navigationMarker from '@/assets/images/navigation.png';

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
    maxZoom: 20,
  });
  useEffect(() => {
    if (!map) return;
    const source = new VectorSource();
    const layer = new OLVectorLayer({
      source: source,
    });
    map?.addLayer(layer);

    navigator.geolocation.watchPosition(
      function (pos) {
        const coords = [pos.coords.longitude, pos.coords.latitude];
        source.clear(true);
        source.addFeatures([
          new Feature(circular(coords, pos.coords.accuracy).transform('EPSG:4326', map.getView().getProjection())),
          new Feature(new Point(fromLonLat(coords))),
        ]);
      },
      function (error) {
        alert(`ERROR: ${error.message}`);
      },
      {
        enableHighAccuracy: true,
      },
    );
    const locate = document.createElement('div');
    locate.className = 'ol-control ol-unselectable locate';
    locate.innerHTML = '<button title="Locate me">◎</button>';
    locate.addEventListener('click', function () {
      if (!source.isEmpty()) {
        map.getView().fit(source.getExtent(), {
          maxZoom: 18,
          duration: 500,
        });
      }
    });
    map.addControl(
      new Control({
        element: locate,
      }),
    );
    //! [style]
    const style = new Style({
      fill: new Fill({
        color: 'rgba(0, 0, 255, 0.2)',
      }),
      image: new Icon({
        src: navigationMarker,
        scale: 0.04,
        imgSize: [27, 55],
        rotateWithView: true,
      }),
    });
    layer.setStyle(style);

    function handleReading(quaternion) {
      // https://w3c.github.io/orientation-sensor/#model explains the order of
      // the 4 elements in the sensor.quaternion array.
      let [qx, qy, qz, qw] = quaternion;

      // When the phone is lying flat, we want to treat the direction toward the
      // top of the phone as the "forward" direction; when the phone is held
      // upright, we want to treat the direction out the back of the phone as the
      // "forward" direction.  So, let's determine the compass heading of the
      // phone based on the vector between these directions, i.e. at a 45-degree
      // angle between the positive Y-axis and the negative Z-axis in this figure:
      // https://w3c.github.io/orientation-sensor/#absoluteorientationsensor-model

      // To find the current "forward" direction of the phone, we want to take this
      // vector, (0, 1, -1), and apply the same rotation as the phone's rotation.
      const y = 1;
      const z = -1;

      // From experimentation, it looks like the quaternion from the sensor is
      // the inverse rotation, so we need to flip the fourth component.
      qw = -qw;

      // This section explains how to convert the quaternion to a rotation matrix:
      // https://w3c.github.io/orientation-sensor/#convert-quaternion-to-rotation-matrix
      // Now let's multiply the forward vector by the rotation matrix.
      const rx = y * (2 * qx * qy + 2 * qw * qz) + z * (2 * qx * qz - 2 * qw * qy);
      const ry = y * (1 - 2 * qx * qx - 2 * qz * qz) + z * (2 * qy * qz + 2 * qw * qx);
      const rz = y * (2 * qy * qz + 2 * qw * qx) + z * (1 - 2 * qx * qx - 2 * qy * qy);

      // This gives us a rotated vector indicating the "forward" direction of the
      // phone with respect to the earth.  We only care about the orientation of
      // this vector in the XY plane (the plane tangential to the ground), i.e.
      // the heading of the (rx, ry) vector, where (0, 1) is north.

      const radians = Math.atan2(ry, rx);
      const degrees = (radians * 180) / Math.PI; // counterclockwise from +X axis
      let heading = 90 - degrees;
      if (heading < 0) heading += 360;
      heading = Math.round(heading);

      //   info.value =
      //     qx.toFixed(3) +
      //     "\n" +
      //     qy.toFixed(3) +
      //     "\n" +
      //     qz.toFixed(3) +
      //     "\n" +
      //     qw.toFixed(3) +
      //     "\n\n" +
      //     rx.toFixed(3) +
      //     "\n" +
      //     ry.toFixed(3) +
      //     "\n" +
      //     rz.toFixed(3) +
      //     "\n\nHeading: " +
      //     heading;
      console.log(heading, 'heading');
      console.log((Math.PI / 180) * heading, '(Math.PI / 180) * heading');
      // To make the arrow point north, rotate it opposite to the phone rotation.
      style.getImage().setRotation((Math.PI / 180) * heading);
    }

    // See the API specification at: https://w3c.github.io/orientation-sensor
    // We use referenceFrame: 'screen' because the web page will rotate when
    // the phone switches from portrait to landscape.
    const sensor = new AbsoluteOrientationSensor({
      frequency: 5,
      referenceFrame: 'screen',
    });
    sensor.addEventListener('reading', () => {
      handleReading(sensor.quaternion);
    });

    // handleReading([0.509, -0.071, -0.19, 0.836]);

    Promise.all([
      navigator.permissions.query({ name: 'accelerometer' }),
      navigator.permissions.query({ name: 'magnetometer' }),
      navigator.permissions.query({ name: 'gyroscope' }),
    ]).then((results) => {
      if (results.every((result) => result.state === 'granted')) {
        sensor.start();
        console.log('Sensor started!');

        // stat.value = "Sensor started!";
      } else {
        console.log('No permissions to use AbsoluteOrientationSensor.');
        // stat.value = "No permissions to use AbsoluteOrientationSensor.";
      }
    });
  }, [map]);
  const homeProjectSummary: projectType[] = CoreModules.useAppSelector((state) => state.home.homeProjectSummary);
  useEffect(() => {
    if (homeProjectSummary?.length === 0) return;
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
          coordinates: project.centroid || [],
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
