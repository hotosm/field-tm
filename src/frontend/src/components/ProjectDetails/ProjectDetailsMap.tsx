import React, { useEffect, useState } from 'react';

import { Circle, Fill, Stroke, Style } from 'ol/style';
import MapStyles from '@/hooks/MapStyles';
import { MapContainer as MapComponent, useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/index';
import MapControlComponent from '@/components/ProjectDetails/MapControlComponent';
import AsyncPopup from '../MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';

import CoreModules from '@/shared/CoreModules';
import WindowDimension from '@/hooks/WindowDimension';
import { useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

import { geojsonObjectModel } from '@/constants/geojsonObjectModal';
import getTaskStatusStyle, { getFeatureStatusStyle } from '@/utilfunctions/getTaskStatusStyle';
import Button from '@/components/common/Button';
import { EntityOsmMap } from '@/models/project/projectModel';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { entity_state, GeoGeomTypesEnum } from '@/types/enums';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { GetEntityStatusList, GetOdkEntitiesGeojson, SyncTaskState } from '@/api/Project';
import MapLegends from '@/components/MapLegends';
import isEmpty from '@/utilfunctions/isEmpty';
import AssetModules from '@/shared/AssetModules';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type ProjectDetailsMapProps = {
  setSelectedTaskArea: (feature: any) => void;
  setSelectedTaskFeature: (feature: any) => void;
  setMap: (feature: any) => void;
};

const ProjectDetailsMap = ({ setSelectedTaskArea, setSelectedTaskFeature, setMap }: ProjectDetailsMapProps) => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const { windowSize } = WindowDimension();
  const geojsonStyles = MapStyles();
  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
  });

  const projectId: string | undefined = params.id;

  const [taskBoundariesLayer, setTaskBoundariesLayer] = useState<null | Record<string, any>>(null);
  const [dataExtractExtent, setDataExtractExtent] = useState(null);
  const [overlappingEntityFeatures, setOverlappingEntityFeatures] = useState<Record<string, any>[]>([]);

  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const mapTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const projectTaskBoundaries = useAppSelector((state) => state.project.projectTaskBoundries);
  const entityOsmMap = useAppSelector((state) => state.project.entityOsmMap);
  const customBasemapUrl = useAppSelector((state) => state.project.customBasemapUrl);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const selectedEntityId = useAppSelector((state) => state.project.selectedEntityId);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const entityOsmMapLoading = useAppSelector((state) => state.project.entityOsmMapLoading);
  const syncTaskStateLoading = useAppSelector((state) => state.project.syncTaskStateLoading);
  const newGeomFeatureCollection = useAppSelector((state) => state.project.newGeomFeatureCollection);
  const badGeomFeatureCollection = useAppSelector((state) => state.project.badGeomFeatureCollection);

  useEffect(() => {
    if (!map) return;
    setMap(map);
  }, [map]);

  useEffect(() => {
    if (!map) return;

    const features = projectTaskBoundaries[0]?.taskBoundries?.map((taskObj) => ({
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
  }, [projectTaskBoundaries[0]?.taskBoundries?.length]);

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
      if (projectInfo.primary_geom_type === 'POINT') {
        layer?.setStyle(
          new Style({
            image: new Circle({
              fill: new Fill({
                color: 'rgba(250,17,0,0.4)',
              }),
              stroke: new Stroke({
                color: 'rgba(250,17,0,0.4)',
                width: width * 4,
              }),
              radius: 8,
              declutterMode: 'obstacle',
            }),
            zIndex: 1,
          }),
        );
      } else {
        layer?.setStyle(
          new Style({
            stroke: new Stroke({ color: 'rgb(215,63,62,1)', width: width }),
          }),
        );
      }
    }, 50);

    return () => clearInterval(interval);
    // TODO: replace badGeomFeatureCollection dependency with other
  }, [map, badGeomFeatureCollection]);

  /**
   * Handles the click event on a project task area.
   *
   * @param {Object} properties - Properties attached to task area boundary feature.
   * @param {Object} feature - The clicked task area feature.
   */
  const handleTaskClick = (properties, feature) => {
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
  const handleFeatureClick = (properties, feature) => {
    // Close task area popup, open task feature popup
    dispatch(ProjectActions.SetSelectedEntityId(feature.getProperties()?.entity_id || feature.getProperties()?.osm_id));
    setSelectedTaskFeature(feature);
    dispatch(CoreModules.TaskActions.SetSelectedFeatureProps(properties));
    dispatch(ProjectActions.ToggleTaskModalStatus(true));
  };

  const getEntityStatusList = () => {
    dispatch(GetEntityStatusList(`${VITE_API_URL}/projects/${projectId}/entities/statuses`));
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

  const getOdkEntitiesGeojson = () => {
    dispatch(GetOdkEntitiesGeojson(`${VITE_API_URL}/projects/${projectId}/entities`));
  };

  const syncStatus = () => {
    getEntityStatusList();
    syncTaskState();
    getOdkEntitiesGeojson();
  };

  const LockedPopup = (properties: Record<string, any>) => {
    if (properties.actioned_by_uid === authDetails?.sub) {
      return <p>This task was locked by you</p>;
    }
    return null;
  };

  useEffect(() => {
    if (!map) return;

    const handleClick = (evt) => {
      // always reset selected entity ID on any map click
      dispatch(ProjectActions.SetSelectedEntityId(null));

      // get features from layer excluding 'project-area'(task layer) i.e. get feature from data-extract & new-geoms layer
      const entityFeatures = map.getFeaturesAtPixel(evt.pixel, {
        layerFilter: (layer) => !['bad-entities-point', 'bad-entities', 'project-area'].includes(layer.get('name')),
      });

      // if the clicked point contains entity-related features, handle them; otherwise, check for task features
      if (!isEmpty(entityFeatures)) {
        // store entities in overlappingEntityFeatures to show selection popup if multiple are present at the clicked point
        if (entityFeatures.length > 1) {
          setSelectedTaskArea(undefined);
          setOverlappingEntityFeatures(entityFeatures);
          dispatch(ProjectActions.ToggleTaskModalStatus(false));
        } else {
          if (overlappingEntityFeatures.length > 1) {
            setOverlappingEntityFeatures([]);
          }
          const feature = entityFeatures[0];
          handleFeatureClick(feature.getProperties(), feature);
        }
      } else {
        if (overlappingEntityFeatures.length > 1) {
          setOverlappingEntityFeatures([]);
        }
        const taskFeatures = map.getFeaturesAtPixel(evt.pixel, {
          layerFilter: (layer) => layer.get('name') === 'project-area',
        });
        if (isEmpty(taskFeatures)) return;
        const feature = taskFeatures[0];
        handleTaskClick(feature.getProperties(), feature);
      }
    };

    map.on('click', handleClick);

    return () => {
      map.un('click', handleClick);
    };
  }, [map, overlappingEntityFeatures]);

  return (
    <>
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className={`map naxatw-relative naxatw-min-h-full naxatw-w-full fmtm-cursor-grab active:fmtm-cursor-grabbing ${
          windowSize.width <= 768 ? '!fmtm-h-[100dvh]' : '!fmtm-h-full'
        }`}
      >
        <MapLegends defaultTheme={defaultTheme} />
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
            zoomToLayer
            zIndex={5}
            style=""
            getTaskStatusStyle={(feature) => {
              return getTaskStatusStyle(
                feature,
                mapTheme,
                feature.getProperties()?.actioned_by_uid == authDetails?.sub,
              );
            }}
          />
        )}
        {projectInfo.data_extract_url &&
          isValidUrl(projectInfo.data_extract_url) &&
          dataExtractExtent &&
          selectedTask && (
            <VectorLayer
              fgbUrl={projectInfo.data_extract_url}
              fgbExtent={dataExtractExtent}
              getTaskStatusStyle={(feature) => {
                const geomType = feature.getGeometry().getType();
                const entity = entityOsmMap?.find(
                  (entity) => entity?.osm_id === feature?.getProperties()?.osm_id,
                ) as EntityOsmMap;
                const status = entity_state[entity?.status];
                const isEntitySelected = selectedEntityId === entity?.osm_id;
                return getFeatureStatusStyle(geomType, mapTheme, status, isEntitySelected);
              }}
              viewProperties={{
                size: map?.getSize(),
                padding: [50, 50, 50, 50],
                constrainResolution: true,
                duration: 2000,
              }}
              style=""
              zoomToLayer
              zIndex={5}
            />
          )}
        {(projectInfo.primary_geom_type === GeoGeomTypesEnum.POINT ||
          projectInfo.new_geom_type === GeoGeomTypesEnum.POINT) && (
          <VectorLayer
            geojson={badGeomFeatureCollection}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            layerProperties={{ name: 'bad-entities-point' }}
            zIndex={5}
            style=""
            getTaskStatusStyle={(feature) => {
              const geomType = feature.getGeometry().getType();
              return getFeatureStatusStyle(geomType, mapTheme, 'MARKED_BAD', false);
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
          getTaskStatusStyle={(feature) => {
            const geomType = feature.getGeometry().getType();
            const featureProperty = feature.getProperties();
            const status = entity_state[+featureProperty?.status];
            const isEntitySelected = selectedEntityId ? +selectedEntityId === +featureProperty?.osm_id : false;
            return getFeatureStatusStyle(geomType, mapTheme, status, isEntitySelected);
          }}
        />
        <AsyncPopup
          map={map}
          popupUI={LockedPopup}
          primaryKey={'actioned_by_uid'}
          showOnHover="pointermove"
          popupId="locked-popup"
          className="fmtm-w-[235px]"
        />
        <div className="fmtm-absolute fmtm-bottom-24 md:fmtm-bottom-10 fmtm-left-[50%] fmtm-translate-x-[-50%] fmtm-z-40">
          <Button
            variant="primary-red"
            onClick={syncStatus}
            disabled={entityOsmMapLoading}
            isLoading={entityOsmMapLoading || syncTaskStateLoading}
          >
            Sync Status
          </Button>
        </div>
        <MapControlComponent map={map} projectName={projectInfo?.name || ''} pmTileLayerUrl={customBasemapUrl} />
      </MapComponent>
      {/* show entity selection popup only if multiple features overlap at the clicked point */}
      {overlappingEntityFeatures.length > 1 && (
        <div
          className={`fmtm-z-[10002] fmtm-h-fit fmtm-bg-white fmtm-p-5 fmtm-flex fmtm-flex-col fmtm-bottom-[4.4rem] md:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-fit fmtm-fixed fmtm-rounded-xl fmtm-border-opacity-50`}
        >
          <div title="Close" className="fmtm-ml-auto">
            <AssetModules.CloseIcon
              style={{ width: '20px' }}
              className="hover:fmtm-text-primaryRed fmtm-cursor-pointer"
              onClick={() => {
                setOverlappingEntityFeatures([]);
                dispatch(ProjectActions.SetSelectedEntityId(null));
              }}
            />
          </div>
          {overlappingEntityFeatures?.map((feature, i) => {
            const featureProperties = feature.getProperties();
            const id = featureProperties?.entity_id || featureProperties?.osm_id;
            return (
              <div className="fmtm-py-4 fmtm-border-b">
                <p className="fmtm-font-semibold fmtm-mb-1">
                  {i + 1}. {id}
                </p>
                <Button
                  className="!fmtm-w-full"
                  variant="primary-red"
                  onClick={() => {
                    handleFeatureClick(featureProperties, feature);
                    setOverlappingEntityFeatures([]);
                  }}
                >
                  Select this feature
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
};

export default ProjectDetailsMap;
