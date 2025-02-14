import pngbluedot from '@/assets/images/png bluedot.png';
import LocationDot from '@/assets/images/LocationDot.png';
import { Fill } from 'ol/style';
import VectorSource from 'ol/source/Vector';
import OLVectorLayer from 'ol/layer/Vector';
import { Feature } from 'ol';
import { Point } from 'ol/geom';
import { fromLonLat } from 'ol/proj';
import { circular } from 'ol/geom/Polygon';
import { Style } from 'ol/style';
import { Icon } from 'ol/style';
import VectorLayer from 'ol/layer/Vector';
import { CommonActions } from '@/store/slices/CommonSlice';

export const Geolocation = (map, geolocationStatus, dispatch) => {
  if (!map) return;

  // check firefox or safari browser as it doesn't support browser's Sensor API
  // @ts-ignore
  const isFirefox = typeof InstallTrigger !== 'undefined';
  const isSafari =
    // @ts-ignore
    /constructor/i.test(window.HTMLElement) ||
    (function (p) {
      return p.toString() === '[object SafariRemoteNotification]';
      // @ts-ignore
    })(!window['safari'] || (typeof safari !== 'undefined' && window['safari'].pushNotification));

  const locationIconStyle = new Style({
    fill: new Fill({
      color: 'rgba(0, 0, 255, 0.2)',
    }),
    image: new Icon({
      src: isFirefox || isSafari ? LocationDot : pngbluedot,
      scale: 0.09,
      imgSize: [27, 55],
      rotateWithView: true,
    }),
  });

  const source = new VectorSource();
  const layer = new OLVectorLayer({
    source: source,
    properties: {
      name: 'geolocation',
    },
  });

  let hasGeolocationLayer = false;
  const layers = map.getAllLayers();
  layers.map((layerx) => {
    if (layerx instanceof VectorLayer) {
      const layerName = layerx.getProperties().name;
      if (layerName === 'geolocation') {
        hasGeolocationLayer = true;
      }
    }
  });

  // only add layer if geolocationStatus is on & has no prior layer with name geolocation
  if (geolocationStatus && !hasGeolocationLayer) {
    map?.addLayer(layer);
  }

  if (geolocationStatus) {
    // zooom to current location extent
    navigator.geolocation.getCurrentPosition((position) => {
      const currentCoordinate = [position.coords.longitude, position.coords.latitude];
      const coordinatePolygon = circular(currentCoordinate, position.coords.accuracy).transform(
        'EPSG:4326',
        map.getView().getProjection(),
      );
      map.getView().fit(coordinatePolygon.getExtent(), {
        padding: [10, 10, 10, 10],
      });
    });

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

    layer.setStyle(locationIconStyle);

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

      // To make the arrow point north, rotate it opposite to the phone rotation.
      locationIconStyle.getImage().setRotation((Math.PI / 180) * heading);
    }

    if (isFirefox || isSafari) {
      dispatch(
        CommonActions.SetSnackBar({
          message: "Unable to handle device orientation. Your browser doesn't support device orientation sensors.",
        }),
      );
    } else {
      // See the API specification at: https://w3c.github.io/orientation-sensor
      // We use referenceFrame: 'screen' because the web page will rotate when
      // the phone switches from portrait to landscape.
      const sensor = new AbsoluteOrientationSensor({
        frequency: 60,
        referenceFrame: 'screen',
      });
      sensor.addEventListener('reading', (event) => {
        layer.on('postrender', handleReading(sensor.quaternion));
      });
      // handleReading([0.509, -0.071, -0.19, 0.836]);

      Promise.all([
        navigator.permissions.query({ name: 'accelerometer' }),
        navigator.permissions.query({ name: 'magnetometer' }),
        navigator.permissions.query({ name: 'gyroscope' }),
      ]).then((results) => {
        if (results.every((result) => result.state === 'granted')) {
          sensor.start();
          // stat.value = "Sensor started!";
        } else {
          // stat.value = "No permissions to use AbsoluteOrientationSensor.";
        }
      });
    }
  }

  // remove the geolocation layer if geolocationStatus turned off
  if (!geolocationStatus) {
    let layerToBeRemoved;
    layers.map((layerx) => {
      if (layerx instanceof VectorLayer) {
        const layerName = layerx.getProperties().name;
        if (layerName === 'geolocation') {
          layerToBeRemoved = layerx;
        }
      }
    });
    if (layerToBeRemoved) {
      map?.removeLayer(layerToBeRemoved);
    }
  }
};
