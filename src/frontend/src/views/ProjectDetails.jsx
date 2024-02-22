// TODO should this be deleted??

import React, { useEffect, useRef, useState } from 'react';
import '../styles/home.scss';
import WindowDimension from '@/hooks/WindowDimension';
import MapDescriptionComponents from '@/components/MapDescriptionComponents';
import ActivitiesPanel from '@/components/ActivitiesPanel';
import OpenLayersMap from '@/components/OpenLayersMap';
import environment from '@/environment';
import { ProjectById } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import CustomizedSnackbar from '@/utilities/CustomizedSnackbar';
import { defaults } from 'ol/control/defaults';
import OnScroll from '@/hooks/OnScroll';
import { Tile as TileLayer } from 'ol/layer.js';
import { OSM } from 'ol/source.js';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import TasksLayer from '@/components/TasksLayer';
import Map from 'ol/Map';
import View from 'ol/View';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import GeoJSON from 'ol/format/GeoJSON';
import FmtmLogo from '@/assets/images/hotLog.png';

import GenerateBasemap from '@/components/GenerateBasemap';
import { get } from 'ol/proj';
import { buildingStyle, basicGeojsonTemplate } from '@/utilities/mapUtils';
import MapLegends from '@/components/MapLegends';
import TaskSectionPopup from '@/components/ProjectDetails/TaskSectionPopup';
import DialogTaskActions from '@/components/DialogTaskActions';
import QrcodeComponent from '@/components/QrcodeComponent';
import MobileFooter from '@/components/ProjectDetails/MobileFooter';
import MobileActivitiesContents from '@/components/ProjectDetails/MobileActivitiesContents';
import BottomSheet from '@/components/common/BottomSheet';
import MobileProjectInfoContent from '@/components/ProjectDetails/MobileProjectInfoContent';
import { useNavigate } from 'react-router-dom';
import ProjectOptions from '@/components/ProjectDetails/ProjectOptions';

const Home = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();

  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const state = CoreModules.useAppSelector((state) => state.project);
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);

  const projectInfo = CoreModules.useAppSelector((state) => state.home.selectedProject);
  const stateDialog = CoreModules.useAppSelector((state) => state.home.dialogStatus);
  const stateSnackBar = CoreModules.useAppSelector((state) => state.home.snackbar);
  const [taskId, setTaskId] = useState();
  const [toggleGenerateModal, setToggleGenerateModal] = useState(false);
  const mapElement = useRef();
  const [map, setMap] = useState();
  const [mainView, setView] = useState();
  const [featuresLayer, setFeaturesLayer] = useState();
  const [top, setTop] = useState(0);
  const encodedId = params.id;
  const decodedId = environment.decode(encodedId);
  const { windowSize, type } = WindowDimension();
  const { y } = OnScroll(map, windowSize.width);
  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const mobileFooterSelection = CoreModules.useAppSelector((state) => state.project.mobileFooterSelection);
  const [toggleAction, setToggleAction] = useState(false);

  //snackbar handle close funtion
  const handleClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    dispatch(
      HomeActions.SetSnackBar({
        open: false,
        message: stateSnackBar.message,
        variant: stateSnackBar.variant,
        duration: 0,
      }),
    );
  };

  //Fetch project for the first time
  useEffect(() => {
    console.log('HERE');
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(encodedId)) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
    }
    if (Object.keys(state.projectInfo).length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
    return () => {
      dispatch(ProjectActions.SetProjectDataExtract(null));
    };
  }, [params.id]);

  useEffect(() => {
    // const container = document.getElementById('popup');
    // const closer = document.getElementById('popup-closer');

    // const overlay = new Overlay({
    //   element: container,
    //   autoPan: {
    //     animation: {
    //       duration: 250,
    //     },
    //   },
    // });
    /**
     * Function to setPosition of Popup to Undefined so that the popup closes
     */
    // function handleClickOutside(event) {
    //   if (container && !container.contains(event.target)) {
    //     overlay.setPosition(undefined);
    //     closer.blur();
    //   }
    // }
    // Bind the event listener for outside click and trigger handleClickOutside
    // document.addEventListener("mousedown", handleClickOutside);

    // closer.style.textDecoration = 'none';
    // closer.style.color = defaultTheme.palette.info['main'];
    // closer.onclick = function () {
    //   overlay.setPosition(undefined);
    //   closer.blur();
    //   return false;
    // };

    const initalFeaturesLayer = new VectorLayer({
      source: new VectorSource(),
    });

    const view = new View({
      projection: 'EPSG:3857',
      center: [0, 0],
      zoom: 1,
    });
    // const mapboxBaseLayer = new MapboxVector({
    //   styleUrl: "mapbox://styles/mapbox/bright-v9",
    //   accessToken:
    //     "pk.eyJ1IjoidmFydW4yNjYiLCJhIjoiY2xsNmU1ZWtrMGhoNjNkcWpqejhhb2IycyJ9.DiPTq9YEErGUHhgW4pINdg",
    // });
    // mapboxBaseLayer.setZIndex(0);
    const initialMap = new Map({
      target: mapElement.current,
      controls: new defaults({
        attribution: false,
        zoom: false,
      }),
      layers: [
        initalFeaturesLayer,
        // mapboxBaseLayer,
        new TileLayer({
          source: new OSM(),
          visible: true,
        }),
      ],
      // overlays: [overlay],
      view: view,
    });
    initialMap.on('click', function (event) {
      initialMap.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
        const status = feature.getId()?.toString()?.replace('_', ',')?.split(',')?.[1];
        if (environment.tasksStatus.findIndex((data) => data.label == status) != -1) {
          setTaskId(feature?.getId()?.split('_')?.[0]);
          const coordinate = event.coordinate;
          // overlay.setPosition(coordinate);
          setFeaturesLayer(feature);
          dispatch(ProjectActions.ToggleTaskModalStatus(true));
          document.querySelector('#project-details-map').scrollIntoView({
            behavior: 'smooth',
          });
          // dispatch(
          //   ProjectDataExtractService(
          //     `${import.meta.env.VITE_API_URL}/projects/${decodedId}/features?task_id=${
          //       feature?.getId()?.split('_')?.[0]
          //     }`,
          //   ),
          // );
        }
      });
    });

    initialMap.on('loadstart', function () {
      initialMap.getTargetElement().classList.add('spinner');
    });

    setMap(initialMap);
    setView(view);
    setFeaturesLayer(initalFeaturesLayer);
    dispatch(ProjectActions.ToggleTaskModalStatus(false));

    return () => {
      /**
       * Removed handleClickOutside Eventlistener on unmount
       */
      // document.removeEventListener('mousedown', handleClickOutside);
      mapElement.current = null;
      setFeaturesLayer();
      setView();
      setMap();
    };
  }, [params.id]);

  useEffect(() => {
    if (!map) return;
    map.on('click', function (event) {
      map.forEachFeatureAtPixel(event.pixel, function (feature) {
        let extent = feature.getGeometry().getExtent();
        if (windowSize.width < 768) {
          map.getView().fit(extent, {
            padding: [10, 20, 300, 20],
          });
        } else {
          map.getView().fit(extent, {
            padding: [20, 350, 50, 10],
          });
        }
      });
    });
    return () => {};
  }, [taskModalStatus, windowSize.width]);

  // useEffect(() => {
  //   if (map != undefined) {
  //     const topX = map.getTargetElement().getBoundingClientRect().y;
  //     setTop(topX);
  //   }
  // }, [map, y]);

  useEffect(() => {
    if (!map) return;
    if (!projectBuildingGeojson) return;
    const taskBuildingGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectBuildingGeojson?.map((feature) => ({
          ...feature.geometry,
          id: feature.id,
        })),
      ],
    };
    const initalFeaturesLayer = new VectorLayer({
      source: new VectorSource({
        features: new GeoJSON().readFeatures(taskBuildingGeojsonFeatureCollection, {
          featureProjection: get('EPSG:3857'),
        }),
      }),
      style: buildingStyle,
      declutter: true,
    });
    map.addLayer(initalFeaturesLayer);
    return () => {
      map.removeLayer(initalFeaturesLayer);
    };
  }, [map, projectBuildingGeojson]);

  TasksLayer(map, mainView, featuresLayer);

  return (
    <div>
      {/* Customized Modal For Generate Tiles */}
      <div>
        <GenerateBasemap
          toggleGenerateModal={toggleGenerateModal}
          setToggleGenerateModal={setToggleGenerateModal}
          projectInfo={state.projectInfo}
        />

        {/* Home snackbar */}
        <CustomizedSnackbar
          duration={stateSnackBar.duration}
          open={stateSnackBar.open}
          variant={stateSnackBar.variant}
          message={stateSnackBar.message}
          handleClose={handleClose}
        />
      </div>

      {/* Top project details heading medium dimension*/}
      {windowSize.width >= 640 && (
        <div>
          <CoreModules.Stack
            sx={{ display: { md: 'flex', xs: 'none' } }}
            direction="column"
            justifyContent="center"
            spacing={5}
            alignItems={'center'}
          >
            <CoreModules.Stack
              direction={'row'}
              p={2}
              spacing={2}
              divider={
                <CoreModules.Divider
                  sx={{ backgroundColor: defaultTheme.palette.grey['main'] }}
                  orientation="vertical"
                  flexItem
                />
              }
            >
              <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                <AssetModules.LocationOn color="error" style={{ fontSize: 22 }} />
                <CoreModules.Typography variant="h1">{state.projectInfo.title}</CoreModules.Typography>
              </CoreModules.Stack>

              <CoreModules.Stack>
                <CoreModules.Typography variant="h4" fontSize={defaultTheme.typography.fontSize}>
                  {`#${state.projectInfo.id}`}
                </CoreModules.Typography>
              </CoreModules.Stack>

              <CoreModules.Stack mt={'5%'}>
                <CoreModules.Typography
                  variant="h4"
                  fontSize={defaultTheme.typography.fontSize}
                  color={defaultTheme.palette.warning['main']}
                >
                  {state.projectInfo.priority_str}
                </CoreModules.Typography>
              </CoreModules.Stack>
            </CoreModules.Stack>
          </CoreModules.Stack>
          {/* project Details Title */}
          <CoreModules.Stack sx={{ display: { xs: 'flex', md: 'none' } }} spacing={2}>
            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
              <AssetModules.LocationOn color="error" style={{ marginTop: '1.5%', fontSize: 22 }} />
              <CoreModules.Typography variant="caption">{state.projectInfo.title}</CoreModules.Typography>
            </CoreModules.Stack>

            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
              <CoreModules.Typography variant="h1" fontSize={defaultTheme.typography.fontSize}>
                {`#${state.projectInfo.id}`}
              </CoreModules.Typography>
            </CoreModules.Stack>

            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
              <CoreModules.Typography
                variant="h1"
                fontSize={defaultTheme.typography.fontSize}
                color={defaultTheme.palette.warning['main']}
              >
                {state.projectInfo.priority_str}
              </CoreModules.Typography>
            </CoreModules.Stack>
          </CoreModules.Stack>
        </div>
      )}

      {/* Center description and map */}
      <CoreModules.Stack direction={'column'} spacing={1}>
        {windowSize.width >= 640 && (
          <div>
            <MapDescriptionComponents defaultTheme={defaultTheme} state={state} type={type} />
            <ProjectOptions setToggleGenerateModal={setToggleGenerateModal} />
          </div>
        )}

        {params?.id && (
          <div className="fmtm-relative sm:fmtm-static">
            <OpenLayersMap
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
            />
            <div
              className="fmtm-absolute fmtm-top-4 fmtm-left-4 fmtm-bg-white fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-red-50 fmtm-duration-300 fmtm-border-[1px] sm:fmtm-hidden fmtm-cursor-pointer"
              onClick={() => navigate('/')}
            >
              <AssetModules.ArrowBackIcon className="fmtm-text-grey-800" />
            </div>
            {mobileFooterSelection === 'projectInfo' && (
              <BottomSheet
                body={<MobileProjectInfoContent projectInfo={state.projectInfo} />}
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection('explore'))}
              />
            )}
            {mobileFooterSelection === 'activities' && (
              <BottomSheet
                body={<MobileActivitiesContents map={map} view={mainView} mapDivPostion={y} />}
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection('explore'))}
              />
            )}
            {mobileFooterSelection === 'explore' && (
              <div className="fmtm-absolute fmtm-bottom-[5.8rem] sm:fmtm-hidden">
                <img src={FmtmLogo} alt="Hot Fmtm Logo" className="fmtm-ml-2 fmtm-z-10 fmtm-w-[5.2rem]" />
              </div>
            )}
            {mobileFooterSelection === 'mapLegend' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[12vh]">
                    <MapLegends defaultTheme={defaultTheme} />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection('explore'))}
              />
            )}
            {mobileFooterSelection === 'others' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[12vh]">
                    <ProjectOptions setToggleGenerateModal={setToggleGenerateModal} />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection('explore'))}
              />
            )}

            <MobileFooter />
          </div>
        )}
      </CoreModules.Stack>

      {windowSize.width >= 640 && (
        <div>
          {/* project Details Tabs */}
          <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
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
        </div>
      )}
      {featuresLayer != undefined && (
        <TaskSectionPopup
          body={
            <div>
              <DialogTaskActions map={map} view={mainView} feature={featuresLayer} taskId={taskId} />
              <QrcodeComponent defaultTheme={defaultTheme} task={taskId} type={type} />
            </div>
          }
        />
      )}
    </div>
  );
};

export default Home;
