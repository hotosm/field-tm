import React, { useEffect, useState } from "react";
import IconButtonCard from "../utilities/IconButtonCard";
import BasicDialog from "../utilities/BasicDialog";
import DialogTaskActions from "../components/DialogTaskActions";
import "../styles/home.scss";
import { HomeActions } from "fmtm/HomeSlice";
import CoreModules from "fmtm/CoreModules";
import AssetModules from "fmtm/AssetModules";
import Control from "ol/control/Control";
import locationImg from "../assets/images/location.png";
import gridIcon from "../assets/images/grid.png";
import QrcodeComponent from "./QrcodeComponent";
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
  function elastic(t) {
    return (
      Math.pow(2, -10 * t) * Math.sin(((t - 0.075) * (2 * Math.PI)) / 0.3) + 1
    );
  }
  const dispatch = CoreModules.useDispatch();

  useEffect(() => {
    let btnsPosition = 0;
    var btnList = ["add", "minus", "defaultPosition", "taskBoundries"];

    if (map != undefined) {
      var handleOnClick = function (e) {
        if (e.target.id == "add") {
          let actualZoom = map.getView().getZoom();
          map.getView().setZoom(actualZoom + 1);
        } else if (e.target.id == "minus") {
          let actualZoom = map.getView().getZoom();
          map.getView().setZoom(actualZoom - 1);
        } else if (e.target.id == "defaultPosition") {
          map.getView().setZoom(15);
        } else if (e.target.id == "taskBoundries") {
          if (state.projectTaskBoundries.length != 0 && map != undefined) {
            if (
              state.projectTaskBoundries.findIndex(
                (project) => project.id == environment.decode(params.id)
              ) != -1
            ) {
              const index = state.projectTaskBoundries.findIndex(
                (project) => project.id == environment.decode(params.id)
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

          map.getTargetElement().classList.remove("spinner");
        }
      };

      //List buttons avoiding code duplication
      btnList.map((elmnt, index) => {
        //Add Button
        let btn = document.createElement("button");
        if (elmnt == "add") {
          btn.innerHTML = "+";
          btn.style.fontSize = defaultTheme.typography.fontSize;
        } else if (elmnt == "minus") {
          btn.innerHTML = "-";
          btn.style.fontSize = defaultTheme.typography.fontSize;
        } else if (elmnt == "defaultPosition") {
          let img = document.createElement("img");
          img.src = locationImg;
          img.id = `${elmnt}`;
          img.addEventListener("click", handleOnClick, false);
          btn.appendChild(img);
        } else if (elmnt == "taskBoundries") {
          let img = document.createElement("img");
          img.src = gridIcon;
          img.id = `${elmnt}`;
          img.addEventListener("click", handleOnClick, false);
          btn.appendChild(img);
        }
        btn.id = `${elmnt}`;
        btn.style.backgroundColor = "white";
        btn.style.boxShadow = `0 2px 2px 0 ${defaultTheme.palette.info["main"]}`;
        btn.style.width = "40px";
        btn.style.height = "40px";
        btn.style.borderRadius = "50%";
        btn.addEventListener("click", handleOnClick, false);

        //Add Button Div
        let btnDiv = document.createElement("div");
        btnDiv.id = "btnsContainer";
        btnDiv.style.borderRadius = "50%";
        btnDiv.className = "ol-unselectable ol-control";
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
            status: 'none'
        },
        {
            value: 'Locked For Mapping',
            color: defaultTheme.palette.mapFeatureColors.locked_for_mapping,
            status: 'lock'
        },
        {
            value: 'Locked For Validation',
            color: defaultTheme.palette.mapFeatureColors.locked_for_validation,
            status: 'lock'
        },
        {
            value: 'Ready For Validation',
            color: defaultTheme.palette.mapFeatureColors.mapped,
            status: 'none'
        },
        {
            value: 'Validated',
            color: defaultTheme.palette.mapFeatureColors.validated,
            status: 'none'
        },
        {
            value: 'Bad',
            color: defaultTheme.palette.mapFeatureColors.bad,
            status: 'none'
        },
        {
            value: 'More mapping needed',
            color: defaultTheme.palette.mapFeatureColors.invalidated,
            status: 'none'
        }
    ]
    let legendContainer = document.createElement("div");
    legendContainer.className = "legend-container";


    // const legendContainer = document.getElementById('legendContainer');
    MapDetails.forEach((detail) => {
      const legend = document.createElement('div');
      legend.className = 'legend';

      const legendText = document.createElement('span');
      legendText.className = 'legend-text';
      legendText.textContent = detail.value;

      const legendSquare = document.createElement('div');
      legendSquare.className = 'legend-square';
      legendSquare.style.backgroundColor = detail.color;

      legend.appendChild(legendText);
      legend.appendChild(legendSquare);

      legendContainer.appendChild(legend);
    });

    var controlx = new Control({
      element: legendContainer,
    });

    map.addControl(controlx);
    }
  }, [map]);

  return (
    <CoreModules.Stack spacing={1} p={2.5} direction={"column"}>
      <CoreModules.Stack
        style={{ border: `4px solid ${defaultTheme.palette.error.main}` }}
        justifyContent={"center"}
        height={608}
      >
        <div ref={mapElement} id="map_container"></div>
        <div id="popup" className="ol-popup">
          <a href="#" id="popup-closer" className="ol-popup-closer"></a>
          {featuresLayer != undefined && (
            <CoreModules.Stack>
              <DialogTaskActions
                map={map}
                view={mainView}
                feature={featuresLayer}
                taskId={taskId}
              />
              <QrcodeComponent
                defaultTheme={defaultTheme}
                task={taskId}
                type={windowType}
              />
            </CoreModules.Stack>
          )}
        </div>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default OpenLayersMap;
