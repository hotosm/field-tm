import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import WindowDimension from '@/hooks/WindowDimension';
// import MapDescriptionComponents from '@/components/MapDescriptionComponents';
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
import TaskSectionPopup from '@/components/ProjectDetailsV2/TaskSectionPopup';
import DialogTaskActions from '@/components/DialogTaskActions';
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
import getTaskStatusStyle from '@/utilfunctions/getTaskStatusStyle';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import MapLegends from '@/components/MapLegends';
import Accordion from '@/components/common/Accordion';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import Button from '@/components/common/Button';
import ProjectInfo from '@/components/ProjectDetailsV2/ProjectInfo';
import useOutsideClick from '@/hooks/useOutsideClick';
import { dataExtractPropertyType } from '@/models/project/projectModel';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { useAppSelector } from '@/types/reduxTypes';
import Comments from '@/components/ProjectDetailsV2/Comments';
import { Geolocation } from '@/utilfunctions/Geolocation';
import Instructions from '@/components/ProjectDetailsV2/Instructions';

const Home = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();
  const { windowSize, type } = WindowDimension();
  const [divRef, toggle, handleToggle] = useOutsideClick();

  const [mainView, setView] = useState<any>();
  const [featuresLayer, setFeaturesLayer] = useState();
  const [dataExtractUrl, setDataExtractUrl] = useState(null);
  const [dataExtractExtent, setDataExtractExtent] = useState(null);
  const [taskBoundariesLayer, setTaskBoundariesLayer] = useState<null | Record<string, any>>(null);

  const [viewState, setViewState] = useState('project_info');
  const encodedId: string = params.id;
  const decodedId = environment.decode(encodedId);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const state = CoreModules.useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.home.selectedProject);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const stateSnackBar = useAppSelector((state) => state.home.snackbar);
  const mobileFooterSelection = useAppSelector((state) => state.project.mobileFooterSelection);
  const mapTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);

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
    return () => {};
  }, [params.id]);

  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
  });

  useEffect(() => {
    if (!map) return;
    Geolocation(map);
  }, [map]);

  const { y } = OnScroll(map, windowSize.width);

  useEffect(() => {
    if (!map) return;

    const features = state.projectTaskBoundries[0]?.taskBoundries?.map((taskObj) => ({
      type: 'Feature',
      geometry: { ...taskObj.outline_geojson.geometry },
      properties: {
        ...taskObj.outline_geojson.properties,
        centroid: taskObj.outline_centroid.geometry.coordinates,
        // TODO add bbox field here too?
      },
      id: `${taskObj.id}_${taskObj.task_status}`,
    }));

    const taskBoundariesFeatcol = {
      ...geojsonObjectModel,
      features: features,
    };
    setTaskBoundariesLayer(taskBoundariesFeatcol);
  }, [state.projectTaskBoundries[0]?.taskBoundries?.length]);

  const dataExtractDataPopup = (properties: dataExtractPropertyType) => {
    return (
      <div className="fmtm-h-fit">
        <h2 className="fmtm-border-b-[2px] fmtm-border-primaryRed fmtm-w-fit fmtm-pr-1">
          OSM ID: #{properties?.osm_id}
        </h2>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
          <p>
            Tags: <span className="fmtm-text-primaryRed">{properties?.tags}</span>
          </p>
          <p>
            Timestamp: <span className="fmtm-text-primaryRed">{properties?.timestamp}</span>
          </p>
          <p>
            Changeset: <span className="fmtm-text-primaryRed">{properties?.changeset}</span>
          </p>
          <p>
            Version: <span className="fmtm-text-primaryRed">{properties?.version}</span>
          </p>
        </div>
      </div>
    );
  };
  const projectClickOnMapTask = (properties, feature) => {
    setFeaturesLayer(feature);
    let extent = properties.geometry.getExtent();

    setDataExtractExtent(properties.geometry);
    setDataExtractUrl(state.projectInfo.data_extract_url);

    mapRef.current?.scrollIntoView({
      block: 'center',
      behavior: 'smooth',
    });

    dispatch(CoreModules.TaskActions.SetSelectedTask(properties.uid));

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
    if (mobileFooterSelection !== '') {
      dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(false));
    }
  }, [mobileFooterSelection]);

  useEffect(() => {
    if (taskModalStatus) {
      dispatch(ProjectActions.ToggleTaskModalStatus(false));
    }
  }, []);

  useEffect(() => {
    if (taskModalStatus) {
      setViewState('comments');
    } else {
      setViewState('project_info');
    }
  }, [taskModalStatus]);

  useEffect(() => {
    dispatch(GetProjectDashboard(`${import.meta.env.VITE_API_URL}/projects/project_dashboard/${decodedId}`));
  }, []);

  return (
    <div className="fmtm-bg-[#f5f5f5]" style={{ height: '100%' }}>
      {/* Customized Modal For Generate Tiles */}
      <div>
        <GenerateBasemap projectInfo={state.projectInfo} />
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
          <div
            className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-flex-auto"
            style={{ height: `${viewState === 'comments' ? 'calc(100% - 50px)' : 'calc(100% - 95px)'}` }}
          >
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
                  viewState === 'project_info' || viewState === 'comments'
                    ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                    : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                } fmtm-py-1`}
                onClick={() => {
                  taskModalStatus ? setViewState('comments') : setViewState('project_info');
                }}
              >
                {taskModalStatus ? 'Comments' : 'Project Info'}
              </button>
              <button
                className={`fmtm-rounded-none fmtm-border-none fmtm-text-base ${
                  viewState === 'task_activity'
                    ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                    : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                } fmtm-py-1`}
                onClick={() => setViewState('task_activity')}
              >
                Task Activity
              </button>
              <button
                className={`fmtm-rounded-none fmtm-border-none fmtm-text-base ${
                  viewState === 'instructions'
                    ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                    : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                } fmtm-py-1`}
                onClick={() => setViewState('instructions')}
              >
                Instructions
              </button>
            </div>
            {viewState === 'project_info' ? (
              <ProjectInfo />
            ) : viewState === 'comments' ? (
              <Comments />
            ) : viewState === 'task_activity' ? (
              <ActivitiesPanel
                params={params}
                state={state.projectTaskBoundries}
                defaultTheme={defaultTheme}
                map={map}
                view={mainView}
                mapDivPostion={y}
                states={state}
              />
            ) : (
              <Instructions instructions={state?.projectInfo?.instructions} />
            )}
          </div>
          {viewState !== 'comments' && (
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
                  <ProjectOptions />
                </div>
              </div>
            </div>
          )}
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

              {taskBoundariesLayer && taskBoundariesLayer?.features?.length > 0 && (
                <VectorLayer
                  geojson={taskBoundariesLayer}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
                    duration: 2000,
                  }}
                  layerProperties={{ name: 'project-area' }}
                  mapOnClick={projectClickOnMapTask}
                  zoomToLayer
                  zIndex={5}
                  getTaskStatusStyle={(feature) => getTaskStatusStyle(feature, mapTheme)}
                />
              )}
              {dataExtractUrl && isValidUrl(dataExtractUrl) && (
                <VectorLayer
                  fgbUrl={dataExtractUrl}
                  fgbExtent={dataExtractExtent}
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
              <AsyncPopup map={map} popupUI={dataExtractDataPopup} primaryKey={'osm_id'} />
              <div className="fmtm-top-28 fmtm-left-5">{window.DeviceMotionEvent}</div>
              <div className="fmtm-absolute fmtm-bottom-36 sm:fmtm-bottom-5 fmtm-left-5 fmtm-z-50 fmtm-rounded-lg">
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
              <div className="fmtm-absolute fmtm-top-3 fmtm-right-3 fmtm-z-50">
                <Button
                  btnText="GENERATE MBTILES"
                  icon={<AssetModules.BoltIcon />}
                  onClick={() => {
                    dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(true));
                  }}
                  btnType="primary"
                  className="!fmtm-text-base !fmtm-pr-2"
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
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'activities' && (
              <BottomSheet
                body={<MobileActivitiesContents map={map} view={mainView} mapDivPostion={y} />}
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'instructions' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[12vh]">
                    <Instructions instructions={state?.projectInfo?.instructions} />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'comment' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[12vh]">
                    <Comments />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'others' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[10vh]">
                    <ProjectOptions />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}

            <MobileFooter />
          </div>
        )}
      </div>
      {featuresLayer != undefined && (
        <TaskSectionPopup
          taskId={selectedTask}
          feature={featuresLayer}
          body={
            <div>
              <DialogTaskActions map={map} view={mainView} feature={featuresLayer} taskId={selectedTask} />
            </div>
          }
        />
      )}
    </div>
  );
};

export default Home;
