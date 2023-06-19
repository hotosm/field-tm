import React, { useEffect, useRef, useState } from "react";
import "../../node_modules/ol/ol.css";
import "../styles/home.scss";
import WindowDimension from "fmtm/WindowDimension";
import MapDescriptionComponents from "../components/MapDescriptionComponents";
import ActivitiesPanel from "../components/ActivitiesPanel";
import OpenLayersMap from "../components/OpenLayersMap";
import environment from "fmtm/environment";
import { ProjectById } from "../api/Project";
import { ProjectActions } from "fmtm/ProjectSlice";
import CustomizedSnackbar from "fmtm/CustomizedSnackbar";
import { defaults } from "ol/control/defaults";
import OnScroll from "fmtm/OnScroll";
import { Tile as TileLayer } from "ol/layer.js";
import { OSM } from "ol/source.js";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import TasksLayer from "../layers/TasksLayer";
import Map from "ol/Map";
import View from "ol/View";
import { HomeActions } from "fmtm/HomeSlice";
import CoreModules from "fmtm/CoreModules";
import AssetModules from "fmtm/AssetModules";
import { ProjectBuildingGeojsonService } from "../api/SubmissionService";
import GeoJSON from 'ol/format/GeoJSON';
import { get } from 'ol/proj';

import Overlay from "ol/Overlay";
import { defaultStyles, getStyles } from "../components/MapComponent/OpenLayersComponent/helpers/styleUtils";
import ProjectMap from "../components/ProjectMap/ProjectMap";
// import XYZ from "ol/source/XYZ.js";
// import { toLonLat } from "ol/proj";
// import { toStringHDMS } from "ol/coordinate";
const basicGeojsonTemplate = {
  "type": "FeatureCollection",
  "features": []
};
const Home = () => {
  const dispatch = CoreModules.useDispatch();
  const params = CoreModules.useParams();
  const defaultTheme = CoreModules.useSelector((state) => state.theme.hotTheme);
  const state = CoreModules.useSelector((state) => state.project);

  const projectInfo = CoreModules.useSelector(
    (state) => state.home.selectedProject
  );
  const stateDialog = CoreModules.useSelector(
    (state) => state.home.dialogStatus
  );
  const stateSnackBar = CoreModules.useSelector((state) => state.home.snackbar);
  const [taskId, setTaskId] = useState();
  const mapElement = useRef();
  const [map, setMap] = useState();
  const [mainView, setView] = useState();
  const [featuresLayer, setFeaturesLayer] = useState();
  const [top, setTop] = useState(0);
  const encodedId = params.id;
  const { windowSize, type } = WindowDimension();
  const { y } = OnScroll(map, windowSize.width);

  //snackbar handle close funtion
  const handleClose = (event, reason) => {
    if (reason === "clickaway") {
      return;
    }
    dispatch(
      HomeActions.SetSnackBar({
        open: false,
        message: stateSnackBar.message,
        variant: stateSnackBar.variant,
        duration: 0,
      })
    );
  };

  //Fetch project for the first time
  useEffect(() => {

    if (
      state.projectTaskBoundries.findIndex(
        (project) => project.id == environment.decode(encodedId)
      ) == -1
    ) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]))

      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries
        ),
        state.projectTaskBoundries
      );
      // dispatch(ProjectBuildingGeojsonService(`${environment.baseApiUrl}/projects/${environment.decode(encodedId)}/features`))

    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]))
      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries
        ),
        state.projectTaskBoundries
      );
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
  }, [params.id]);

  useEffect(() => {
    const container = document.getElementById("popup");
    const closer = document.getElementById("popup-closer");

    const overlay = new Overlay({
      element: container,
      autoPan: {
        animation: {
          duration: 250,
        },
      },
    });
    /**
     * Function to setPosition of Popup to Undefined so that the popup closes
     */
    function handleClickOutside(event) {
      if (container && !container.contains(event.target)) {
        overlay.setPosition(undefined);
        closer.blur();
      }
    }
    // Bind the event listener for outside click and trigger handleClickOutside
    // document.addEventListener("mousedown", handleClickOutside);

    closer.style.textDecoration = "none";
    closer.style.color = defaultTheme.palette.info["main"];
    closer.onclick = function () {
      overlay.setPosition(undefined);
      closer.blur();
      return false;
    };

    const initalFeaturesLayer = new VectorLayer({
      source: new VectorSource(),
    });


    const view = new View({
      projection: "EPSG:4326",
      center: [0, 0],
      zoom: 4,
    });

    const initialMap = new Map({
      target: mapElement.current,
      controls: new defaults({
        attribution: false,
        zoom: false,
      }),
      layers: [
        new TileLayer({
          source: new OSM(),
          visible: true,
        }),
        initalFeaturesLayer
      ],
      overlays: [overlay],
      view: view,
    });
    initialMap.on("click", function (event) {
      initialMap.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
        const status = feature.getId()?.toString()?.replace("_", ",")?.split(",")?.[1];
        if (
          environment.tasksStatus.findIndex((data) => data.label == status) !=
          -1
        ) {
          setTaskId(feature?.getId()?.split("_")?.[0]);
          const coordinate = event.coordinate;
          overlay.setPosition(coordinate);
          setFeaturesLayer(feature);
        }
      });
    });

    initialMap.on("loadstart", function () {
      initialMap.getTargetElement().classList.add("spinner");
    });

    setMap(initialMap);
    setView(view);
    setFeaturesLayer(initalFeaturesLayer);

    return () => {
      /**
       * Removed handleClickOutside Eventlistener on unmount
       */
      document.removeEventListener("mousedown", handleClickOutside);
      mapElement.current = null;
      setFeaturesLayer();
      setView();
      setMap();
    };
  }, [params.id]);

  useEffect(() => {
    if (map != undefined) {
      const topX = map.getTargetElement().getBoundingClientRect().y;
      setTop(topX);
    }
  }, [map, y]);

  TasksLayer(map, mainView, featuresLayer);
  return (
    <CoreModules.Stack spacing={2}>
      {/* Home snackbar */}
      <CustomizedSnackbar
        duration={stateSnackBar.duration}
        open={stateSnackBar.open}
        variant={stateSnackBar.variant}
        message={stateSnackBar.message}
        handleClose={handleClose}
      />

      {/* Top project details heading medium dimension*/}
      <CoreModules.Stack
        sx={{ display: { md: "flex", xs: "none" } }}
        direction="column"
        justifyContent="center"
        spacing={5}
        alignItems={"center"}
      >
        <CoreModules.Stack
          direction={"row"}
          p={2}
          spacing={2}
          divider={
            <CoreModules.Divider
              sx={{ backgroundColor: defaultTheme.palette.grey["main"] }}
              orientation="vertical"
              flexItem
            />
          }
        >
          <CoreModules.Stack direction={"row"} justifyContent={"center"}>
            <AssetModules.LocationOn color="error" style={{ fontSize: 22 }} />
            <CoreModules.Typography variant="h1">
              {state.projectInfo.title}
            </CoreModules.Typography>
          </CoreModules.Stack>

          <CoreModules.Stack>
            <CoreModules.Typography
              variant="h4"
              fontSize={defaultTheme.typography.fontSize}
            >
              {`#${state.projectInfo.id}`}
            </CoreModules.Typography>
          </CoreModules.Stack>

          <CoreModules.Stack mt={"5%"}>
            <CoreModules.Typography
              variant="h4"
              fontSize={defaultTheme.typography.fontSize}
              color={defaultTheme.palette.warning["main"]}
            >
              {state.projectInfo.priority_str}
            </CoreModules.Typography>
          </CoreModules.Stack>
        </CoreModules.Stack>
      </CoreModules.Stack>

      {/* project Details Title */}
      <CoreModules.Stack
        sx={{ display: { xs: "flex", md: "none" } }}
        spacing={2}
      >
        <CoreModules.Stack direction={"row"} justifyContent={"center"}>
          <AssetModules.LocationOn
            color="error"
            style={{ marginTop: "1.5%", fontSize: 22 }}
          />
          <CoreModules.Typography variant="caption">
            {state.projectInfo.title}
          </CoreModules.Typography>
        </CoreModules.Stack>

        <CoreModules.Stack direction={"row"} justifyContent={"center"}>
          <CoreModules.Typography
            variant="h1"
            fontSize={defaultTheme.typography.fontSize}
          >
            {`#${state.projectInfo.id}`}
          </CoreModules.Typography>
        </CoreModules.Stack>

        <CoreModules.Stack direction={"row"} justifyContent={"center"}>
          <CoreModules.Typography
            variant="h1"
            fontSize={defaultTheme.typography.fontSize}
            color={defaultTheme.palette.warning["main"]}
          >
            {state.projectInfo.priority_str}
          </CoreModules.Typography>
        </CoreModules.Stack>
      </CoreModules.Stack>

      {/* Center description and map */}
      <CoreModules.Stack direction={"column"} spacing={1}>
        <MapDescriptionComponents
          defaultTheme={defaultTheme}
          state={state}
          type={type}
        />
        <CoreModules.Stack
          direction={"column"}
          spacing={1}
          justifyContent="flex-end"
        >
          <CoreModules.Link
            to={`/projectInfo/${encodedId}`}
            style={{
              display: "flex",
              justifyContent: "flex-end",
              textDecoration: "none",
              marginRight: "15px",
            }}
          >
            <CoreModules.Button
              variant="contained"
              color="error"
              sx={{ width: "10%" }}
            >
              ProjectInfo
            </CoreModules.Button>
          </CoreModules.Link>
        </CoreModules.Stack>
        {/* <ProjectMap /> */}
        {params?.id && <OpenLayersMap
          key={params.id}
          defaultTheme={defaultTheme}
          stateDialog={stateDialog}
          params={params}
          state={state}
          taskId={taskId}
          top={top}
          featuresLayer={featuresLayer}
          map={map}
          mainView={mainView}
          mapElement={mapElement}
          environment={environment}
          windowType={type}
        />}
      </CoreModules.Stack>

      {/* project Details Tabs */}
      <CoreModules.Stack
        sx={{ display: "flex", flexDirection: "row", justifyContent: "center" }}
      >
        {/* <BasicTabs listOfData={panelData} /> */}
        <ActivitiesPanel
          params={params}
          state={state.projectTaskBoundries}
          defaultTheme={defaultTheme}
          map={map}
          view={mainView}
          mapDivPostion={y}
          states={state}
        />
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default Home;
