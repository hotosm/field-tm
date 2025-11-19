import React, { useCallback, useState, useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import { MapContainer as MapComponent } from '@/components/MapComponent/OpenLayersComponent';
import { useOLMap } from '@/components/MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher';
import { VectorLayer } from '@/components/MapComponent/OpenLayersComponent/Layers';
import { Vector as VectorSource } from 'ol/source';
import GeoJSON from 'ol/format/GeoJSON';
import { get } from 'ol/proj';
import { getStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';
import TaskSubmissionsMapLegend from '@/components/ProjectSubmissions/Infographics/TaskSubmissionsMapLegend';
import Accordion from '@/components/common/Accordion';
import AsyncPopup from '@/components/MapComponent/OpenLayersComponent/AsyncPopup/AsyncPopup';
import {
  colorCodesType,
  taskWiseSubmissionCount,
  legendColorArrayType,
  taskBoundariesType,
  taskFeaturePropertyType,
} from '@/models/task/taskModel';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { projectInfoType, projectTaskBoundriesType } from '@/models/project/projectModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import LayerSwitchMenu from '@/components/MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';
import { defaultStyles } from '@/components/MapComponent/OpenLayersComponent/helpers/styleUtils';

export const municipalStyles = {
  ...defaultStyles,
  fillOpacity: 0,
  lineColor: '#008099',
  dashline: 5,
  width: 10,
};

const colorCodes: colorCodesType = {
  '#A9D2F3': { min: 10, max: 50 },
  '#7CB2E8': { min: 50, max: 100 },
  '#4A90D9': { min: 100, max: 130 },
  '#0062AC': { min: 130, max: 160 },
};

function colorRange(data, noOfRange) {
  if (data?.length === 0) return [];
  const actualCodes = [{ min: 0, max: 0, color: '#FF4538' }];
  const maxVal = Math.max(...data?.map((d) => d.count));
  const maxValue = maxVal <= noOfRange ? 10 : maxVal;
  const minValue = 1;
  const colorCodesKeys = Object.keys(colorCodes);
  const interval = (maxValue - minValue) / noOfRange;
  let currentValue = minValue;
  colorCodesKeys.forEach((key, index) => {
    const nextValue = currentValue + interval;
    actualCodes.push({
      min: Math.round(currentValue),
      max: Math.round(nextValue),
      color: colorCodesKeys[index],
    });
    currentValue = nextValue;
  });
  return actualCodes;
}

const getChoroplethColor = (value, colorCodesOutput) => {
  let toReturn = '#FF4538';
  colorCodesOutput?.map((obj) => {
    if (obj.min <= value && obj.max >= value) {
      toReturn = obj.color;
      return toReturn;
    }
    return toReturn;
  });
  return toReturn;
};

const TaskSubmissionsMap = () => {
  const dispatch = useAppDispatch();

  const [taskBoundaries, setTaskBoundaries] = useState<taskBoundariesType | null>(null);
  const [dataExtractUrl, setDataExtractUrl] = useState<string | null>(null);
  const [taskAreaExtent, setTaskAreaExtent] = useState(null);

  const projectInfo: projectInfoType = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const projectTaskBoundries: projectTaskBoundriesType[] = CoreModules.useAppSelector(
    (state) => state.project.projectTaskBoundries,
  );
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const taskWiseSubmissionCount: taskWiseSubmissionCount[] = taskInfo?.map((task) => ({
    code: task.task_id,
    count: task.submission_count,
  }));
  const selectedTask: number = CoreModules.useAppSelector((state) => state.task.selectedTask);

  const legendColorArray: legendColorArrayType[] = colorRange(taskWiseSubmissionCount, '4');

  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });

  useEffect(() => {
    if (
      !projectTaskBoundries ||
      projectTaskBoundries?.length < 1 ||
      projectTaskBoundries?.[0]?.taskBoundries?.length < 1
    ) {
      return;
    }
    const taskGeojsonFeatureCollection = {
      type: 'FeatureCollection',
      features: [
        ...projectTaskBoundries?.[0]?.taskBoundries?.map((task) => ({
          type: 'Feature',
          geometry: { ...task.outline, id: task?.outline?.properties?.fid },
          properties: {
            fid: task?.index,
            uid: task?.id,
          },
        })),
      ],
    };
    setTaskBoundaries(taskGeojsonFeatureCollection);
  }, [projectTaskBoundries]);

  useEffect(() => {
    if (!taskBoundaries) return;
    if (!selectedTask) return;
    const filteredSelectedTaskGeojson = {
      type: 'FeatureCollection',
      features: taskBoundaries?.features?.filter((task) => task?.properties?.fid === selectedTask),
    };
    const vectorSource = new VectorSource({
      features: new GeoJSON().readFeatures(filteredSelectedTaskGeojson, {
        featureProjection: get('EPSG:3857'),
      }),
    });
    const extent = vectorSource.getExtent();

    setTaskAreaExtent(vectorSource.getFeatures()[0]?.getGeometry());
    setDataExtractUrl(projectInfo.data_extract_url);

    map.getView().fit(extent, {
      animate: true,
      size: map?.getSize(),
      padding: [50, 50, 50, 50],
      constrainResolution: true,
      duration: 2000,
    });
    dispatch(CoreModules.TaskActions.SetSelectedTask(null));
  }, [selectedTask]);

  const taskOnSelect = (properties, feature) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(properties?.fid));
  };

  const setChoropleth = useCallback(
    (style, feature, resolution) => {
      const stylex = { ...style };
      stylex.fillOpacity = 80;
      const getTask = taskWiseSubmissionCount?.find((d) => d.code == feature.getProperties().fid);
      const getTaskSubmissionCount = getTask?.count;
      stylex.labelMaxResolution = 1000;
      stylex.showLabel = true;
      const choroplethColor = getChoroplethColor(getTaskSubmissionCount, legendColorArray);
      stylex.fillColor = choroplethColor;
      return getStyles({
        style: stylex,
        feature,
        resolution,
      });
    },
    [taskWiseSubmissionCount],
  );

  map?.on('loadstart', function () {
    map.getTargetElement().classList.add('spinner');
  });
  map?.on('loadend', function () {
    map.getTargetElement().classList.remove('spinner');
  });

  const taskSubmissionsPopupUI = (properties: taskFeaturePropertyType) => {
    const currentTask = taskInfo?.filter((task) => +task?.task_id === properties?.fid);
    if (currentTask?.length === 0) return;
    return (
      <div className="fmtm-h-fit">
        <h2 className="fmtm-border-b-[2px] fmtm-border-primaryRed fmtm-w-fit fmtm-pr-1">
          Task ID: #{currentTask?.[0]?.index}
        </h2>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
          <p>
            Expected Count: <span className="fmtm-text-primaryRed">{currentTask?.[0]?.feature_count}</span>
          </p>
          <p>
            Submission Count: <span className="fmtm-text-primaryRed">{currentTask?.[0]?.submission_count}</span>
          </p>
        </div>
      </div>
    );
  };

  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        gap: 2,
      }}
      className="fmtm-h-full"
    >
      <MapComponent
        ref={mapRef}
        mapInstance={map}
        className="map"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <div className="fmtm-absolute fmtm-right-2 fmtm-top-3 fmtm-z-20">
          <LayerSwitchMenu map={map} />
        </div>
        <LayerSwitcherControl visible={'osm'} />
        {taskBoundaries && (
          <VectorLayer
            setStyle={(feature, resolution) =>
              setChoropleth({ ...municipalStyles, lineThickness: 3 }, feature, resolution)
            }
            geojson={taskBoundaries}
            mapOnClick={taskOnSelect}
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
        <div className="fmtm-absolute fmtm-bottom-2 fmtm-left-2 sm:fmtm-bottom-5 sm:fmtm-left-5 fmtm-z-50 fmtm-rounded-lg">
          <Accordion
            body={<TaskSubmissionsMapLegend legendColorArray={legendColorArray} />}
            header={
              <p className="fmtm-text-lg fmtm-font-normal fmtm-my-auto fmtm-mb-[0.35rem] fmtm-ml-2">
                No. of Submissions
              </p>
            }
            onToggle={() => {}}
            className="fmtm-py-0 !fmtm-pb-0 fmtm-rounded-lg hover:fmtm-bg-gray-50"
            collapsed={true}
          />
        </div>
        {taskInfo?.length > 0 && <AsyncPopup map={map} popupUI={taskSubmissionsPopupUI} primaryKey="fid" />}
        {dataExtractUrl && isValidUrl(dataExtractUrl) && (
          <VectorLayer
            fgbUrl={dataExtractUrl}
            // For POLYLINE, show all geoms, else filter by clicked task area (not working)
            // fgbExtentFilter={projectInfo.primary_geom_type === 'POLYLINE' ? null : taskAreaExtent}
            fgbExtentFilter={taskAreaExtent}
            zIndex={15}
          />
        )}
      </MapComponent>
    </CoreModules.Box>
  );
};

export default TaskSubmissionsMap;
