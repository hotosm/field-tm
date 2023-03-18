import React, { useEffect, useState } from "react";
import IconButtonCard from "../utilities/IconButtonCard";
import BasicDialog from "../utilities/BasicDialog";
import DialogActions from "../components/DialogActions";
import "../styles/home.scss";
import { HomeActions } from "fmtm/HomeSlice";
import CoreModules from "fmtm/CoreModules";
import AssetModules from "fmtm/AssetModules";
import Control from "ol/control/Control";
import locationImg from "../assets/images/location.png";
import gridIcon from "../assets/images/grid.png";
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
    let btnsPosition = 22;
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

      //Div element
      let div = document.createElement("div");
      div.id = "btnsContainer";
      div.style.height = "inherit";
      div.style.width = "50px"
      div.style.backgroundColor = defaultTheme.palette.info["info_rgb"];

      //List buttons avoiding code duplication
      btnList.map((elmnt) => {
        //Add Button
        let btn = document.createElement("button");
        if (elmnt == "add") {
          btn.innerHTML = "+";
        } else if (elmnt == "minus") {
          btn.innerHTML = "-";
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
        btn.style.boxShadow =
          " 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)";
        btn.style.width = "40px";
        btn.style.height = "40px";
        btn.addEventListener("click", handleOnClick, false);

        //Add Button Div
        let btnDiv = document.createElement("div");
        btnDiv.className = "ol-unselectable ol-control";
        btnDiv.style.top = `${(btnsPosition = btnsPosition + 9)}%`;
        btnDiv.appendChild(btn);
        div.appendChild(btnDiv);
      });

      var control = new Control({
        element: div,
      });

      map.addControl(control);
    }
  }, [map]);

  return (
    <CoreModules.Stack spacing={1} direction={"column"}>
      <CoreModules.Stack
        style={{ border: `4px solid ${defaultTheme.palette.error.main}` }}
        justifyContent={"center"}
        height={608}
      >
        <div ref={mapElement} id="map_container">
          <BasicDialog
            open={stateDialog}
            title={`Task #${taskId}`}
            onClose={() => {
              dispatch(HomeActions.SetDialogStatus(false));
            }}
            actions={
              <DialogActions
                map={map}
                view={mainView}
                feature={featuresLayer}
                taskId={taskId}
              />
            }
          />
        </div>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default OpenLayersMap;
