import React, { useEffect, useState } from 'react';
import DialogTaskActions from '../components/DialogTaskActions';
import '../styles/home.scss';
import CoreModules from '../shared/CoreModules';
import Control from 'ol/control/Control';
import locationImg from '../assets/images/location.png';
import accDownImg from '../assets/images/acc-down.png';
import accUpImg from '../assets/images/acc-up.png';
import gridIcon from '../assets/images/grid.png';
import QrcodeComponent from './QrcodeComponent';
import * as ol from 'ol';
import { Point } from 'ol/geom';
import Vector from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { transform } from 'ol/proj';
import { Icon, Style } from 'ol/style';
import LocationImage from '../assets/images/location.png';
import AssetModules from '../shared/AssetModules';
let currentLocationLayer = null;
const OpenLayersMap = ({
  defaultTheme,
  stateDialog,
  params,
  state,
  taskId,
  top,
  map,
  mainView,
  featuresLayer,
  mapElement,
  environment,
  windowType,
}) => {
  const [toggleCurrentLoc, setToggleCurrentLoc] = useState(false);
  const [currentLocLayer, setCurrentLocLayer] = useState(null);
  function elastic(t) {
    return Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1;
  }

  useEffect(() => {
    let btnsPosition = 0;
    var btnList = ['add', 'minus', 'defaultPosition', 'taskBoundries'];

    if (map != undefined) {
      var handleOnClick = function (e) {
        if (e.target.id == 'add') {
          let actualZoom = map.getView().getZoom();
          map.getView().setZoom(actualZoom + 1);
        } else if (e.target.id == 'minus') {
          let actualZoom = map.getView().getZoom();
          map.getView().setZoom(actualZoom - 1);
        } else if (e.target.id == 'defaultPosition') {
          const sourceProjection = 'EPSG:4326'; // The current projection of the coordinates
          const targetProjection = 'EPSG:3857'; // The desired projection
          // Create a style for the marker
          var markerStyle = new Style({
            image: new Icon({
              src: LocationImage, // Path to your marker icon image
              anchor: [0.5, 1], // Anchor point of the marker icon (center bottom)
              scale: 2, // Scale factor for the marker icon
            }),
          });
          if ('geolocation' in navigator) {
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
          }
          setToggleCurrentLoc(!toggleCurrentLoc);

          // map.getView().setZoom(15);
        } else if (e.target.id == 'taskBoundries') {
          if (state.projectTaskBoundries.length != 0 && map != undefined) {
            if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(params.id)) != -1) {
              const index = state.projectTaskBoundries.findIndex(
                (project) => project.id == environment.decode(params.id),
              );
              const centroid =
                state.projectTaskBoundries[index].taskBoundries[
                  state.projectTaskBoundries[index].taskBoundries.length - 1
                ].outline_centroid.geometry.coordinates;

              mainView.animate({
                center: centroid,
                duration: 2000,
                easing: elastic,
              });
            }
          }

          map.getTargetElement().classList.remove('spinner');
        }
      };

      //List buttons avoiding code duplication
      btnList.map((elmnt, index) => {
        //Add Button
        let btn = document.createElement('button');
        if (elmnt == 'add') {
          btn.innerHTML = '+';
          btn.style.fontSize = defaultTheme.typography.fontSize;
        } else if (elmnt == 'minus') {
          btn.innerHTML = '-';
          btn.style.fontSize = defaultTheme.typography.fontSize;
        } else if (elmnt == 'defaultPosition') {
          let img = document.createElement('img');
          img.src = locationImg;
          img.id = `${elmnt}`;
          img.addEventListener('click', handleOnClick, false);
          btn.appendChild(img);
        } else if (elmnt == 'taskBoundries') {
          let img = document.createElement('img');
          img.src = gridIcon;
          img.id = `${elmnt}`;
          img.addEventListener('click', handleOnClick, false);
          btn.appendChild(img);
        }
        btn.id = `${elmnt}`;
        btn.style.backgroundColor = 'white';
        btn.style.boxShadow = `0 2px 2px 0 ${defaultTheme.palette.info['main']}`;
        btn.style.width = '40px';
        btn.style.height = '40px';
        btn.style.borderRadius = '50%';
        btn.addEventListener('click', handleOnClick, false);

        //Add Button Div
        let btnDiv = document.createElement('div');
        btnDiv.id = 'btnsContainer';
        btnDiv.style.borderRadius = '50%';
        btnDiv.className = 'ol-unselectable ol-control';
        index == 0
          ? (btnDiv.style.top = `${(btnsPosition = btnsPosition + 2)}%`)
          : (btnDiv.style.top = `${(btnsPosition = btnsPosition + 9)}%`);
        btnDiv.appendChild(btn);
        var control = new Control({
          element: btnDiv,
        });

        map.addControl(control);
      });

      const MapDetails = [
        {
          value: 'Ready',
          color: defaultTheme.palette.mapFeatureColors.ready,
          status: 'none',
        },
        {
          value: 'Locked For Mapping',
          color: defaultTheme.palette.mapFeatureColors.locked_for_mapping,
          status: 'lock',
        },
        {
          value: 'Ready For Validation',
          color: defaultTheme.palette.mapFeatureColors.mapped,
          status: 'none',
        },
        {
          value: 'Locked For Validation',
          color: defaultTheme.palette.mapFeatureColors.locked_for_validation,
          status: 'lock',
        },
        {
          value: 'Validated',
          color: defaultTheme.palette.mapFeatureColors.validated,
          status: 'none',
        },
        // {
        //   value: "Bad",
        //   color: defaultTheme.palette.mapFeatureColors.bad,
        //   status: "none",
        // },
        {
          value: 'More mapping needed',
          color: defaultTheme.palette.mapFeatureColors.invalidated,
          status: 'none',
        },
        {
          value: 'Locked',
          color: defaultTheme.palette.mapFeatureColors.invalidated,
          status: 'none',
          type: 'locked',
        },
      ];
      let legendContainer = document.createElement('div');
      legendContainer.className = 'legend-container';
      const legendLabel = document.createElement('span');
      legendLabel.innerHTML = 'Legend';
      const legendAccIcon = document.createElement('span');
      legendAccIcon.className = 'legend-acc-icon';
      let img = document.createElement('img');
      img.src = accDownImg;
      img.style.width = '24px';
      img.style.height = '24px';
      img.style.display = 'none';
      let accUp = document.createElement('img');
      accUp.src = accUpImg;
      accUp.style.width = '18px';
      accUp.style.height = '18px';
      // accUp.style.display = 'none';
      // img.id = `${elmnt}`;
      // legendAccIcon.addEventListener("click", function(){

      // }, false);
      legendAccIcon.appendChild(img);
      legendAccIcon.appendChild(accUp);
      legendContainer.appendChild(legendLabel);
      legendContainer.appendChild(legendAccIcon);

      // const legendContainer = document.getElementById('legendContainer');
      let legendContent = document.createElement('div');
      legendContent.className = 'legend-content';
      legendContent.style.display = 'none';
      legendContainer.style.margin = '552px 6px';
      MapDetails.forEach((detail) => {
        const legend = document.createElement('div');
        legend.className = 'legend';

        const legendText = document.createElement('span');
        legendText.className = 'legend-text';
        legendText.textContent = detail.value;

        if (detail.type === 'locked') {
          const legendSquare = document.createElement('img');
          legendSquare.className = 'legend-lock-img';
          // legendSquare.style.width = "20px";
          legendSquare.style.height = '20px';
          legendSquare.src = AssetModules.LockPng;
          legend.appendChild(legendText);
          legend.appendChild(legendSquare);
        } else {
          const legendSquare = document.createElement('div');
          legendSquare.className = 'legend-square';
          legendSquare.style.backgroundColor = detail.color;
          legend.appendChild(legendText);
          legend.appendChild(legendSquare);
        }

        legendContent.appendChild(legend);
      });
      legendContainer.appendChild(legendContent);
      // Add event listener to toggle the accordion content
      legendAccIcon.addEventListener('click', function () {
        if (legendContent.style.display === 'none') {
          accUp.style.display = 'none';
          img.style.display = 'inline';
          legendContent.style.display = 'block';
          legendContainer.style.margin = '200px 10px';
        } else {
          img.style.display = 'none';
          accUp.style.display = 'inline';
          legendContent.style.display = 'none';
          legendContainer.style.margin = '552px 6px';
        }
      });
      var controlx = new Control({
        element: legendContainer,
      });

      map.addControl(controlx);
    }
  }, [map]);

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

  return (
    <CoreModules.Stack spacing={1} p={2.5} direction={'column'}>
      <CoreModules.Stack
        style={{ border: `4px solid ${defaultTheme.palette.error.main}` }}
        justifyContent={'center'}
        height={608}
      >
        <div ref={mapElement} id="map_container"></div>
        <div id="popup" className="ol-popup">
          <a href="#" id="popup-closer" className="ol-popup-closer"></a>
          {featuresLayer != undefined && (
            <CoreModules.Stack>
              <DialogTaskActions map={map} view={mainView} feature={featuresLayer} taskId={taskId} />
              <QrcodeComponent defaultTheme={defaultTheme} task={taskId} type={windowType} />
            </CoreModules.Stack>
          )}
        </div>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default OpenLayersMap;
