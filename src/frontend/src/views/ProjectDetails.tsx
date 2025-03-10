import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import { Style, Stroke } from 'ol/style';
import WindowDimension from '@/hooks/WindowDimension';
import ActivitiesPanel from '@/components/ProjectDetails/ActivitiesPanel';
import { ProjectById, GetEntityStatusList, GetGeometryLog, SyncTaskState } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import GenerateBasemap from '@/components/GenerateBasemap';
import TaskSelectionPopup from '@/components/ProjectDetails/TaskSelectionPopup';
import FeatureSelectionPopup from '@/components/ProjectDetails/FeatureSelectionPopup';
import DialogTaskActions from '@/components/DialogTaskActions';
import MobileFooter from '@/components/ProjectDetails/MobileFooter';
import MobileActivitiesContents from '@/components/ProjectDetails/MobileActivitiesContents';
import BottomSheet from '@/components/common/BottomSheet';
import MobileProjectInfoContent from '@/components/ProjectDetails/MobileProjectInfoContent';
import { useNavigate, useParams } from 'react-router-dom';
import ProjectOptions from '@/components/ProjectDetails/ProjectOptions';
import { MapContainer as MapComponent, useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index';
import MapControlComponent from '@/components/ProjectDetails/MapControlComponent';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { geojsonObjectModel } from '@/constants/geojsonObjectModal';
import getTaskStatusStyle, { getFeatureStatusStyle } from '@/utilfunctions/getTaskStatusStyle';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import Button from '@/components/common/Button';
import ProjectInfo from '@/components/ProjectDetails/ProjectInfo';
import useOutsideClick from '@/hooks/useOutsideClick';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import Comments from '@/components/ProjectDetails/Comments';
import { Geolocation } from '@/utilfunctions/Geolocation';
import Instructions from '@/components/ProjectDetails/Instructions';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import MapStyles from '@/hooks/MapStyles';
import { entity_state } from '@/types/enums';
import { EntityOsmMap } from '@/models/project/projectModel';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type tabType = 'project_info' | 'task_activity' | 'comments' | 'instructions';

const tabList: { id: tabType; name: string }[] = [
  { id: 'project_info', name: 'Project Info' },
  { id: 'task_activity', name: 'Task Activity' },
  { id: 'comments', name: 'Comments' },
  { id: 'instructions', name: 'Instructions' },
];

const ProjectDetails = () => {
  useDocumentTitle('Project Details');
  const dispatch = useAppDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const { windowSize } = WindowDimension();
  const [divRef, toggle, handleToggle] = useOutsideClick();

  const geojsonStyles = MapStyles();

  const [selectedTaskArea, setSelectedTaskArea] = useState<Record<string, any> | null>(null);
  const [selectedTaskFeature, setSelectedTaskFeature] = useState();
  const [dataExtractUrl, setDataExtractUrl] = useState<string | undefined>();
  const [dataExtractExtent, setDataExtractExtent] = useState(null);
  const [taskBoundariesLayer, setTaskBoundariesLayer] = useState<null | Record<string, any>>(null);
  const customBasemapUrl = useAppSelector((state) => state.project.customBasemapUrl);
  const [selectedTab, setSelectedTab] = useState<tabType>('project_info');
  const projectId: string | undefined = params.id;
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const state = useAppSelector((state) => state.project);
  const projectInfo = useAppSelector((state) => state.home.selectedProject);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const selectedFeatureProps = useAppSelector((state) => state.task.selectedFeatureProps);
  const mobileFooterSelection = useAppSelector((state) => state.project.mobileFooterSelection);
  const mapTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectDetailsLoading = useAppSelector((state) => state?.project?.projectDetailsLoading);
  const geolocationStatus = useAppSelector((state) => state.project.geolocationStatus);
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const entityOsmMap = useAppSelector((state) => state?.project?.entityOsmMap);
  const entityOsmMapLoading = useAppSelector((state) => state?.project?.entityOsmMapLoading);
  const badGeomFeatureCollection = useAppSelector((state) => state?.project?.badGeomFeatureCollection);
  const newGeomFeatureCollection = useAppSelector((state) => state?.project?.newGeomFeatureCollection);
  const getGeomLogLoading = useAppSelector((state) => state?.project?.getGeomLogLoading);
  const syncTaskStateLoading = useAppSelector((state) => state?.project?.syncTaskStateLoading);

  useEffect(() => {
    if (state.projectInfo.name) {
      document.title = `${state.projectInfo.name} - HOT Field Mapping Tasking Manager`;
    } else {
      document.title = 'HOT Field Mapping Tasking Manager';
    }
  }, [state.projectInfo.name]);

  //Fetch project for the first time
  useEffect(() => {
    if (!projectId) return;

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
    setSelectedTaskFeature(feature);
    dispatch(CoreModules.TaskActions.SetSelectedFeatureProps(properties));
    dispatch(ProjectActions.ToggleTaskModalStatus(true));
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
      setSelectedTab('task_activity');
    } else {
      setSelectedTab('project_info');
    }
  }, [taskModalStatus]);

  const getEntityStatusList = () => {
    dispatch(GetEntityStatusList(`${VITE_API_URL}/projects/${projectId}/entities/statuses`));
  };

  const getGeometryLog = () => {
    dispatch(GetGeometryLog(`${VITE_API_URL}/projects/${projectId}/geometry/records`));
  };

  const syncTaskState = () => {
    const taskBoundaryLayer = map
      .getLayers()
      .getArray()
      .find((layer: any) => layer.get('name') == 'project-area');
    const taskBoundaryFeatures = taskBoundaryLayer.getSource().getFeatures();

    projectId &&
      dispatch(SyncTaskState(`${VITE_API_URL}/tasks`, { project_id: projectId }, taskBoundaryFeatures, geojsonStyles));
  };

  useEffect(() => {
    getEntityStatusList();
    getGeometryLog();
  }, []);

  // pulse rejected entity feature stroke effect
  useEffect(() => {
    if (!map) return;
    let layer;
    let width = 1;
    let expanding = true;

    const interval = setInterval(() => {
      const allLayers = map?.getAllLayers();
      // layer representing bad entities
      layer = allLayers?.find((layer) => layer.getProperties().name === 'bad-entities');
      if (!layer) return;

      if (expanding) {
        width += 0.3;
        if (width >= 6) expanding = false;
      } else {
        width -= 0.3;
        if (width <= 1) expanding = true;
      }

      // apply style to the layer
      layer?.setStyle(
        new Style({
          stroke: new Stroke({ color: 'rgb(215,63,62,1)', width: width }),
        }),
      );
    }, 50);

    return () => clearInterval(interval);
  }, [map, badGeomFeatureCollection]);

  const syncStatus = () => {
    getEntityStatusList();
    getGeometryLog();
    syncTaskState();
  };

  const getTabContent = (tabState: tabType) => {
    switch (tabState) {
      case 'project_info':
        return <ProjectInfo />;
      case 'task_activity':
        return (
          <ActivitiesPanel params={params} state={state.projectTaskBoundries} defaultTheme={defaultTheme} map={map} />
        );
      case 'comments':
        return <Comments />;
      case 'instructions':
        return <Instructions instructions={state?.projectInfo?.instructions} />;
      default:
        return <></>;
    }
  };

  const getMobileBottomSheetContent = (
    mobileTabState: '' | 'projectInfo' | 'activities' | 'comment' | 'instructions',
  ) => {
    switch (mobileTabState) {
      case 'projectInfo':
        return <MobileProjectInfoContent projectInfo={state.projectInfo} />;
      case 'activities':
        return <MobileActivitiesContents map={map} />;
      case 'instructions':
        return (
          <div className="fmtm-mb-[10vh]">
            <Instructions instructions={state?.projectInfo?.instructions} />
          </div>
        );
      case 'comment':
        return (
          <div className="fmtm-mb-[10vh]">
            <Comments />
          </div>
        );
      default:
        return <></>;
    }
  };

  return (
    <div className="fmtm-bg-[#f5f5f5] !fmtm-h-[100dvh] sm:!fmtm-h-full">
      {/* Customized Modal For Generate Tiles */}
      <GenerateBasemap projectInfo={state.projectInfo} />

      <div className="fmtm-flex fmtm-h-full fmtm-gap-6">
        <div className="fmtm-w-[22rem] fmtm-h-full fmtm-hidden md:fmtm-block">
          <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-mb-4">
            {projectDetailsLoading ? (
              <div className="fmtm-flex fmtm-gap-1 fmtm-items-center">
                <p className="fmtm-text-[#9B9999]">#</p>
                <CoreModules.Skeleton className="!fmtm-w-[50px] fmtm-h-[20px]" />
              </div>
            ) : (
              <p className="fmtm-text-lg fmtm-font-archivo fmtm-text-[#9B9999]">{`#${state.projectInfo.id}`}</p>
            )}
            <Button variant="secondary-red" onClick={() => navigate(`/manage/project/${params?.id}`)}>
              MANAGE PROJECT <AssetModules.SettingsIcon />
            </Button>
          </div>
          <div
            className="fmtm-flex fmtm-flex-col fmtm-gap-4 fmtm-flex-auto"
            style={{ height: `${selectedTab === 'comments' ? 'calc(100% - 63px)' : 'calc(100% - 103px)'}` }}
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
              {tabList.map((tab) => (
                <button
                  key={tab.id}
                  className={`fmtm-rounded-none fmtm-border-none fmtm-text-base fmtm-py-1 ${
                    selectedTab === tab.id
                      ? 'fmtm-bg-primaryRed fmtm-text-white hover:fmtm-bg-red-700'
                      : 'fmtm-bg-white fmtm-text-[#706E6E] hover:fmtm-bg-grey-50'
                  } ${(taskModalStatus && tab.id === 'project_info') || (!taskModalStatus && (tab.id === 'task_activity' || tab.id === 'comments')) ? 'fmtm-hidden' : ''}`}
                  onClick={() => setSelectedTab(tab.id)}
                >
                  {tab.name}
                </button>
              ))}
            </div>
            {getTabContent(selectedTab)}
          </div>
          {selectedTab !== 'comments' && (
            <div className="fmtm-flex fmtm-gap-4">
              <Button
                variant="secondary-red"
                className="!fmtm-w-1/2"
                onClick={() => navigate(`/project-submissions/${projectId}`)}
              >
                VIEW INFOGRAPHICS
              </Button>
              <div className="fmtm-relative fmtm-w-1/2" ref={divRef}>
                <Button variant="secondary-red" className="fmtm-w-full" onClick={handleToggle}>
                  DOWNLOAD
                </Button>
                <div
                  className={`fmtm-flex fmtm-gap-4 fmtm-absolute fmtm-duration-200 fmtm-z-[1000] fmtm-bg-[#F5F5F5] fmtm-px-2 fmtm-py-[2px] fmtm-rounded ${
                    toggle
                      ? 'fmtm-left-0 fmtm-bottom-0 lg:fmtm-top-0'
                      : '-fmtm-left-[65rem] fmtm-bottom-0 lg:fmtm-top-0'
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
                windowSize.width <= 768 ? '!fmtm-h-[100dvh]' : '!fmtm-h-full'
              }`}
            >
              <LayerSwitcherControl visible={customBasemapUrl ? 'custom' : 'osm'} pmTileLayerUrl={customBasemapUrl} />

              {taskBoundariesLayer && taskBoundariesLayer?.features?.length > 0 && (
                <VectorLayer
                  geojson={taskBoundariesLayer}
                  viewProperties={{
                    size: map?.getSize(),
                    padding: [50, 50, 50, 50],
                    constrainResolution: true,
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
              <VectorLayer
                geojson={badGeomFeatureCollection}
                viewProperties={{
                  size: map?.getSize(),
                  padding: [50, 50, 50, 50],
                  constrainResolution: true,
                  duration: 2000,
                }}
                layerProperties={{ name: 'bad-entities' }}
                zIndex={5}
                style=""
              />
              <VectorLayer
                geojson={newGeomFeatureCollection}
                viewProperties={{
                  size: map?.getSize(),
                  padding: [50, 50, 50, 50],
                  constrainResolution: true,
                  duration: 2000,
                }}
                layerProperties={{ name: 'new-entities' }}
                zIndex={5}
                style=""
                mapOnClick={projectClickOnTaskFeature}
                getTaskStatusStyle={(feature) => {
                  const geomType = feature.getGeometry().getType();
                  const entity = entityOsmMap?.find(
                    (entity) => entity?.id === feature?.getProperties()?.entity_id,
                  ) as EntityOsmMap;
                  const status = entity_state[entity?.status];
                  return getFeatureStatusStyle(geomType, mapTheme, status);
                }}
              />
              {dataExtractUrl && isValidUrl(dataExtractUrl) && dataExtractExtent && selectedTask && (
                <VectorLayer
                  fgbUrl={dataExtractUrl}
                  fgbExtent={dataExtractExtent}
                  getTaskStatusStyle={(feature) => {
                    const geomType = feature.getGeometry().getType();
                    const entity = entityOsmMap?.find(
                      (entity) => entity?.osm_id === feature?.getProperties()?.osm_id,
                    ) as EntityOsmMap;
                    const status = entity_state[entity?.status];
                    return getFeatureStatusStyle(geomType, mapTheme, status);
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
              <div className="fmtm-absolute fmtm-bottom-20 md:fmtm-bottom-3 fmtm-left-3 fmtm-z-50">
                <Button
                  variant="secondary-red"
                  onClick={() => dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(true))}
                >
                  BASEMAPS
                  <AssetModules.BoltIcon className="!fmtm-text-xl" />
                </Button>
              </div>
              <div className="fmtm-absolute fmtm-bottom-20 md:fmtm-bottom-3 fmtm-right-3 fmtm-z-50">
                <Button variant="secondary-red" onClick={syncStatus} disabled={entityOsmMapLoading}>
                  SYNC STATUS
                  <AssetModules.SyncIcon
                    className={`!fmtm-text-xl ${(entityOsmMapLoading || getGeomLogLoading || syncTaskStateLoading) && 'fmtm-animate-spin'}`}
                  />
                </Button>
              </div>
              <MapControlComponent
                map={map}
                projectName={state?.projectInfo?.name || ''}
                pmTileLayerUrl={customBasemapUrl}
              />
            </MapComponent>
            <div
              className="fmtm-absolute fmtm-top-4 fmtm-left-4 fmtm-bg-white fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-red-50 fmtm-duration-300 fmtm-border-[1px] md:fmtm-hidden fmtm-cursor-pointer"
              onClick={() => navigate('/')}
            >
              <AssetModules.ArrowBackIcon className="fmtm-text-grey-800" />
            </div>
            {['projectInfo', 'activities', 'instructions', 'comment'].includes(mobileFooterSelection) && (
              <BottomSheet
                body={getMobileBottomSheetContent(mobileFooterSelection)}
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
        <FeatureSelectionPopup featureProperties={selectedFeatureProps} taskId={selectedTask} />
      )}
    </div>
  );
};

export default ProjectDetails;
