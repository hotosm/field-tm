import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import WindowDimension from '@/hooks/WindowDimension';
import ActivitiesPanel from '@/components/ProjectDetailsV2/ActivitiesPanel';
import { ProjectById, GetEntityInfo } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import CustomizedSnackbar from '@/utilities/CustomizedSnackbar';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import GenerateBasemap from '@/components/GenerateBasemap';
import TaskSelectionPopup from '@/components/ProjectDetailsV2/TaskSelectionPopup';
import FeatureSelectionPopup from '@/components/ProjectDetailsV2/FeatureSelectionPopup';
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
import getTaskStatusStyle, { getFeatureStatusStyle } from '@/utilfunctions/getTaskStatusStyle';
import MapLegends from '@/components/MapLegends';
import Accordion from '@/components/common/Accordion';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import Button from '@/components/common/Button';
import ProjectInfo from '@/components/ProjectDetailsV2/ProjectInfo';
import useOutsideClick from '@/hooks/useOutsideClick';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { useAppSelector } from '@/types/reduxTypes';
import Comments from '@/components/ProjectDetailsV2/Comments';
import { Geolocation } from '@/utilfunctions/Geolocation';
import Instructions from '@/components/ProjectDetailsV2/Instructions';
import { readFileFromOPFS } from '@/api/Files';
import DebugConsole from '@/utilities/DebugConsole';
import { CustomCheckbox } from '@/components/common/Checkbox';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import QrcodeComponent from '@/components/QrcodeComponent';
import { createDropdownMenuScope } from '@radix-ui/react-dropdown-menu';

const ProjectDetailsV2 = () => {
  useDocumentTitle('Project Details');
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();
  const { windowSize } = WindowDimension();
  const [divRef, toggle, handleToggle] = useOutsideClick();
  const [legendRef, legendToggle, handleLegendToggle] = useOutsideClick();

  const [mainView, setView] = useState<any>();
  const [selectedTaskArea, setSelectedTaskArea] = useState<Record<string, any> | null>(null);
  const [selectedTaskFeature, setSelectedTaskFeature] = useState();
  const [dataExtractUrl, setDataExtractUrl] = useState<string | undefined>();
  const [dataExtractExtent, setDataExtractExtent] = useState(null);
  const [taskBoundariesLayer, setTaskBoundariesLayer] = useState<null | Record<string, any>>(null);
  // Can pass a File object, or a string URL to be read by PMTiles
  const [customBasemapData, setCustomBasemapData] = useState<File | string | null>();
  const [viewState, setViewState] = useState('project_info');
  const projectId: string = params.id;
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const state = useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.home.selectedProject);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const selectedFeatureProps = useAppSelector((state) => state.task.selectedFeatureProps);
  const stateSnackBar = useAppSelector((state) => state.home.snackbar);
  const mobileFooterSelection = useAppSelector((state) => state.project.mobileFooterSelection);
  const mapTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const geolocationStatus = useAppSelector((state) => state.project.geolocationStatus);
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);
  const projectOpfsBasemapPath = useAppSelector((state) => state?.project?.projectOpfsBasemapPath);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const entityOsmMap = useAppSelector((state) => state?.project?.entityOsmMap);

  useEffect(() => {
    if (state.projectInfo.name) {
      document.title = `${state.projectInfo.name} - HOT Field Mapping Tasking Manager`;
    } else {
      document.title = 'HOT Field Mapping Tasking Manager';
    }
  }, [state.projectInfo.name]);

  //snackbar handle close function
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
    if (state.projectTaskBoundries.findIndex((project) => project.id.toString() === projectId) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    }
    if (Object.keys(state.projectInfo)?.length == 0) {
      dispatch(ProjectActions.SetProjectInfo(projectInfo));
    } else {
      if (state.projectInfo.id?.toString() != projectId) {
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
    Geolocation(map, geolocationStatus, dispatch);
  }, [geolocationStatus]);

  useEffect(() => {
    if (!map) return;

    // FIXME should the feature id be an int, not a string?
    const features = state.projectTaskBoundries[0]?.taskBoundries?.map((taskObj) => ({
      type: 'Feature',
      id: taskObj.id,
      geometry: { ...taskObj.outline },
      properties: {
        ...taskObj.outline.properties,
        task_state: taskObj?.task_state,
        actioned_by_uid: taskObj?.actioned_by_uid,
        actioned_by_username: taskObj?.actioned_by_username,
      },
    }));

    const taskBoundariesFeatcol = {
      ...geojsonObjectModel,
      features: features,
    };
    setTaskBoundariesLayer(taskBoundariesFeatcol);
  }, [state.projectTaskBoundries[0]?.taskBoundries?.length]);

  /**
   * Sets the data extract URL when the data extract URL in the state changes.
   */
  useEffect(() => {
    setDataExtractUrl(state.projectInfo.data_extract_url);
  }, [state.projectInfo.data_extract_url]);

  const lockedPopup = (properties: Record<string, any>) => {
    if (properties.actioned_by_uid === authDetails?.id) {
      return <p>This task was locked by you</p>;
    }
    return null;
  };

  /**
   * Handles the click event on a project task area.
   *
   * @param {Object} properties - Properties attached to task area boundary feature.
   * @param {Object} feature - The clicked task area feature.
   */
  const projectClickOnTaskArea = (properties, feature) => {
    // Close task feature popup, open task area popup
    setSelectedTaskFeature(undefined);
    setSelectedTaskArea(feature);

    let extent = properties.geometry.getExtent();
    setDataExtractExtent(properties.geometry);

    mapRef.current?.scrollIntoView({
      block: 'center',
      behavior: 'smooth',
    });

    dispatch(CoreModules.TaskActions.SetSelectedTask(feature.getId()));
    dispatch(ProjectActions.ToggleTaskModalStatus(true));

    // Fit the map view to the clicked feature's extent based on the window size
    if (windowSize.width < 768 && map.getView().getZoom() < 17) {
      map.getView().fit(extent, {
        padding: [10, 20, 300, 20],
      });
    } else if (windowSize.width > 768 && map.getView().getZoom() < 17) {
      map.getView().fit(extent, {
        padding: [20, 350, 50, 10],
      });
    }
  };

  /**
   * Handles the click event on a task feature (geometry).
   *
   * @param {Object} properties - Properties attached to map feature.
   * @param {Object} feature - The clicked feature.
   */
  const projectClickOnTaskFeature = (properties, feature) => {
    // Close task area popup, open task feature popup
    // setSelectedTaskArea(undefined);
    setSelectedTaskFeature(feature);

    dispatch(CoreModules.TaskActions.SetSelectedFeatureProps(properties));

    // let extent = properties.geometry.getExtent();
    // setDataExtractExtent(properties.geometry);

    // mapRef.current?.scrollIntoView({
    //   block: 'center',
    //   behavior: 'smooth',
    // });

    dispatch(ProjectActions.ToggleTaskModalStatus(true));

    // // Fit the map view to the clicked feature's extent based on the window size
    // if (windowSize.width < 768 && map.getView().getZoom() < 17) {
    //   map.getView().fit(extent, {
    //     padding: [10, 20, 300, 20],
    //   });
    // } else if (windowSize.width > 768 && map.getView().getZoom() < 17) {
    //   map.getView().fit(extent, {
    //     padding: [20, 350, 50, 10],
    //   });
    // }
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
      setViewState('task_activity');
    } else {
      setViewState('project_info');
    }
  }, [taskModalStatus]);

  useEffect(() => {
    dispatch(GetEntityInfo(`${import.meta.env.VITE_API_URL}/projects/${projectId}/entities/statuses`));
  }, []);

  const getPmtilesBasemap = async () => {
    if (!projectOpfsBasemapPath) {
      return;
    }
    const opfsPmtilesData = await readFileFromOPFS(projectOpfsBasemapPath);
    setCustomBasemapData(opfsPmtilesData);
  };
  useEffect(() => {
    if (!projectOpfsBasemapPath) {
      return;
    }

    // Extract project id from projectOpfsBasemapPath
    const projectOpfsBasemapPathParts = projectOpfsBasemapPath.split('/');
    const projectOpfsBasemapProjectId = projectOpfsBasemapPathParts[0];

    // Check if project id from projectOpfsBasemapPath matches current projectId
    if (projectOpfsBasemapProjectId !== projectId) {
      // If they don't match, set CustomBasemapData to null
      setCustomBasemapData(null);
    } else {
      // If they match, fetch the basemap data
      getPmtilesBasemap();
    }
    return () => {};
  }, [projectOpfsBasemapPath]);
  const [showDebugConsole, setShowDebugConsole] = useState(false);

  return (
    <div className="fmtm-bg-[#f5f5f5] !fmtm-h-[100dvh] sm:!fmtm-h-full">
      {/* only used to display debug console */}

      <DebugConsole showDebugConsole={showDebugConsole} setShowDebugConsole={setShowDebugConsole} />
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

      <div className="fmtm-flex fmtm-h-full fmtm-gap-6">
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
            style={{ height: `${viewState === 'comments' ? 'calc(100% - 63px)' : 'calc(100% - 103px)'}` }}
          >
            {projectDetailsLoading ? (
              <CoreModules.Skeleton className="!fmtm-w-[250px] fmtm-h-[25px]" />
            ) : (
              <div className="fmtm-relative">
                <p
                  className="fmtm-text-xl fmtm-font-archivo fmtm-line-clamp-3 fmtm-mr-4"
                  title={state.projectInfo.name}
                >
                  {state.projectInfo.name}
                </p>
              </div>
            )}
            <div className="fmtm-w-full fmtm-h-1 fmtm-bg-white"></div>
            <div className="fmtm-flex fmtm-w-full">
              {!taskModalStatus && (
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
              )}
              {taskModalStatus && (
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
              )}
              {taskModalStatus && (
                <button
                  className={`fmtm-rounded-none fmtm-border-none fmtm-text-base ${
                    viewState === 'comments'
                      ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                      : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                  } fmtm-py-1`}
                  onClick={() => setViewState('comments')}
                >
                  Comments
                </button>
              )}
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
                onClick={() => navigate(`/project-submissions/${projectId}`)}
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
                    toggle
                      ? 'fmtm-left-0 fmtm-bottom-0 lg:fmtm-top-0'
                      : '-fmtm-left-[60rem] fmtm-bottom-0 lg:fmtm-top-0'
                  }`}
                >
                  <ProjectOptions projectName={state?.projectInfo?.name} />
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
                windowSize.width <= 640 ? '!fmtm-h-[100dvh]' : '!fmtm-h-full'
              }`}
            >
              {import.meta.env.MODE === 'development' && (
                <div className="fmtm-block sm:fmtm-hidden fmtm-absolute fmtm-top-6 fmtm-left-16 fmtm-z-50">
                  <CustomCheckbox
                    label="Toggle-Console"
                    checked={showDebugConsole}
                    onCheckedChange={(status) => {
                      setShowDebugConsole(status);
                    }}
                    className="fmtm-text-black !fmtm-w-full"
                  />
                </div>
              )}
              <LayerSwitcherControl
                visible={customBasemapData ? 'custom' : 'osm'}
                pmTileLayerData={customBasemapData}
              />

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
                  mapOnClick={projectClickOnTaskArea}
                  zoomToLayer
                  zIndex={5}
                  style=""
                  getTaskStatusStyle={(feature) => {
                    return getTaskStatusStyle(
                      feature,
                      mapTheme,
                      feature.getProperties()?.actioned_by_uid == authDetails?.id,
                    );
                  }}
                />
              )}
              {dataExtractUrl && isValidUrl(dataExtractUrl) && dataExtractExtent && (
                <VectorLayer
                  fgbUrl={dataExtractUrl}
                  fgbExtent={dataExtractExtent}
                  getTaskStatusStyle={(feature) => {
                    return getFeatureStatusStyle(feature?.getProperties()?.osm_id, mapTheme, entityOsmMap);
                  }}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
                    duration: 2000,
                  }}
                  style=""
                  mapOnClick={projectClickOnTaskFeature}
                  zoomToLayer
                  zIndex={5}
                />
              )}
              <AsyncPopup
                map={map}
                popupUI={lockedPopup}
                primaryKey={'actioned_by_uid'}
                showOnHover="pointermove"
                popupId="locked-popup"
                className="fmtm-w-[235px]"
              />
              <div className="fmtm-absolute fmtm-bottom-20 sm:fmtm-bottom-3 fmtm-left-3 fmtm-z-50 fmtm-rounded-lg">
                <Accordion
                  ref={legendRef}
                  body={<MapLegends defaultTheme={defaultTheme} />}
                  header={
                    <div className="fmtm-flex fmtm-items-center fmtm-gap-1 sm:fmtm-gap-2">
                      <p className="fmtm-text-base fmtm-font-normal">LEGEND</p>
                    </div>
                  }
                  onToggle={() => {
                    handleLegendToggle();
                  }}
                  className="fmtm-py-0 !fmtm-pb-0 fmtm-rounded-lg hover:fmtm-bg-gray-50"
                  collapsed={!legendToggle}
                />
              </div>
              <div className="fmtm-absolute fmtm-bottom-20 sm:fmtm-bottom-5 fmtm-right-3 fmtm-z-50 fmtm-h-fit">
                <Button
                  btnText="Basemaps"
                  icon={<AssetModules.BoltIcon />}
                  onClick={() => {
                    dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(true));
                  }}
                  btnType="primary"
                  className="!fmtm-text-base !fmtm-pr-2"
                />
              </div>
              <div className="fmtm-absolute fmtm-right-0 fmtm-top-0 fmtm-z-50 fmtm-hidden sm:fmtm-block">
                <QrcodeComponent />
              </div>
              <MapControlComponent
                map={map}
                projectName={state?.projectInfo?.name || ''}
                pmTileLayerData={customBasemapData}
              />
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
                body={<MobileActivitiesContents map={map} />}
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'instructions' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[10vh]">
                    <Instructions instructions={state?.projectInfo?.instructions} />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            {mobileFooterSelection === 'comment' && (
              <BottomSheet
                body={
                  <div className="fmtm-mb-[10vh]">
                    <Comments />
                  </div>
                }
                onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
              />
            )}
            <MobileFooter />
          </div>
        )}
      </div>
      {selectedTaskArea != undefined && selectedTaskFeature === undefined && selectedTask && (
        <TaskSelectionPopup
          taskId={selectedTask}
          feature={selectedTaskArea}
          body={
            <div>
              <DialogTaskActions feature={selectedTaskArea} taskId={selectedTask} />
            </div>
          }
        />
      )}
      {selectedTaskFeature != undefined && selectedTask && selectedTaskArea && (
        <FeatureSelectionPopup
          featureProperties={selectedFeatureProps}
          taskId={selectedTask}
          taskFeature={selectedTaskArea}
        />
      )}
    </div>
  );
};

export default ProjectDetailsV2;
