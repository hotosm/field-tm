import React, { useEffect, useRef, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import WindowDimension from '../hooks/WindowDimension';
import MapDescriptionComponents from '../components/MapDescriptionComponents';
import ActivitiesPanel from '../components/ActivitiesPanel';
import OpenLayersMap from '../components/OpenLayersMap';
import environment from '../environment';
import { DownloadDataExtract, DownloadProjectForm, ProjectById } from '../api/Project';
import { ProjectActions } from '../store/slices/ProjectSlice';
import CustomizedSnackbar from '../utilities/CustomizedSnackbar';
import { defaults } from 'ol/control/defaults';
import OnScroll from '../hooks/OnScroll';
import { Tile as TileLayer } from 'ol/layer.js';
import { OSM } from 'ol/source.js';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import TasksLayer from '../components/TasksLayer';
import Map from 'ol/Map';
import View from 'ol/View';
import { HomeActions } from '../store/slices/HomeSlice';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import GeoJSON from 'ol/format/GeoJSON';

import Overlay from 'ol/Overlay';
import GenerateMbTiles from '../components/GenerateMbTiles';
import { ProjectBuildingGeojsonService } from '../api/SubmissionService';
import { get } from 'ol/proj';
import { buildingStyle, basicGeojsonTemplate } from '../utilities/mapUtils';

const Home = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();

  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const state = CoreModules.useAppSelector((state) => state.project);

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
  const downloadProjectFormLoading = CoreModules.useAppSelector((state) => state.project.downloadProjectFormLoading);
  const downloadDataExtractLoading = CoreModules.useAppSelector((state) => state.project.downloadDataExtractLoading);
  const projectBuildingGeojson = CoreModules.useAppSelector((state) => state.project.projectBuildingGeojson);

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

      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedId),
        ),
        state.projectTaskBoundries,
      );
      // dispatch(ProjectBuildingGeojsonService(`${environment.baseApiUrl}/projects/${environment.decode(encodedId)}/features`))
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(
        ProjectById(
          `${environment.baseApiUrl}/projects/${environment.decode(encodedId)}`,
          state.projectTaskBoundries,
          environment.decode(encodedId),
        ),
        state.projectTaskBoundries,
      );
    }
    if (Object.keys(state.projectInfo).length == 0) {
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

  useEffect(() => {
    const container = document.getElementById('popup');
    const closer = document.getElementById('popup-closer');

    const overlay = new Overlay({
      element: container,
      autoPan: {
        animation: {
          duration: 250,
        },
      },
    });
    /**
     * Function to setPosition of Popup to Undefined so that the popup closes
     */
    function handleClickOutside(event) {
      if (container && !container.contains(event.target)) {
        overlay.setPosition(undefined);
        closer.blur();
      }
    }
    // Bind the event listener for outside click and trigger handleClickOutside
    // document.addEventListener("mousedown", handleClickOutside);

    closer.style.textDecoration = 'none';
    closer.style.color = defaultTheme.palette.info['main'];
    closer.onclick = function () {
      overlay.setPosition(undefined);
      closer.blur();
      return false;
    };

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
      overlays: [overlay],
      view: view,
    });
    initialMap.on('click', function (event) {
      initialMap.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
        const status = feature.getId()?.toString()?.replace('_', ',')?.split(',')?.[1];
        if (environment.tasksStatus.findIndex((data) => data.label == status) != -1) {
          setTaskId(feature?.getId()?.split('_')?.[0]);
          const coordinate = event.coordinate;
          overlay.setPosition(coordinate);
          setFeaturesLayer(feature);
          dispatch(
            ProjectBuildingGeojsonService(
              `${environment.baseApiUrl}/projects/${decodedId}/features?task_id=${feature?.getId()?.split('_')?.[0]}`,
            ),
          );
        }
      });
    });

    initialMap.on('loadstart', function () {
      initialMap.getTargetElement().classList.add('spinner');
    });

    setMap(initialMap);
    setView(view);
    setFeaturesLayer(initalFeaturesLayer);

    return () => {
      /**
       * Removed handleClickOutside Eventlistener on unmount
       */
      document.removeEventListener('mousedown', handleClickOutside);
      mapElement.current = null;
      setFeaturesLayer();
      setView();
      setMap();
    };
  }, [params.id]);

  useEffect(() => {
    if (map != undefined) {
      const topX = map.getTargetElement().getBoundingClientRect().y;
      setTop(topX);
    }
  }, [map, y]);

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

  const handleDownload = (downloadType) => {
    if (downloadType === 'form') {
      dispatch(DownloadProjectForm(`${environment.baseApiUrl}/projects/download_form/${decodedId}/`, downloadType));
    } else if (downloadType === 'geojson') {
      dispatch(DownloadProjectForm(`${environment.baseApiUrl}/projects/${decodedId}/download_tasks`, downloadType));
    }
  };
  const onDataExtractDownload = () => {
    dispatch(DownloadDataExtract(`${environment.baseApiUrl}/projects/features/download/?project_id=${decodedId}`));
  };

  return (
    <CoreModules.Stack spacing={2}>
      {/* Customized Modal For Generate Tiles */}
      <GenerateMbTiles
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

      {/* Top project details heading medium dimension*/}
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

      {/* Center description and map */}
      <CoreModules.Stack direction={'column'} spacing={1}>
        <MapDescriptionComponents defaultTheme={defaultTheme} state={state} type={type} />
        <CoreModules.Stack direction={'row'} spacing={1}>
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'flex-start',
              marginLeft: '1rem',
              gap: 6,
            }}
          >
            <CoreModules.LoadingButton
              onClick={() => handleDownload('form')}
              sx={{ width: 'unset' }}
              loading={downloadProjectFormLoading.type === 'form' && downloadProjectFormLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              Form
            </CoreModules.LoadingButton>
            <CoreModules.LoadingButton
              onClick={() => handleDownload('geojson')}
              sx={{ width: 'unset' }}
              loading={downloadProjectFormLoading.type === 'geojson' && downloadProjectFormLoading.loading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              Tasks
            </CoreModules.LoadingButton>
            <CoreModules.LoadingButton
              onClick={() => onDataExtractDownload()}
              sx={{ width: 'unset' }}
              loading={downloadDataExtractLoading}
              loadingPosition="end"
              endIcon={<AssetModules.FileDownloadIcon />}
              variant="contained"
              color="error"
            >
              Data Extract
            </CoreModules.LoadingButton>
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'flex-end',
              width: '100%',
            }}
          >
            <CoreModules.Link
              to={`/projectInfo/${encodedId}`}
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'flex-end',
                textDecoration: 'none',
                marginRight: '15px',
              }}
            >
              <CoreModules.Button variant="contained" color="error">
                ProjectInfo
              </CoreModules.Button>
            </CoreModules.Link>
            <CoreModules.Button
              onClick={() => setToggleGenerateModal(true)}
              variant="contained"
              color="error"
              sx={{ width: '200px', mr: '15px' }}
              endIcon={<AssetModules.BoltIcon />}
            >
              Generate MbTiles
            </CoreModules.Button>
            <CoreModules.Link
              to={`/edit-project/project-details/${encodedId}`}
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'flex-end',
                textDecoration: 'none',
                marginRight: '15px',
              }}
            >
              <CoreModules.Button variant="outlined" color="error">
                Edit Project
              </CoreModules.Button>
            </CoreModules.Link>
          </div>
        </CoreModules.Stack>
        {/* <ProjectMap /> */}
        {params?.id && (
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
        )}
      </CoreModules.Stack>

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
    </CoreModules.Stack>
  );
};

export default Home;
