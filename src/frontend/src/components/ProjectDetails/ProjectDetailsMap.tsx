import React, { useEffect, useState } from 'react';

import { Stroke, Style } from 'ol/style';
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
import { entity_state } from '@/types/enums';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { GetEntityStatusList, GetGeometryLog, SyncTaskState } from '@/api/Project';
import MapLegends from '@/components/MapLegends';

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

  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const mapTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const projectTaskBoundaries = useAppSelector((state) => state.project.projectTaskBoundries);
  const entityOsmMap = useAppSelector((state) => state.project.entityOsmMap);
  const badGeomFeatureCollection = useAppSelector((state) => state.project.badGeomFeatureCollection);
  const newGeomFeatureCollection = useAppSelector((state) => state.project.newGeomFeatureCollection);
  const customBasemapUrl = useAppSelector((state) => state.project.customBasemapUrl);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const entityOsmMapLoading = useAppSelector((state) => state.project.entityOsmMapLoading);
  const getGeomLogLoading = useAppSelector((state) => state.project.getGeomLogLoading);
  const syncTaskStateLoading = useAppSelector((state) => state.project.syncTaskStateLoading);

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
      layer?.setStyle(
        new Style({
          stroke: new Stroke({ color: 'rgb(215,63,62,1)', width: width }),
        }),
      );
    }, 50);

    return () => clearInterval(interval);
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
    setSelectedTaskFeature(feature);
    dispatch(CoreModules.TaskActions.SetSelectedFeatureProps(properties));
    dispatch(ProjectActions.ToggleTaskModalStatus(true));
  };

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

  const syncStatus = () => {
    getEntityStatusList();
    getGeometryLog();
    syncTaskState();
  };

  const LockedPopup = (properties: Record<string, any>) => {
    if (properties.actioned_by_uid === authDetails?.id) {
      return <p>This task was locked by you</p>;
    }
    return null;
  };

  return (
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
          mapOnClick={handleTaskClick}
          zoomToLayer
          zIndex={5}
          style=""
          getTaskStatusStyle={(feature) => {
            return getTaskStatusStyle(feature, mapTheme, feature.getProperties()?.actioned_by_uid == authDetails?.id);
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
        mapOnClick={handleFeatureClick}
        getTaskStatusStyle={(feature) => {
          const geomType = feature.getGeometry().getType();
          const entity = entityOsmMap?.find(
            (entity) => entity?.id === feature?.getProperties()?.entity_id,
          ) as EntityOsmMap;
          const status = entity_state[entity?.status];
          return getFeatureStatusStyle(geomType, mapTheme, status);
        }}
      />
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
              return getFeatureStatusStyle(geomType, mapTheme, status);
            }}
            viewProperties={{
              size: map?.getSize(),
              padding: [50, 50, 50, 50],
              constrainResolution: true,
              duration: 2000,
            }}
            style=""
            mapOnClick={handleFeatureClick}
            zoomToLayer
            zIndex={5}
          />
        )}
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
          isLoading={entityOsmMapLoading || getGeomLogLoading || syncTaskStateLoading}
        >
          Sync Status
        </Button>
      </div>
      <MapControlComponent map={map} projectName={projectInfo?.name || ''} pmTileLayerUrl={customBasemapUrl} />
    </MapComponent>
  );
};

export default ProjectDetailsMap;
