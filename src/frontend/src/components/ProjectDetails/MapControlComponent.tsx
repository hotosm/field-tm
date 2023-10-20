import React, { useEffect, useState } from 'react';
import AssetModules from '../../shared/AssetModules';
import { transform } from 'ol/proj';
import * as ol from 'ol';
import { Point } from 'ol/geom';
import Vector from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Style } from 'ol/style';
import { Icon } from 'ol/style';
import LocationImage from '../../assets/images/location.png';
import VectorLayer from 'ol/layer/Vector';

const MapControlComponent = ({ map }) => {
  const btnList = [
    {
      id: 'add',
      icon: <AssetModules.AddIcon />,
    },
    {
      id: 'minus',
      icon: <AssetModules.RemoveIcon />,
    },
    {
      id: 'currentLocation',
      icon: <AssetModules.MyLocationIcon />,
    },
    {
      id: 'taskBoundries',
      icon: <AssetModules.CropFreeIcon />,
    },
  ];
  const [toggleCurrentLoc, setToggleCurrentLoc] = useState(false);
  const [currentLocLayer, setCurrentLocLayer] = useState(null);
  useEffect(() => {
    if (!map) return;
    if (!currentLocLayer) return;
    map.addLayer(currentLocLayer);
    map.getView().fit(currentLocLayer.getSource().getExtent(), {
      maxZoom: 18,
      duration: 500,
    });
    return () => {
      map.removeLayer(currentLocLayer);
    };
  }, [map, currentLocLayer]);
  const handleOnClick = (btnId) => {
    if (btnId === 'add') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom + 1);
    } else if (btnId === 'minus') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom - 1);
    } else if (btnId === 'currentLocation') {
      setToggleCurrentLoc(!toggleCurrentLoc);
      const sourceProjection = 'EPSG:4326'; // The current projection of the coordinates
      const targetProjection = 'EPSG:3857'; // The desired projection
      var markerStyle = new Style({
        image: new Icon({
          src: LocationImage, // Path to your marker icon image
          anchor: [0.5, 1], // Anchor point of the marker icon (center bottom)
          scale: 2, // Scale factor for the marker icon
        }),
      });
      if ('geolocation' in navigator) {
        if (!toggleCurrentLoc) {
          navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const convertedCoordinates = transform([lng, lat], sourceProjection, targetProjection);
            const positionFeature = new ol.Feature(new Point(convertedCoordinates));
            const positionLayer = new Vector({
              source: new VectorSource({
                features: [positionFeature],
              }),
            });
            positionFeature.setStyle(markerStyle);
            setCurrentLocLayer(positionLayer);
          });
        } else {
          setCurrentLocLayer(null);
        }
      }
    } else if (btnId === 'taskBoundries') {
      const layers = map.getAllLayers();
      let extent;
      layers.map((layer) => {
        if (layer instanceof VectorLayer) {
          const layerName = layer.getProperties().name;
          if (layerName === 'project-area') {
            extent = layer.getSource().getExtent();
          }
        }
      });
      map.getView().fit(extent, {
        padding: [10, 10, 10, 10],
      });
    }
  };

  return (
    <div className="fmtm-absolute fmtm-top-[20px] fmtm-right-5 fmtm-z-[99] fmtm-flex fmtm-flex-col fmtm-gap-4">
      {btnList.map((btn) => (
        <div key={btn.id}>
          <div
            className="fmtm-bg-white fmtm-rounded-full fmtm-p-2 hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300"
            onClick={() => handleOnClick(btn.id)}
          >
            {btn.icon}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MapControlComponent;
