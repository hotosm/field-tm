import React, { useCallback, useState, useEffect } from 'react';

import CoreModules from '../../shared/CoreModules';
import { MapContainer as MapComponent } from '../MapComponent/OpenLayersComponent';
import { useOLMap } from '../MapComponent/OpenLayersComponent';
import LayerSwitcherControl from '../MapComponent/OpenLayersComponent/LayerSwitcher';
import { VectorLayer } from '../MapComponent/OpenLayersComponent/Layers';
import { Vector as VectorSource } from 'ol/source';
import GeoJSON from 'ol/format/GeoJSON';
import { get } from 'ol/proj';
import { ProjectBuildingGeojsonService } from '../../api/SubmissionService';
import environment from '../../environment';
import { getStyles } from '../MapComponent/OpenLayersComponent/helpers/styleUtils';
import { ProjectActions } from '../../store/slices/ProjectSlice';
import { basicGeojsonTemplate } from '../../utilities/mapUtils';
import ProjectInfoMapLegend from './ProjectInfoMapLegend';
import Accordion from '../common/Accordion';

export const defaultStyles = {
  lineColor: '#000000',
  lineOpacity: 70,
  fillColor: '#1a2fa2',
  fillOpacity: 50,
  lineThickness: 1,
  circleRadius: 5,
  dashline: 0,
  showLabel: false,
  customLabelText: null,
  labelField: '',
  labelFont: 'Calibri',
  labelFontSize: 14,
  labelColor: '#000000',
  labelOpacity: 100,
  labelOutlineWidth: 3,
  labelOutlineColor: '#ffffff',
  labelOffsetX: 0,
  labelOffsetY: 0,
  labelText: 'normal',
  labelMaxResolution: 400,
  labelAlign: 'center',
  labelBaseline: 'middle',
  labelRotationDegree: 0,
  labelFontWeight: 'normal',
  labelPlacement: 'point',
  labelMaxAngleDegree: 45.0,
  labelOverflow: false,
  labelLineHeight: 1,
  visibleOnMap: true,
  icon: {},
  showSublayer: false,
  sublayerColumnName: '',
  sublayer: {},
};

export const municipalStyles = {
  ...defaultStyles,
  fillOpacity: 0,
  lineColor: '#008099',
  dashline: 5,
  width: 10,
};

const colorCodes = {
  // '#9edefa': { min: 0, max: 5 },
  '#A9D2F3': { min: 10, max: 50 },
  '#7CB2E8': { min: 50, max: 100 },
  '#4A90D9': { min: 100, max: 130 },
  '#0062AC': { min: 130, max: 160 },
};
function colorRange(data, noOfRange) {
  if (data?.length === 0) return [];
  const actualCodes = [{ min: 0, max: 0, color: '#605f5e' }];
  const maxVal = Math.max(...data?.map((d) => d.count));
  const maxValue = maxVal <= noOfRange ? 10 : maxVal;
  // const minValue = Math.min(...data?.map((d) => d.count)) 0;
  const minValue = 1;
  // const firstValue = minValue;
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

const ProjectInfomap = () => {
  const dispatch = CoreModules.useAppDispatch();
  const [taskBoundaries, setTaskBoundaries] = useState(null);
  const [buildingGeojson, setBuildingGeojson] = useState(null);
  const projectTaskBoundries = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);

  const taskInfo = CoreModules.useAppSelector((state) => state.task.taskInfo);
  const federalWiseProjectCount = taskInfo?.map((task) => ({
    code: task.task_id,
    count: task.submission_count,
  }));

  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);
  const selectedTask = CoreModules.useAppSelector((state) => state.task.selectedTask);
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const params = CoreModules.useParams();
  const encodedId = params.projectId;
  const decodedId = environment.decode(encodedId);
  const legendColorArray = colorRange(federalWiseProjectCount, '4');
  const { mapRef, map } = useOLMap({
    center: [0, 0],
    zoom: 4,
    maxZoom: 25,
  });

  useEffect(() => {
    return () => {
      dispatch(ProjectActions.SetProjectBuildingGeojson(null));
    };
  }, []);

  useEffect(() => {
    if (
      !projectTaskBoundries ||
      projectTaskBoundries?.length < 1 ||
      projectTaskBoundries?.[0]?.taskBoundries?.length < 1
    ) {
      return;
    }
    const taskGeojsonFeatureCollection = {
      ...basicGeojsonTemplate,
      features: [
        ...projectTaskBoundries?.[0]?.taskBoundries?.map((task) => ({
          ...task.outline_geojson,
          id: task.outline_geojson.properties.uid,
        })),
      ],
    };
    setTaskBoundaries(taskGeojsonFeatureCollection);
    // const taskBuildingGeojsonFeatureCollection = {
    //   ...basicGeojsonTemplate,
    //   features: [
    //     ...projectBuildingGeojson?.map((feature) => ({
    //       ...feature.geometry,
    //       id: feature.id,
    //     })),
    //   ],
    // };
    // setBuildingGeojson(taskBuildingGeojsonFeatureCollection);
  }, [projectTaskBoundries]);
  useEffect(() => {
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
    setBuildingGeojson(taskBuildingGeojsonFeatureCollection);
  }, [projectBuildingGeojson]);

  useEffect(() => {
    if (!taskBoundaries) return;
    const filteredSelectedTaskGeojson = {
      ...basicGeojsonTemplate,
      features: taskBoundaries?.features?.filter((task) => task.properties.uid === selectedTask),
    };
    const vectorSource = new VectorSource({
      features: new GeoJSON().readFeatures(filteredSelectedTaskGeojson, {
        featureProjection: get('EPSG:3857'),
      }),
    });
    var extent = vectorSource.getExtent();
    map.getView().fit(extent, {
      // easing: elastic,
      animate: true,
      size: map?.getSize(),
      // maxZoom: 15,
      padding: [50, 50, 50, 50],
      // duration: 900,
      constrainResolution: true,
      duration: 2000,
    });

    dispatch(
      ProjectBuildingGeojsonService(
        `${import.meta.env.VITE_API_URL}/projects/${decodedId}/features?task_id=${selectedTask}`,
      ),
    );
  }, [selectedTask]);

  const taskOnSelect = (properties, feature) => {
    dispatch(CoreModules.TaskActions.SetSelectedTask(properties.uid));
  };

  const setChoropleth = useCallback(
    (style, feature, resolution) => {
      const stylex = { ...style };
      stylex.fillOpacity = 80;
      const getFederal = federalWiseProjectCount?.find((d) => d.code === feature.getProperties().uid);
      const getFederalCount = getFederal?.count;
      stylex.labelMaxResolution = 1000;
      stylex.showLabel = true;
      // stylex.labelField = 'district_code';
      // stylex.customLabelText = getFederalName;
      const choroplethColor = getChoroplethColor(getFederalCount, legendColorArray);
      stylex.fillColor = choroplethColor;
      return getStyles({
        style: stylex,
        feature,
        resolution,
      });
    },
    [federalWiseProjectCount],
  );

  map?.on('loadstart', function () {
    map.getTargetElement().classList.add('spinner');
  });
  map?.on('loadend', function () {
    map.getTargetElement().classList.remove('spinner');
  });
  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        gap: 2,
      }}
      className="fmtm-h-[35vh] md:fmtm-h-[70vh]"
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
        <LayerSwitcherControl />
        {taskBoundaries && (
          <VectorLayer
            hoverEffect
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
            body={<ProjectInfoMapLegend defaultTheme={defaultTheme} />}
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
        {buildingGeojson && <VectorLayer key={buildingGeojson} geojson={buildingGeojson} zIndex={15} />}
      </MapComponent>
    </CoreModules.Box>
  );
};

export default ProjectInfomap;
