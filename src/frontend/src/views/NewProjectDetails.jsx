import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import WindowDimension from '../hooks/WindowDimension';
import MapDescriptionComponents from '../components/MapDescriptionComponents';
import ActivitiesPanel from '../components/ActivitiesPanel';
import environment from '../environment';
import { ProjectById } from '../api/Project';
import { ProjectActions } from '../store/slices/ProjectSlice';
import CustomizedSnackbar from '../utilities/CustomizedSnackbar';
import OnScroll from '../hooks/OnScroll';
import { HomeActions } from '../store/slices/HomeSlice';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import FmtmLogo from '../assets/images/hotLog.png';
import GenerateBasemap from '../components/GenerateBasemap';
import { ProjectBuildingGeojsonService } from '../api/SubmissionService';
import TaskSectionPopup from '../components/ProjectDetails/TaskSectionPopup';
import DialogTaskActions from '../components/DialogTaskActions';
import QrcodeComponent from '../components/QrcodeComponent';
import MobileFooter from '../components/ProjectDetails/MobileFooter';
import MobileActivitiesContents from '../components/ProjectDetails/MobileActivitiesContents';
import BottomSheet from '../components/common/BottomSheet';
import MobileProjectInfoContent from '../components/ProjectDetails/MobileProjectInfoContent';
import { useNavigate } from 'react-router-dom';
import ProjectOptions from '../components/ProjectDetails/ProjectOptions';
import { MapContainer as MapComponent, useOLMap } from '../components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../components/MapComponent/OpenLayersComponent/LayerSwitcher/index';
import MapControlComponent from '../components/ProjectDetails/MapControlComponent';
import { VectorLayer } from '../components/MapComponent/OpenLayersComponent/Layers';
import { geojsonObjectModel } from '../constants/geojsonObjectModal';
import { basicGeojsonTemplate } from '../utilities/mapUtils';
import getTaskStatusStyle from '../utilfunctions/getTaskStatusStyle';
import { defaultStyles } from '../components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MapLegends from '../components/MapLegends';
import Accordion from '../components/common/Accordion';
import { Geolocation } from '@capacitor/geolocation';
import { Icon, Style } from 'ol/style';
import { Motion } from '@capacitor/motion';
import locationArc from '../assets/images/locationArc.png';
import { CommonActions } from '../store/slices/CommonSlice';

const Home = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();
  const { windowSize, type } = WindowDimension();

  const [taskId, setTaskId] = useState();
  const [mainView, setView] = useState();
  const [featuresLayer, setFeaturesLayer] = useState();
  const [toggleGenerateModal, setToggleGenerateModal] = useState(false);
  const [taskBuildingGeojson, setTaskBuildingGeojson] = useState(null);
  const [initialFeaturesLayer, setInitialFeaturesLayer] = useState(null);
  const [currentCoordinate, setCurrentCoordinate] = useState({ latitude: null, longitude: null });
  const [positionGeojson, setPositionGeojson] = useState(null);
  const [deviceRotation, setDeviceRotation] = useState(0);

  const encodedId = params.id;
  const decodedId = environment.decode(encodedId);
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const state = CoreModules.useAppSelector((state) => state.project);
  const projectInfo = CoreModules.useAppSelector((state) => state.home.selectedProject);
  const stateSnackBar = CoreModules.useAppSelector((state) => state.home.snackbar);
  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const mobileFooterSelection = CoreModules.useAppSelector((state) => state.project.mobileFooterSelection);
  const mapTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const geolocationStatus = CoreModules.useAppSelector((state) => state.project.geolocationStatus);

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
    dispatch(ProjectActions.SetNewProjectTrigger());
    if (state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(encodedId)) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
      // dispatch(ProjectBuildingGeojsonService(`${import.meta.env.VITE_API_URL}/projects/${environment.decode(encodedId)}/features`))
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(state.projectTaskBoundries, environment.decode(encodedId)));
    }
    if (Object.keys(state.projectInfo)?.length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id != environment.decode(encodedId)) {
        dispatch(ProjectActions.SetProjectInfo(projectInfo));
      }
    }
    return () => {
      dispatch(ProjectActions.SetProjectBuildingGeojson(null));
    };
  }, [params.id]);

  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    // maxZoom: 17,
  });

  const { y } = OnScroll(map, windowSize.width);

  useEffect(() => {
    if (!map) return;

    const features = state.projectTaskBoundries[0]?.taskBoundries?.map((feature) => ({
      type: 'Feature',
      geometry: { ...feature.outline_geojson.geometry },
      properties: {
        ...feature.outline_geojson.properties,
        centroid: feature.bbox,
      },
      id: `${feature.project_task_name}_${feature.task_status_str}`,
    }));
    const taskBuildingGeojsonFeatureCollection = {
      ...geojsonObjectModel,
      features: features,
    };
    setInitialFeaturesLayer(taskBuildingGeojsonFeatureCollection);
  }, [state.projectTaskBoundries[0]?.taskBoundries?.length]);

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

    setTaskBuildingGeojson(taskBuildingGeojsonFeatureCollection);
  }, [map, projectBuildingGeojson]);

  // TasksLayer(map, mainView, featuresLayer);
  const projectClickOnMap = (properties, feature) => {
    setFeaturesLayer(feature, 'feature');
    let extent = properties.geometry.getExtent();
    dispatch(
      ProjectBuildingGeojsonService(
        `${import.meta.env.VITE_API_URL}/projects/${decodedId}/features?task_id=${properties.uid}`,
      ),
    );
    mapRef.current?.scrollIntoView({
      block: 'center',
      behavior: 'smooth',
    });
    setTaskId(properties.uid);
    dispatch(ProjectActions.ToggleTaskModalStatus(true));
    if (windowSize.width < 768) {
      map.getView().fit(extent, {
        padding: [10, 20, 300, 20],
      });
    } else {
      map.getView().fit(extent, {
        padding: [20, 350, 50, 10],
      });
    }
  };

  const buildingStyle = {
    ...defaultStyles,
    lineColor: '#FF0000',
    fillOpacity: '0',
  };

  useEffect(() => {
    if (mobileFooterSelection !== 'explore') {
      setToggleGenerateModal(false);
    }
  }, [mobileFooterSelection]);

  const handlePositionChange = (position) => {
    setCurrentCoordinate({
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    });

    const geojson = {
      type: 'Point',
      coordinates: [position.coords.longitude, position.coords.latitude],
    };
    setPositionGeojson(geojson);
  };

  useEffect(async () => {
    if (geolocationStatus) {
      const checkPermission = await Geolocation.checkPermissions();
      if (checkPermission.location === 'denied') {
        await Geolocation.requestPermissions(['location']);
      }
    }
  }, [geolocationStatus]);

  useEffect(() => {
    if (geolocationStatus) {
      const getCurrentPosition = async () => {
        try {
          const position = await Geolocation.getCurrentPosition();
          handlePositionChange(position);
          // Watch for position changes
          const watchId = Geolocation.watchPosition({ enableHighAccuracy: true }, handlePositionChange);
          // Clean up the watchPosition when the component unmounts
          return () => {
            Geolocation.clearWatch({ id: watchId });
          };
        } catch (error) {
          dispatch(
            CommonActions.SetSnackBar({
              open: true,
              message: `Error getting current position. Please ensure location permissions has been granted.`,
              variant: 'error',
              duration: 2000,
            }),
          );
          dispatch(ProjectActions.ToggleGeolocationStatus(false));

          console.error('Error getting current position:', error);
        }
      };

      getCurrentPosition();
    }
  }, [geolocationStatus]);

  const locationArcStyle = new Style({
    image: new Icon({
      src: locationArc,
    }),
  });

  const startOrientation = async () => {
    const handler = await Motion.addListener('orientation', (event) => {
      var alphaRad = event?.alpha * (Math.PI / 180);
      var betaRad = event?.beta * (Math.PI / 180);
      var gammaRad = event?.gamma * (Math.PI / 180);

      setDeviceRotation(alphaRad + betaRad + gammaRad);
    });
  };

  useEffect(() => {
    // Cleanup when the component unmounts
    if (geolocationStatus) {
      startOrientation();
    }
    return () => {};
  }, [geolocationStatus]);

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

        {/* <ProjectMap /> */}
        {params?.id && (
          <div className="fmtm-relative sm:fmtm-static">
            <MapComponent
              ref={mapRef}
              mapInstance={map}
              className={`map naxatw-relative naxatw-min-h-full naxatw-w-full ${
                windowSize.width <= 640
                  ? 'fmtm-h-[100vh]'
                  : 'fmtm-border-y-[4px] sm:fmtm-border-x-[4px] fmtm-border-primaryRed fmtm-h-[608px]'
              }`}
            >
              <LayerSwitcherControl visible={'outdoors'} />

              {initialFeaturesLayer && initialFeaturesLayer?.features?.length > 0 && (
                <VectorLayer
                  geojson={initialFeaturesLayer}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
                    duration: 2000,
                  }}
                  layerProperties={{ name: 'project-area' }}
                  mapOnClick={projectClickOnMap}
                  zoomToLayer
                  zIndex={5}
                  getTaskStatusStyle={(feature) => getTaskStatusStyle(feature, mapTheme)}
                />
              )}
              {taskBuildingGeojson && taskBuildingGeojson?.features?.length > 0 && (
                <VectorLayer
                  geojson={taskBuildingGeojson}
                  style={buildingStyle}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
                    duration: 2000,
                  }}
                  zoomToLayer
                  zIndex={5}
                />
              )}
              {geolocationStatus && currentCoordinate?.latitude && currentCoordinate?.longitude && (
                <VectorLayer
                  map={map}
                  geojson={positionGeojson}
                  setStyle={locationArcStyle}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
                    duration: 2000,
                  }}
                  zIndex={5}
                  rotation={deviceRotation}
                />
              )}
              <div className="fmtm-top-28 fmtm-left-5">{window.DeviceMotionEvent}</div>
              <div className="fmtm-hidden sm:fmtm-block fmtm-absolute fmtm-bottom-5 fmtm-left-5 fmtm-z-50 fmtm-rounded-lg">
                <Accordion
                  body={<MapLegends defaultTheme={defaultTheme} />}
                  header={
                    <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
                      <AssetModules.LegendToggleIcon className=" fmtm-text-primaryRed" sx={{ fontSize: '30px' }} />
                      <p className="fmtm-text-lg fmtm-font-normal">Legend</p>
                    </div>
                  }
                  onToggle={() => {}}
                  className="fmtm-py-0 !fmtm-pb-0 fmtm-rounded-lg hover:fmtm-bg-gray-50"
                  collapsed={true}
                />
              </div>
              <MapControlComponent map={map} />
            </MapComponent>
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
                  <div className="fmtm-mb-[10vh]">
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
          <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
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
