import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import WindowDimension from '@/hooks/WindowDimension';
import MapDescriptionComponents from '@/components/MapDescriptionComponents';
import ActivitiesPanel from '@/components/ProjectDetailsV2/ActivitiesPanel';
import environment from '@/environment';
import { ProjectById, GetProjectDashboard } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import CustomizedSnackbar from '@/utilities/CustomizedSnackbar';
import OnScroll from '@/hooks/OnScroll';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import FmtmLogo from '@/assets/images/hotLog.png';
import GenerateBasemap from '@/components/GenerateBasemap';
import { ProjectBuildingGeojsonService } from '@/api/SubmissionService';
import TaskSectionPopup from '@/components/ProjectDetailsV2/TaskSectionPopup';
import DialogTaskActions from '@/components/DialogTaskActions';
import QrcodeComponent from '@/components/QrcodeComponent';
import MobileFooter from '@/components/ProjectDetailsV2/MobileFooter';
import MobileActivitiesContents from '@/components/ProjectDetailsV2/MobileActivitiesContents';
import BottomSheet from '@/components/common/BottomSheet';
import MobileProjectInfoContent from '@/components/ProjectDetailsV2/MobileProjectInfoContent';
import { useNavigate } from 'react-router-dom';
import ProjectOptions from '@/components/ProjectDetailsV2/ProjectOptions';
import { MapContainer as MapComponent, useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index';
import MapControlComponent from '@/components/ProjectDetailsV2/MapControlComponent';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { geojsonObjectModel } from '@/constants/geojsonObjectModal';
import { basicGeojsonTemplate } from '@/utilities/mapUtils';
import getTaskStatusStyle from '@/utilfunctions/getTaskStatusStyle';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MapLegends from '@/components/MapLegends';
import Accordion from '@/components/common/Accordion';
import { Geolocation } from '@capacitor/geolocation';
import { Icon, Style } from 'ol/style';
import { Motion } from '@capacitor/motion';
import locationArc from '@/assets/images/locationArc.png';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import ProjectInfo from '@/components/ProjectDetailsV2/ProjectInfo';
import useOutsideClick from '@/hooks/useOutsideClick';

const Home = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();
  const { windowSize, type } = WindowDimension();
  const [divRef, toggle, handleToggle] = useOutsideClick();

  const [taskId, setTaskId] = useState();
  const [mainView, setView] = useState();
  const [featuresLayer, setFeaturesLayer] = useState();
  const [toggleGenerateModal, setToggleGenerateModal] = useState(false);
  const [taskBuildingGeojson, setTaskBuildingGeojson] = useState(null);
  const [initialFeaturesLayer, setInitialFeaturesLayer] = useState(null);
  const [currentCoordinate, setCurrentCoordinate] = useState({ latitude: null, longitude: null });
  const [positionGeojson, setPositionGeojson] = useState(null);
  const [deviceRotation, setDeviceRotation] = useState(0);
  const [viewState, setViewState] = useState('project_info');
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
  const projectDetailsLoading = CoreModules.useAppSelector((state) => state?.project?.projectDetailsLoading);

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
      id: `${feature.id}_${feature.task_status}`,
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

  useEffect(() => {
    dispatch(GetProjectDashboard(`${import.meta.env.VITE_API_URL}/projects/project_dashboard/${decodedId}`));
  }, []);

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
    <div className="fmtm-bg-[#F5F5F5] fmtm-h-[100vh] sm:fmtm-h-[90vh]">
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

      <div className="fmtm-flex fmtm-h-full sm:fmtm-p-6 fmtm-gap-6">
        <div className="fmtm-w-[22rem] fmtm-h-full sm:fmtm-block fmtm-hidden">
          <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-mb-4">
            {projectDetailsLoading ? (
              <div className="fmtm-flex fmtm-gap-1 fmtm-items-center">
                <p className="fmtm-text-[#9B9999]">#</p>
                <CoreModules.Skeleton className="!fmtm-w-[50px] fmtm-h-[20px]" />
              </div>
            ) : (
              <p className="fmtm-text-lg fmtm-font-archivo fmtm-text-[#9B9999]">{`#${state.projectInfo.id}`}</p>
            )}
            <Button
              btnText="MANAGE PROJECT"
              btnType="other"
              className="hover:fmtm-text-red-700 fmtm-border-red-700 !fmtm-rounded-md"
              icon={<AssetModules.SettingsIcon />}
              onClick={() => navigate(`/manage-project/${params?.id}`)}
            />
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
            {projectDetailsLoading ? (
              <CoreModules.Skeleton className="!fmtm-w-[250px] fmtm-h-[25px]" />
            ) : (
              <div className="fmtm-relative">
                <p
                  className="fmtm-text-xl fmtm-font-archivo fmtm-line-clamp-3 fmtm-mr-4"
                  title={state.projectInfo.title}
                >
                  {state.projectInfo.title}
                </p>
              </div>
            )}
            <div className="fmtm-w-full fmtm-h-1 fmtm-bg-white"></div>
            <div className="fmtm-flex fmtm-w-full">
              <button
                className={`fmtm-rounded-none fmtm-border-none fmtm-text-base ${
                  viewState === 'project_info'
                    ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                    : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                } fmtm-py-1`}
                onClick={() => setViewState('project_info')}
              >
                Project Info
              </button>
              <button
                className={`fmtm-rounded-none fmtm-border-none fmtm-text-base ${
                  viewState !== 'project_info'
                    ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                    : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                } fmtm-py-1`}
                onClick={() => setViewState('task_activity')}
              >
                Task Activity
              </button>
            </div>
            {viewState === 'project_info' ? (
              <ProjectInfo />
            ) : (
              <ActivitiesPanel
                params={params}
                state={state.projectTaskBoundries}
                defaultTheme={defaultTheme}
                map={map}
                view={mainView}
                mapDivPostion={y}
                states={state}
              />
            )}
          </div>
          <div className="fmtm-flex fmtm-gap-4">
            <Button
              btnText="VIEW INFOGRAPHICS"
              btnType="other"
              className="hover:fmtm-text-red-700 fmtm-border-red-700 !fmtm-rounded-md fmtm-my-2"
              onClick={() => navigate(`/project-submissions/${encodedId}`)}
            />
            <div className="fmtm-relative" ref={divRef}>
              <div onClick={() => handleToggle()}>
                <Button
                  btnText="DOWNLOAD"
                  btnType="other"
                  className="hover:fmtm-text-red-700 fmtm-border-red-700 !fmtm-rounded-md fmtm-my-2"
                />
              </div>
              <div
                className={`fmtm-flex fmtm-gap-4 fmtm-absolute fmtm-duration-200 fmtm-z-[1000] fmtm-bg-[#F5F5F5] fmtm-p-2 fmtm-rounded-md ${
                  toggle ? 'fmtm-left-0 fmtm-top-0' : '-fmtm-left-[60rem] fmtm-top-0'
                }`}
              >
                <ProjectOptions setToggleGenerateModal={false} />
              </div>
            </div>
          </div>
        </div>
        {params?.id && (
          <div className="fmtm-relative sm:fmtm-static fmtm-flex-grow fmtm-h-full sm:fmtm-rounded-2xl fmtm-overflow-hidden">
            <MapComponent
              ref={mapRef}
              mapInstance={map}
              className={`map naxatw-relative naxatw-min-h-full naxatw-w-full ${
                windowSize.width <= 640 ? 'fmtm-h-[100vh]' : 'fmtm-h-full'
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
      </div>
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
